import requests
import random
import time
import os
import sys
import base64
from nacl import encoding, public

# --- 配置区 ---
# 从环境变量读取（由 GitHub Actions 传入）
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')
G_TOKEN = os.getenv('G_TOKEN')  # 用于写回 Secret 的 GitHub PAT
SECRET_NAME = os.getenv('SECRET_NAME') # 当前操作的 Secret 名称 (REFRESH_TOKEN_1 或 2)
REPO_NAME = os.getenv('GITHUB_REPOSITORY') # 格式: 用户名/仓库名

def renew_token():
    print(f"正在为 {SECRET_NAME} 刷新 Token...")
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    res = requests.post(url, data=data).json()
    if 'access_token' in res:
        return res['access_token'], res['refresh_token']
    else:
        print(f"刷新失败: {res.get('error_description')}")
        sys.exit(1)

def update_github_secret(new_token):
    """极致自动化：利用 PyNaCl 加密并更新 GitHub Secret"""
    print(f"正在将新的 Token 存回 GitHub Secret: {SECRET_NAME}...")
    headers = {
        'Authorization': f'token {G_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # 1. 获取仓库公钥
    get_key_url = f"https://api.github.com/repos/{REPO_NAME}/actions/secrets/public-key"
    key_data = requests.get(get_key_url, headers=headers).json()
    public_key = key_data['key']
    key_id = key_data['key_id']

    # 2. 加密 Secret
    public_key_obj = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key_obj)
    encrypted_value = base64.b64encode(sealed_box.encrypt(new_token.encode("utf-8"))).decode("utf-8")

    # 3. 更新 Secret
    put_url = f"https://api.github.com/repos/{REPO_NAME}/actions/secrets/{SECRET_NAME}"
    put_data = {"encrypted_value": encrypted_value, "key_id": key_id}
    resp = requests.put(put_url, headers=headers, json=put_data)
    if resp.status_code in [201, 204]:
        print("Secret 更新成功！")
    else:
        print(f"Secret 更新失败: {resp.text}")

def call_graph_apis(token):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # --- 模拟动作定义 ---
    def action_mail():
        # 创建草稿并删除
        mail_body = {"subject": "Dev Check", "body": {"content": "System OK"}, "toRecipients": []}
        r = requests.post("https://graph.microsoft.com/v1.0/me/messages", headers=headers, json=mail_body)
        if r.status_code == 201:
            mid = r.json()['id']
            requests.delete(f"https://graph.microsoft.com/v1.0/me/messages/{mid}", headers=headers)
            print("API: Mail Draft Cycle OK")

    def action_drive():
        # 上传小文件并删除
        r = requests.put("https://graph.microsoft.com/v1.0/me/drive/root:/dev_test.txt:/content", headers=headers, data="test")
        if r.status_code in [200, 201]:
            fid = r.json()['id']
            requests.delete(f"https://graph.microsoft.com/v1.0/me/drive/items/{fid}", headers=headers)
            print("API: OneDrive I/O OK")

    def action_calendar():
        # 创建日程并删除
        ev = {
            "subject": "Dev Sync",
            "start": {"dateTime": "2026-07-03T10:00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2026-07-03T11:00:00", "timeZone": "UTC"}
        }
        r = requests.post("https://graph.microsoft.com/v1.0/me/events", headers=headers, json=ev)
        if r.status_code == 201:
            eid = r.json()['id']
            requests.delete(f"https://graph.microsoft.com/v1.0/me/events/{eid}", headers=headers)
            print("API: Calendar Sync OK")

    def action_read_only():
        # 读取个人资料、联系人、笔记
        endpoints = [
            "https://graph.microsoft.com/v1.0/me",
            "https://graph.microsoft.com/v1.0/me/contacts",
            "https://graph.microsoft.com/v1.0/me/onenote/notebooks",
            "https://graph.microsoft.com/v1.0/me/presence"
        ]
        for ep in endpoints:
            requests.get(ep, headers=headers)
        print("API: Batch Read Operations OK")

    # 随机执行
    actions = [action_mail, action_drive, action_calendar, action_read_only]
    random.shuffle(actions)
    for a in actions:
        try:
            a()
            time.sleep(random.randint(1, 3))
        except: pass

# --- 执行主逻辑 ---
if __name__ == "__main__":
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        print("错误：缺少必要的环境变量。")
        sys.exit(1)
        
    new_access, new_refresh = renew_token()
    call_graph_apis(new_access)
    
    # 只有在提供了 G_TOKEN 的情况下才尝试自动更新 Secret
    if G_TOKEN:
        update_github_secret(new_refresh)
    else:
        print("未提供 G_TOKEN，跳过 Secret 自动回写。")
