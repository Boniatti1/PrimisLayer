import requests
import sys
from datetime import datetime
from dotenv import load_dotenv
from os import getenv

load_dotenv()

TOKEN = getenv("TOKEN")
CHAT_ID = getenv("CHAT_ID")

ip = sys.argv[1]
action = sys.argv[2]
level = sys.argv[3] if len(sys.argv) >= 4 else "Média"
message = sys.argv[4] if len(sys.argv) == 5 else None

msg = f"""
**ALERTA DE SEGURANÇA**
• *IP*: `{ip}`
• *Ação*: `{action}`
• *Nível de Segurança*: `{level}`
• *Data*: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
"""

if message:
    msg += f"""• *Mensagem*: `{message}`"""


url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": msg,
    "parse_mode": "Markdown"
}
response = requests.post(url, json=payload)

print(f"Telegram Alert: {response.status_code}, Response: {response.text}", file=sys.stderr)