import requests
import hashlib
import re
import time
import json

# ================= 配置区域 =================
# 服务器地址 (请修改为您部署的服务器IP或域名)
SERVER_URL = "http://70.39.203.31:3000"

# 访问密码 (如果在服务器上配置了 ACCESS_PASSWORD，请在此填写)
ACCESS_PASSWORD = ""

# 邮箱账户 ID 范围配置
# 设置起始 ID 和 结束 ID (包含结束 ID)
START_ID = 1
END_ID = 100

# 自动生成 ID 列表 (例如: 1 到 5 -> [1, 2, 3, 4, 5])
ACCOUNT_IDS = list(range(START_ID, END_ID + 1))

# 邮箱文件夹 (通常验证码在收件箱 INBOX，如果找不到试一下 Junk)
MAILBOX = "INBOX"
# ===========================================

def get_auth_header():
    """生成认证头"""
    if not ACCESS_PASSWORD:
        return {}
    
    # 计算 SHA256
    token = hashlib.sha256(ACCESS_PASSWORD.encode('utf-8')).hexdigest()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def get_account_map():
    """获取所有账号的 Email -> ID 映射 (分页全量获取，含重试)"""
    result = {}
    page = 1
    page_size = 20  # 服务器默认每页20条

    while True:
        url = f"{SERVER_URL}/api/accounts"
        params = {"page": page, "pageSize": page_size}
        success = False
        for attempt in range(3):  # 每页最多重试3次
            try:
                response = requests.get(url, headers=get_auth_header(), params=params, timeout=20)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == 200:
                        acc_list = data.get("data", {}).get("list", [])
                        total = data.get("data", {}).get("total", 0)
                        if not acc_list:
                            return result  # 没有更多了
                        for acc in acc_list:
                            result[acc['email'].lower()] = acc['id']
                        if len(result) >= total or len(acc_list) < page_size:
                            return result  # 全部获取完毕
                        page += 1
                        success = True
                        break
            except Exception as e:
                print(f"第{page}页第{attempt+1}次尝试失败: {e}")
                time.sleep(1)
        if not success:
            print(f"第{page}页重试3次均失败，已获取 {len(result)} 个账号。")
            break

    return result



def fetch_latest_code(account_identifier):
    """
    获取指定账号最新邮件中的验证码
    :param account_identifier: 可以是 整数ID 或 邮箱地址字符串
    """
    # 如果传入的是邮箱 (字符串)，先尝试解析为 ID
    account_id = account_identifier
    if isinstance(account_identifier, str) and "@" in account_identifier:
        print(f"正在查找邮箱 {account_identifier} 对应的服务器 ID...")
        account_map = get_account_map()
        # 查找时也统一转小写
        account_id = account_map.get(account_identifier.lower())
        if not account_id:
            print(f"错误: 在服务器上找不到邮箱 {account_identifier}。请确保已在服务器导入该账号。")
            # 尝试打印一些可用的账号供调试
            print(f"服务器上前5个可用账号: {list(account_map.keys())[:5]}")
            return None
        print(f"邮箱 {account_identifier} 对应 ID 为: {account_id}")

    url = f"{SERVER_URL}/api/mails/fetch-new"
    payload = {
        "account_id": account_id,
        "mailbox": MAILBOX
    }
    
    try:
        print(f"正在尝试从 {SERVER_URL} 获取账号 {account_id} 的最新邮件...")
        response = requests.post(url, json=payload, headers=get_auth_header(), timeout=30)
        
        if response.status_code != 200:
            print(f"请求失败: {response.status_code} - {response.text}")
            return None
            
        data = response.json()
        
        # 检查业务状态码
        if data.get("code") != 200:
            print(f"API 错误: {data.get('message')}")
            return None
        
        mail = data.get("data")
        if not mail:
            print(f"账号 {account_id} 没有获取到新邮件")
            return None
            
        # 打印邮件主题，确认是正确的邮件
        print(f"账号 {account_id} 获取到邮件: {mail.get('subject')}")
        
        # 获取邮件内容
        content = mail.get("text_content") or mail.get("html_content") or ""
        
        # 使用正则提取 6 位数字验证码
        verification_code = None
        
        # 常见的验证码模式
        patterns = [
            r'\b(\d{6})\b',  # 独立的6位数字
            r'code is:?\s*(\d{6})', # "code is 123456"
            r'verification code:?\s*(\d{6})' # "verification code: 123456"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                verification_code = match.group(1)
                break
        
        if verification_code:
            print(f"账号 {account_id} 成功提取验证码: {verification_code}")
            return verification_code
        else:
            print(f"账号 {account_id} 未能在邮件中找到符合格式的验证码")
            return None
            
    except Exception as e:
        print(f"账号 {account_id} 发生异常: {e}")
        return None

if __name__ == "__main__":
    print(f"即将检查的账号 ID 范围: {START_ID} - {END_ID} (共 {len(ACCOUNT_IDS)} 个)")
    
    for acc_id in ACCOUNT_IDS:
        print(f"\n--- 正在检查账号 ID: {acc_id} ---")
        code = fetch_latest_code(acc_id)
        if code:
            print(f"✅ 账号 {acc_id} 最终结果: {code}")
        else:
            print(f"❌ 账号 {acc_id} 获取失败")
