import requests
import sys
from datetime import datetime
from dotenv import load_dotenv
from os import getenv

load_dotenv()

TOKEN = getenv("TOKEN")
CHAT_ID = getenv("CHAT_ID")

LEVEL = {
    "nginx-4xx": "Média",
}

ip = sys.argv[1]
action = sys.argv[2]

msg = f"""
**ALERTA DE SEGURANÇA**
• *IP*: `{ip}`
• *Ação*: `{action}`
• *Data*: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
"""

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": msg,
    "parse_mode": "Markdown"
}
response = requests.post(url, json=payload)

print(f"Telegram Alert: {response.status_code}, Response: {response.text}", file=sys.stderr)