import requests
import os
import random
import sys

# 从 GitHub Secrets 获取环境变量
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
refresh_tokens_raw = os.getenv('REFRESH_TOKENS')

def run_renew():
    if not client_id or not client_secret or not refresh_tokens_raw:
        print("❌ 错误: 请确保 Secrets 中的 CLIENT_ID, CLIENT_SECRET 和 REFRESH_TOKENS 已设置")
        sys.exit(1)

    tokens = [t.strip() for t in refresh_tokens_raw.split(',') if t.strip()]
    
    # API 列表：涵盖邮件、文件、日历、笔记、站点、用户状态等
    endpoints = [
        "https://graph.microsoft.com/v1.0/me/messages",
        "https://graph.microsoft.com/v1.0/me/mailFolders",
        "https://graph.microsoft.com/v1.0/me/calendar/events",
        "https://graph.microsoft.com/v1.0/me/contacts",
        "https://graph.microsoft.com/v1.0/me/drive/root",
        "https://graph.microsoft.com/v1.0/me/drive/root/children",
        "https://graph.microsoft.com/v1.0/me/drive/recent",
        "https://graph.microsoft.com/v1.0/me/onenote/notebooks",
        "https://graph.microsoft.com/v1.0/me/onenote/sections",
        "https://graph.microsoft.com/v1.0/me/presence",
        "https://graph.microsoft.com/v1.0/sites/root",
        "https://graph.microsoft.com/v1.0/me/profile",
        "https://graph.microsoft.com/v1.0/me",
        "https://graph.microsoft.com/v1.0/me/itemAnalytics",
        "https://graph.microsoft.com/v1.0/me/settings/regionalAndLanguageSettings"
    ]

    for i, token in enumerate(tokens):
        print(f"\n======== 正在处理账号 {i+1} ========")
        
        # 步骤 1: 刷新 Token 获取 Access Token
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': token
        }
        
        try:
            res = requests.post(token_url, data=token_data).json()
            if 'access_token' not in res:
                print(f"❌ 账号 {i+1} 刷新失败: {res.get('error_description')}")
                continue
            
            access_token = res['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}
            
            # 步骤 2: 随机调用 API 模拟活跃
            # 每次随机抽取 10 个 API，增加行为的不可预测性
            selected_apis = random.sample(endpoints, min(len(endpoints), 10))
            for api in selected_apis:
                api_name = api.split('/')[-1]
                try:
                    r = requests.get(api, headers=headers, timeout=10)
                    if r.status_code == 200:
                        print(f"✅ 成功 | API: {api_name}")
                    else:
                        print(f"⚠️ 状态 {r.status_code} | API: {api_name}")
                except Exception as e:
                    print(f"❌ 异常 | API: {api_name} | {e}")
                    
            print(f"✨ 账号 {i+1} 续期任务执行完毕")
            
        except Exception as e:
            print(f"🔥 致命错误: {e}")

if __name__ == "__main__":
    run_renew()
