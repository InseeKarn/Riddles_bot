import requests
import os
from dotenv import load_dotenv
load_dotenv()

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

def discord_message(content):
    if not DISCORD_WEBHOOK:
        print("❌ No Discord Webhook URL set.")
        return
    requests.post(DISCORD_WEBHOOK, json={"content": content})

if __name__ == "__main__":
    discord_message()