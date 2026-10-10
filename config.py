import os
from dotenv import load_dotenv

load_dotenv()

VPN_NAME = "GhostWalkVPN"

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

ROLLY_TERMINAL_ID = os.getenv("ROLLY_TERMINAL_ID")
ROLLY_API_KEY = os.getenv("ROLLY_API_KEY")
ROLLY_SECRET = os.getenv("ROLLY_SECRET")
ROLLY_API_URL = os.getenv("ROLLY_API_URL", "https://api.rollypay.io")
ROLLY_CALLBACK = os.getenv("ROLLY_CALLBACK", "http://YOUR_IP:8080/webhook/rollypay")

WG_INTERFACE = "wg0"
WG_SERVER_PUBLIC_KEY = os.getenv("WG_SERVER_PUBLIC_KEY")
WG_SERVER_ENDPOINT = os.getenv("WG_SERVER_ENDPOINT")
WG_DNS = os.getenv("WG_DNS", "1.1.1.1")
WG_CONF = "/etc/wireguard/wg0.conf"
WG_SUBNET = "10.8.0.0/24"

DB_PATH = "ghostwalk.db"

PRICES = {
    "1m": {"days": 30,  "amount": 150, "label": "1 месяц"},
    "3m": {"days": 90,  "amount": 400, "label": "3 месяца"},
    "6m": {"days": 180, "amount": 750, "label": "6 месяцев"},
}
