
import os
import requests
import time
from bs4 import BeautifulSoup

def get_outlook_verification_link(token, retries=5):
    print("正在尝试使用 Token 读取 Outlook 邮件 (API 测试)...")
    # Microsoft Graph API endpoint for messages
    url = "https://graph.microsoft.com/v1.0/me/messages?$top=5&$search='OpenAI'"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    for i in range(retries):
        try:
            print(f"[{i+1}/{retries}] 请求 API: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("value", [])
                print(f"找到 {len(messages)} 封相关邮件。")
                
                if not messages:
                    print("没有任何包含 'OpenAI' 的邮件。请稍后重試。")
                    time.sleep(3)
                    continue
                
                # 检查最新一封邮件
                latest_msg = messages[0]
                print(f"最新邮件标题: {latest_msg.get('subject')}")
                
                # 获取邮件内容
                body_content = latest_msg.get('body', {}).get('content', '')
                
                # 解析 HTML 寻找验证链接
                soup = BeautifulSoup(body_content, 'html.parser')
                links = soup.find_all('a')
                for link in links:
                    href = link.get('href')
                    if href and "verify_email" in href:
                        print(f"SUCCESS! 找到验证链接: {href}")
                        return href
                
                print("邮件中未找到验证链接。")
            elif response.status_code == 401:
                print("Token 无效或无权访问 (401 Unauthorized)。请检查 Token 是否包含 Mail.Read 权限。")
                return None
            else:
                print(f"API 请求失败: {response.text}")
        except Exception as e:
            print(f"请求出错: {e}")
        
        time.sleep(3)
    
    return None

def main():
    if not os.path.exists("accounts.txt"):
        print("未找到 accounts.txt")
        return

    tokens = []
    with open("accounts.txt", "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("----")
            if len(parts) >= 4:
                tokens.append(parts[3].strip())
    
    if not tokens:
        print("accounts.txt 中未找到 Token (需要至少4列)。")
        return

    print(f"找到 {len(tokens)} 个 Token，开始测试第一个...")
    token = tokens[0]
    get_outlook_verification_link(token)

if __name__ == "__main__":
    main()
