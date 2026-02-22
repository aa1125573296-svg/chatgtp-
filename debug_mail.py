import requests
import json

SERVER_URL = "http://70.39.203.31:3000"
TEST_EMAIL = "MrsDestiny6257@outlook.com"

def test_fetch(payload, desc):
    url = f"{SERVER_URL}/api/mails/fetch-new"
    print(f"\n--- Testing {desc} ---")
    print(f"Payload: {json.dumps(payload)}")
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

import logging

logging.basicConfig(filename='debug_result.log', level=logging.INFO, format='%(message)s', encoding='utf-8')

# Test various payloads
test_cases = [
    ({"account_id": 1, "mailbox": "INBOX"}, "Integer ID"),
    ({"account_id": TEST_EMAIL, "mailbox": "INBOX"}, "Email as Account ID"),
    ({"email": TEST_EMAIL, "mailbox": "INBOX"}, "Email Key"),
    ({"username": TEST_EMAIL, "mailbox": "INBOX"}, "Username Key"),
    ({"user": TEST_EMAIL, "mailbox": "INBOX"}, "User Key"),
]

url = f"{SERVER_URL}/api/mails/fetch-new"
for payload, desc in test_cases:
    msg = f"\n--- Testing {desc} ---"
    print(msg)
    logging.info(msg)
    try:
        resp = requests.post(url, json=payload, timeout=5)
        msg_payload = f"Payload: {json.dumps(payload)}"
        print(msg_payload)
        logging.info(msg_payload)
        
        msg_status = f"Status: {resp.status_code}"
        print(msg_status)
        logging.info(msg_status)
        
        try:
            json_resp = json.dumps(resp.json(), indent=2, ensure_ascii=False)
            print(json_resp)
            logging.info(json_resp)
        except:
            print(f"Raw Response: {resp.text}")
            logging.info(f"Raw Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")
        logging.info(f"Error: {e}")

# Test listing accounts (guess endpoint)
list_url = f"{SERVER_URL}/api/accounts"
msg_list = f"\n--- Testing List Accounts ({list_url}) ---"
print(msg_list)
logging.info(msg_list)
try:
    resp = requests.get(list_url, timeout=5)
    print(f"Status: {resp.status_code}")
    logging.info(f"Status: {resp.status_code}")
    print(resp.text[:500])
    logging.info(resp.text[:2000])
except Exception as e:
    print(f"Error: {e}")
    logging.info(f"Error: {e}")
