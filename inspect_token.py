
import json
import base64
import os
import time

def decode_jwt(token):
    try:
        # A JWT has 3 parts: header, payload, signature
        parts = token.split('.')
        if len(parts) != 3:
            print("❌ Token 格式看似不是标准的 JWT (没有3个部分)。")
            return None
        
        # Decode payload (2nd part)
        payload = parts[1]
        # Allow padding
        padded = payload + '=' * (4 - len(payload) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded)
        decoded_str = decoded_bytes.decode('utf-8')
        claims = json.loads(decoded_str)
        return claims
    except Exception as e:
        print(f"❌ 解析 Token 失败: {e}")
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
        print("accounts.txt 中未找到 Token。")
        return

    token = tokens[0]
    print(f"Token 前缀: {token[:20]}...")
    
    claims = decode_jwt(token)
    if claims:
        print("\n=== Token 信息解析 ===")
        
        # Audience
        aud = claims.get('aud', 'Unknown')
        print(f"Audience (适用对象): {aud}")
        if "graph.microsoft.com" not in aud:
            print("⚠️ 警告: 此 Token 的适用对象似乎不是 Microsoft Graph。")
        
        # Scopes
        scp = claims.get('scp', claims.get('roles', 'No scopes found'))
        print(f"Scopes (权限): {scp}")
        if "Mail.Read" not in str(scp) and "Mail.ReadWrite" not in str(scp):
             print("⚠️ 警告: 未在权限中找到 'Mail.Read'。可能无法读取邮件。")
        else:
             print("✅ 权限检查通过: 包含邮件读取权限。")

        # Expiration
        exp = claims.get('exp', 0)
        now = time.time()
        if exp < now:
             print(f"❌ 错误: Token 已过期! (过期时间: {exp})")
        else:
             print(f"✅ Token 有效期正常 (剩余 {int(exp - now)} 秒)。")
             
    else:
        print("无法解析 Token 内容。它可能不是 JWT，或者格式不正确。")

if __name__ == "__main__":
    main()
