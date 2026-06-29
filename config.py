import os
from dotenv import load_dotenv

load_dotenv("/root/KikuAportes/.env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
FRIEND_ID = int(os.getenv("FRIEND_ID", "0"))