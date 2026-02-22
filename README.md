# ChatGPT 批量注册自动化脚本

基于 Playwright + Microsoft Edge 的全自动账号注册脚本，支持本地验证码服务器和 Outlook Token 两种验证方式。

---

## 环境准备

1. **安装 Python 3.8+**
2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   playwright install msedge
   ```

---

## 账号文件格式 (`accounts.txt`)

每行一个账号，格式如下（字段间用 `----` 分隔）：

```
邮箱----密码
邮箱----密码----Outlook_Token
```

**示例：**
```
alice@outlook.com----MyPass123
bob@outlook.com----Short1----M.C3_BAY...（Outlook Token）
```

> **密码不足 12 位时会自动在末尾补充 `1`（例如 `abc123` → `abc1231111111`），补全后的密码会保存到结果文件。**

---

## 配置验证码服务器 (`fetch_code_local.py`)

```python
SERVER_URL = "http://你的服务器IP:3000"   # 本地邮件服务器地址
ACCESS_PASSWORD = ""                       # 访问密码（如有）
```

脚本启动时会自动从服务器拉取所有账号（支持分页），并与 `accounts.txt` 做匹配：
- **在服务器上的账号** → 自动从服务器获取验证码
- **有 Outlook Token 的账号** → 自动用 Token 获取验证码
- **两者都没有的账号** → 跳过

---

## 运行

```bash
python register.py
```

---

## 注册流程

1. 读取 `accounts.txt` 并加载服务器账号列表
2. 跳过 `registered_success.txt` 中已注册的账号
3. 自动补全不足 12 位的密码
4. 打开浏览器，填写邮箱 → 密码 → 提交注册
5. 自动获取验证码并填入
6. 自动填写随机**姓名**和**生日**
7. 注册成功后将账号信息追加到 `registered_success.txt`

---

## 结果文件 (`registered_success.txt`)

```
邮箱----最终密码（补全后）----Outlook_Token
```

---

## 注意事项

- 使用 Microsoft Edge 浏览器（需已安装）
- 建议配合代理使用，避免同 IP 注册过多被封锁
- `user_data/` 目录保存浏览器持久化数据，有助于绕过 Cloudflare
