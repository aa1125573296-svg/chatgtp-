import time
import pandas as pd
import pandas as pd
from playwright.sync_api import sync_playwright
try:
    from fetch_code_local import fetch_latest_code
except ImportError:
    print("⚠️ 警告: 未找到 fetch_code_local.py，本地验证码功能将不可用。")
    def fetch_latest_code(account_id): return None

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

def register_account(context, email, password, token=None, account_id=None):
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
            print("等待密码输入框...")
            # 尝试多种选择器
            page.wait_for_selector("input[name='password'], input[type='password'], input[data-testid='password-input']", state="visible", timeout=30000)
            page.fill("input[name='password'], input[type='password'], input[data-testid='password-input']", password)
            print("已输入密码")
            
            # 点击继续
            page.keyboard.press("Enter")
            time.sleep(1)
            # 再次尝试点击按钮以防万一
            if page.is_visible("button[type='submit']"):
                 page.click("button[type='submit']", timeout=2000)

        except Exception as e:
            print(f"【注意】未检测到密码框或输入失败: {e}")
            page.click("button[type='submit']") 
        except:
             print("【注意】未检测到密码框 (可能已手动输入或卡住)，继续尝试验证步骤...")
             
        
        print("=== 关键步骤: 邮箱验证码 ===")
        import ctypes
        
        # Use API Token
        # Use API Token
        code = None
        # if token:
        #     print("检测到 Token，尝试 API 获取验证码...")
        #     code = get_outlook_verification_code(token)
        
        # Fallback to local server if no token or token failed (optional)
        if not code:
            print(f"正在使用电子邮箱注册模式 (本地服务获取验证码 Account ID: {account_id})...")
            # 尝试更多次，因为邮件可能需要时间到达
            for i in range(12): 
                code = fetch_latest_code(account_id)
                if code: break
                print(f"[{i+1}/12] 等待 5 秒后重试...")
                time.sleep(5)

        if code:
            print(f"获取到验证码: {code}")
            try:
                # Fill the code
                page.wait_for_selector("input", timeout=10000)
                page.fill("input[type='text'], input[inputmode='numeric']", code)
                print(f"验证码 {code} 已填入，正在提交...")
                time.sleep(1)
                page.keyboard.press("Enter")
                # 有时候可能需要点击 verify 按钮，尝试查找并点击
                try:
                    verify_btn = page.locator("button:has-text('Verify'), button:has-text('验证')")
                    if verify_btn.is_visible():
                        verify_btn.click(timeout=2000)
                except:
                    pass
                time.sleep(3) # 等待跳转
            except:
                print(f"验证码提取成功: {code}，但找不到输入框。")
        else:
             print("无法自动获取验证码 (Token 无效或本地服务无响应)。跳过...")

        # === 新增步骤: 填写随机全名和生日 ===
        try:
            print("等待 'Full Name' 输入框 (可能需要一点时间加载)...")
            # 等待全名输入框出现
            page.wait_for_selector("input[autocomplete='name'], input[placeholder='Full name'], input[aria-label='Full name']", state="visible", timeout=15000)
            
            import random
            import string
            
            # 随机生成全名
            first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Rodriguez", "Wilson"]
            random_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            print(f"自动填写全名: {random_name}")
            page.fill("input[autocomplete='name'], input[placeholder='Full name'], input[aria-label='Full name']", random_name)
            
            # 填写生日 (调试 + 盲打模式)
            print("正在填写生日...")
            birth_year = f"{random.randint(1990, 2000)}"
            birth_month = f"{random.randint(1, 12):02d}"
            birth_day = f"{random.randint(1, 28):02d}"
            
            plain_date_iso = f"{birth_year}{birth_month}{birth_day}" # YYYYMMDD
            
            # === 关键调试：打印页面上所有输入框 ===
            print("=== 页面输入框侦测开始 ===")
            inputs = page.locator("input:visible")
            count = inputs.count()
            print(f"找到 {count} 个可见输入框:")
            for i in range(count):
                try:
                    el = inputs.nth(i)
                    print(f"Input [{i}]: html={el.evaluate('el => el.outerHTML')} | value={el.input_value()}")
                except:
                    pass
            print("=== 页面输入框侦测结束 ===")

            # 策略: 聚焦 Full Name -> Tab -> 输入纯数字
            print(f"尝试盲打生日: {plain_date_iso}")
            try:
                # 1. 确保 Full Name 有焦点
                page.click("input[autocomplete='name'], input[placeholder='Full name'], input[aria-label='Full name']")
                time.sleep(0.5)
                
                # 2. 切换到下一个 (Birthday)
                page.keyboard.press("Tab")
                time.sleep(0.5)
                
                # 3. 模拟按键 (逐个数字输入)
                # 有些控件对快速输入反应不过来
                for digit in plain_date_iso:
                    page.keyboard.type(digit)
                    time.sleep(0.1) # 慢速输入
                
                print("已完成按键模拟。")
                
            except Exception as e:
                print(f"盲打执行异常: {e}")

            print("生日填写步骤完成。")

            print(f"已尝试填写生日")
            
            # 点击继续
            print("尝试点击 Continue...")
            continue_btn = page.locator("button:has-text('Continue'), button:has-text('继续')")
            if continue_btn.count() > 0:
                continue_btn.first.click()
            else:
                 page.keyboard.press("Enter")
                 
        except Exception as e:
            print(f"自动填写个人信息时遇到问题 (可能已跳过或界面不同): {e}")

        # 保存成功账号
        try:
            with open("registered_success.txt", "a", encoding="utf-8") as f:
                # 保持原始格式或清晰格式
                f.write(f"{email}----{password}----{token}\n")
            print(f"✅ 账号 {email} 已保存到 registered_success.txt")
        except Exception as e:
            print(f"保存账号失败: {e}")

        print(f"账号 {email} 流程结束，自动进入下一个...")
        time.sleep(3) # 给一点缓冲时间
        
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
                password = parts[1].strip() if len(parts) >= 2 else "Password123!" # 默认密码
                
                # 智能识别 Token (通常以 M. 开头)
                token = None
                for part in parts:
                    p = part.strip()
                    if p.startswith("M."):
                        token = p
                        break
                
                # 如果没找到 M. 开头，且长度足够，尝试按位置回退 (旧逻辑)
                if not token and len(parts) >= 3:
                     # 假设第3位是 Token (Step 259 格式)
                     # 或者第4位 (Step 281 格式)
                     if len(parts) >= 4 and parts[3].strip().startswith("M."):
                         token = parts[3].strip()
                     elif parts[2].strip().startswith("M."):
                         token = parts[2].strip()

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

    # 获取服务器上的可用账号列表
    try:
        from fetch_code_local import get_account_map
        print("正在连接本地验证码服务器获取可用账号列表...")
        server_accounts = get_account_map()
        print(f"服务器上共有 {len(server_accounts)} 个可用账号:")
        for srv_email in list(server_accounts.keys()):
            print(f"  - {srv_email}")
    except Exception as e:
        print(f"⚠️ 无法获取服务器账号列表: {e}")
        server_accounts = {}

    with sync_playwright() as p:
        # 使用持久化上下文 + 防检测参数
        user_data_dir = "./user_data" 
        print("启动浏览器中... (使用持久化数据目录，有助于通过 Cloudflare)")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            channel="msedge",  # 指定使用 Microsoft Edge 浏览器
            headless=False,
            # slow_mo=1000, # 稍微减少延迟，避免太慢
            args=[
                "--disable-blink-features=AutomationControlled", 
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-webauthn", 
                "--disable-features=WebAuthn,WebAuthentication,WebAuthenticationProxy,ClientSideDetectionModel,CreditCardSave,PasswordManager", 
                "--disable-password-manager-reauthentication",
                "--disable-client-side-phishing-detection",
                "--no-default-browser-check",
                "--disable-component-update",
                "--ignore-certificate-errors",
                "--disable-infobars",
                "--disable-popup-blocking"
            ]
        )
        
        # 增加一个防检测脚本注入
        page = context.pages[0] if context.pages else context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 读取已成功注册的账号，避免重复注册
        already_registered = set()
        if os.path.exists("registered_success.txt"):
            with open("registered_success.txt", "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("----")
                    if parts and parts[0].strip():
                        already_registered.add(parts[0].strip().lower())
            print(f"✅ 已跳过列表加载完毕，共 {len(already_registered)} 个已注册账号。")

        for idx, account in enumerate(accounts_data, start=1):
            email = account['email']
            password = account['password']
            token = account.get('token')

            # 密码不足12位自动补全数字 '1'
            if len(password) < 12:
                original_pwd = password
                password = password.ljust(12, '1')
                print(f"🔑 {email} 密码不足12位 ({original_pwd!r})，已补全为: {password!r}")

            # 跳过已成功注册的账号
            if email.lower() in already_registered:
                print(f"⏭️ 跳过 {email}（已在 registered_success.txt 中）")
                continue

            # 检查账号是否在服务器上 (大小写不敏感)
            if server_accounts and email.lower() not in server_accounts:
                print(f"⚠️ 跳过账号 {email}: 未在验证码服务器上找到。")
                continue
            
            # 使用 try-except 包裹，防止单个失败影响后续
            try:
                # Use email as account_id for local fetcher
                status = register_account(context, email, password, token, account_id=email)
                if status == "STOP":
                    break
            except Exception as e:
                print(f"处理账号 {email} 时发生未捕获异常: {e}")

            print(f"账号 {email} 处理完毕。休息 5 秒...")
            time.sleep(5)
            
        context.close()

if __name__ == "__main__":
    main()
