import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

# Primero intenta cargar el .env situado junto al proyecto. Se mantiene la
# ruta antigua como respaldo para no romper la instalación actual del VPS.
load_dotenv(BASE_DIR / ".env")
load_dotenv("/root/KikuAportes/.env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
FRIEND_ID = int(os.getenv("FRIEND_ID", "0"))


def validate_config() -> None:
    missing = []

    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not GROUP_ID:
        missing.append("GROUP_ID")
    if not FRIEND_ID:
        missing.append("FRIEND_ID")

    if missing:
        raise RuntimeError(
            "Faltan variables obligatorias en el .env: " + ", ".join(missing)
        )
