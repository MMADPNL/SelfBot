import os
import asyncio
from telethon import TelegramClient

from handlers import register_handlers


API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "selfbot")


if not API_ID or not API_HASH:
    raise RuntimeError("❌ API_ID یا API_HASH تنظیم نشده است.")


client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH
)


register_handlers(client)


async def main():
    print("🚀 SelfBot starting...")

    await client.start()

    me = await client.get_me()

    print(
        f"✅ Logged in: "
        f"{me.first_name} "
        f"(ID: {me.id})"
    )

    print("✅ SelfBot is running...")


if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
        client.run_until_disconnected()
