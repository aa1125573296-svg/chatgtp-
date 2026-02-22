import time
import pandas as pd
from playwright.sync_api import sync_playwright

def get_outlook_verification_code(token, retries=5):
    import requests
    import re
    from bs4 import BeautifulSoup
    
    print("正在尝试使用 Token 读取 Outlook 邮件 (寻找验证码)...")
    url = "https://graph.microsoft.com/v1.0/me/messages?$top=5&$search='OpenAI'"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    for i in range(retries):
        try:
            print(f"[{i+1}/{retries}] 请求 API -> Outlook...")
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                messages = data.get("value", [])
                if not messages:
                    print(f"邮箱中暂未找到 OpenAI 相关邮件，等待 5 秒...")
                    time.sleep(5)
                    continue
                
                # Check the latest email
                latest_msg = messages[0]
                subject = latest_msg.get('subject', '')
                print(f"找到邮件: {subject}")
                
                body_content = latest_msg.get('body', {}).get('content', '')
                
                # Regex for 6-digit code
                # Pattern: Look for 6 digits that are likely the code
                match = re.search(r'\b\d{6}\b', body_content)
                if match:
                    code = match.group(0)
                    print(f"成功提取验证码: {code}")
                    return code
                else:
                    # Try title
                    match_title = re.search(r'\b\d{6}\b', subject)
                    if match_title:
                        code = match_title.group(0)
                        print(f"从标题提取验证码: {code}")
                        return code
                
                print("邮件中未找到 6 位数字验证码。")
                print("尝试打印邮件部分内容以供调试:", body_content[:200])
                
            elif response.status_code == 401:
                print("Token 无效或无权访问 Outlook (401 Unauthorized)。")
                return None
            else:
                print(f"API 请求失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"获取邮件时出错: {e}")
        
        time.sleep(5)
    
    return None

def register_account(context, email, password, token=None):
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        print(f"正在注册账号: {email}")
        page.goto("https://chatgpt.com/auth/login")
        page.wait_for_load_state("networkidle")
        
        # 1. Click Sign up
        try:
            print("正在寻找 Sign up 按钮...")
            page.get_by_test_id("signup-button").click(timeout=15000) 
        except:
            try:
                page.get_by_text("Sign up").first.click(timeout=5000)
            except:
                print("未自动点击 Sign up，请手动点击...")

        print("等待邮箱输入框...")
        
        # 2. Input Email
        try:
            page.wait_for_selector("input[name='email']", state="visible", timeout=60000)
        except:
            print("等待邮箱输入框超时，请手动导航。")

        page.fill("input[name='email']", email)
        print("已输入邮箱")
        
        # Click Continue
        clicked_continue = False
        for _ in range(3):
            try:
                if page.is_visible("button[type='submit']"):
                    page.click("button[type='submit']", timeout=3000)
                    clicked_continue = True
                    break
            except: pass
            time.sleep(1)
            
        if not clicked_continue:
             page.keyboard.press("Enter")
        
        # 3. Input Password
        try:
            page.wait_for_selector("input[name='password']", state="visible", timeout=15000)
            page.fill("input[name='password']", password)
            print("已输入密码")
            page.click("button[type='submit']") 
        except:
             print("【注意】未检测到密码框 (可能已手动输入或卡住)，继续尝试验证步骤...")
             
        
        print("=== 关键步骤: 邮箱验证码 ===")
        import ctypes
        
        # Use API Token
        if token:
            print("检测到 Token，尝试 API 获取验证码...")
            code = get_outlook_verification_code(token)
            if code:
                print(f"获取到验证码: {code}")
                try:
                    # Fill the code
                    page.wait_for_selector("input", timeout=10000)
                    page.fill("input[type='text'], input[inputmode='numeric']", code)
                    print("验证码已填入！")
                    page.keyboard.press("Enter")
                except:
                    ctypes.windll.user32.MessageBoxW(0, f"验证码是: {code}\n\n找不到输入框，请手动填入。", "验证码", 0)
            else:
                 print("API 获取验证码失败。")
                 ctypes.windll.user32.MessageBoxW(0, "无法自动获取验证码 (Token 无效或无邮件)。\n请手动处理。", "需人工辅助", 0)
        else:
             print("没有 Token，请手动验证。")
             ctypes.windll.user32.MessageBoxW(0, "没有 Token，无法自动获取验证码。\n请手动登录邮箱查看。", "需人工辅助", 0)

        # Final pause
        MB_OKCANCEL = 1
        result = ctypes.windll.user32.MessageBoxW(0, f"账号 {email} 流程暂停。\n请确认验证已通过。\n\n点击【确定】继续下一个，【取消】退出。", "人工确认", MB_OKCANCEL)
        
        if result == 2: 
            return "STOP"
        
        print("继续下一个账号...")
        
    except Exception as e:
        print(f"注册 {email} 时发生未捕获错误: {e}")
        
    except Exception as e:
        print(f"注册 {email} 时发生错误: {e}")
        # 截图保存错误现场
        page.screenshot(path=f"error_{email}.png")
    finally:
        page.close()

def main():
    import os
    accounts_data = []

    # 优先检查 accounts.txt (自定义格式: email----password----uuid----token)
    if os.path.exists("accounts.txt"):
        print("发现 accounts.txt，正在读取...")
        with open("accounts.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                parts = line.split("----")
                # 兼容不同长度，只要有前2个就行
                email = parts[0].strip() if len(parts) >= 1 else ""
                password = parts[1].strip() if len(parts) >= 2 else "Password123!" # 默认密码防止报错
                token = parts[3].strip() if len(parts) >= 4 else None # 第4位是Token
                
                if email:
                    accounts_data.append({
                        "email": email,
                        "password": password,
                        "token": token
                    })
        print(f"从 accounts.txt 加载了 {len(accounts_data)} 个账号。")

    # 如果没有找到 txt 或为空，且 csv 存在，则尝试 csv
    if not accounts_data and os.path.exists("accounts.csv"):
        print("未找到有效 accounts.txt，尝试读取 accounts.csv...")
        df = pd.read_csv("accounts.csv")
        # CSV 通常没有 token，设为 None
        accounts_data = df.to_dict('records')
        for acc in accounts_data:
            acc['token'] = None
        print(f"从 accounts.csv 加载了 {len(accounts_data)} 个账号。")

    if not accounts_data:
        print("未找到账号文件 (accounts.txt 或 accounts.csv)，或文件为空。")
        return

    with sync_playwright() as p:
        # 使用持久化上下文 + 防检测参数
        user_data_dir = "./user_data" 
        print("启动浏览器中... (使用持久化数据目录，有助于通过 Cloudflare)")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            # slow_mo=1000, # 稍微减少延迟，避免太慢
            args=[
                "--disable-blink-features=AutomationControlled", # 关键：隐藏自动化特征
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        # 增加一个防检测脚本注入
        page = context.pages[0] if context.pages else context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        for account in accounts_data:
            email = account['email']
            password = account['password']
            token = account.get('token')
            
            # 使用 try-except 包裹，防止单个失败影响后续
            try:
                status = register_account(context, email, password, token)
                if status == "STOP":
                    break
            except Exception as e:
                print(f"处理账号 {email} 时发生未捕获异常: {e}")

            print(f"账号 {email} 处理完毕。休息 5 秒...")
            time.sleep(5)
            
        context.close()

if __name__ == "__main__":
    main()
