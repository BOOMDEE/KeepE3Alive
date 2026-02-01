import requests
import random
import time

# ... (之前的 Token 刷新逻辑保持不变) ...

def call_all_power_apis(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # 1. 日历操作：创建并立即删除 (Calendars.ReadWrite)
    def test_calendar():
        event_data = {
            "subject": f"Dev Scan {random.randint(100,999)}",
            "start": {"dateTime": "2026-02-02T12:00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2026-02-02T13:00:00", "timeZone": "UTC"}
        }
        # 创建
        res = requests.post("https://graph.microsoft.com/v1.0/me/events", headers=headers, json=event_data)
        if res.status_code == 201:
            event_id = res.json().get('id')
            print(f"Calendar: Created event {event_id}")
            # 模拟开发延迟后删除
            requests.delete(f"https://graph.microsoft.com/v1.0/me/events/{event_id}", headers=headers)
            print("Calendar: Deleted event (Cleanup)")

    # 2. OneDrive 操作：上传小文件并删除 (Files.ReadWrite)
    def test_files():
        file_content = f"Active session {time.time()}".encode()
        # 上传到根目录
        url = "https://graph.microsoft.com/v1.0/me/drive/root:/dev_test.txt:/content"
        res = requests.put(url, headers=headers, data=file_content)
        if res.status_code in [200, 201]:
            print("Files: Uploaded test file")
            item_id = res.json().get('id')
            requests.delete(f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}", headers=headers)
            print("Files: Deleted test file (Cleanup)")

    # 3. 邮件操作：给自己发邮件并存入草稿箱 (Mail.ReadWrite/Send)
    def test_mail():
        mail_data = {
            "message": {
                "subject": "System Integrity Check",
                "body": {"contentType": "Text", "content": "All systems go."},
                "toRecipients": [{"emailAddress": {"address": "自己账号的邮箱"}}]
            }
        }
        # 创建草稿
        res = requests.post("https://graph.microsoft.com/v1.0/me/messages", headers=headers, json=mail_data)
        if res.status_code == 201:
            msg_id = res.json().get('id')
            print(f"Mail: Created draft {msg_id}")
            requests.delete(f"https://graph.microsoft.com/v1.0/me/messages/{msg_id}", headers=headers)
            print("Mail: Deleted draft (Cleanup)")

    # 4. 笔记操作：列出 OneNote 页面 (Notes.Read.All)
    def test_notes():
        res = requests.get("https://graph.microsoft.com/v1.0/me/onenote/pages", headers=headers)
        print(f"Notes: Queried pages, status {res.status_code}")

    # 5. 状态操作：修改自己的在线状态 (Presence.ReadWrite - 需相应权限)
    # 这个权限你清单里有 Read，这里就只读一下
    def test_presence():
        res = requests.get("https://graph.microsoft.com/v1.0/me/presence", headers=headers)
        print(f"Presence: Current status is {res.json().get('availability')}")

    # 随机组合运行，不要每次都全跑，防止被识别
    actions = [test_calendar, test_files, test_mail, test_notes, test_presence]
    for action in random.sample(actions, k=random.randint(3, 5)):
        try:
            action()
        except Exception as e:
            print(f"Action failed: {e}")
