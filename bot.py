import os
import json
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
BIRTHDAY_CHANNEL_ID = int(os.getenv("BIRTHDAY_CHANNEL_ID"))

DATA_FILE = "birthdays.json"
SENT_FILE = "sent_birthdays.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

SG_TZ = ZoneInfo("Asia/Singapore")

BIRTHDAY_MESSAGES = [
    "🎉 Happy Birthday {mention}! Hope your day is amazing! 🎂",
    "🎂 It's your special day {mention}! Enjoy every moment! 🥳",
    "🥳 Everyone say happy birthday to {mention}! 🎉",
    "🎉 Another year stronger! Happy Birthday {mention}! 🎂",
    "🎂 Cheers to you {mention}! Have a fantastic birthday! 🎉",
    "🥳 Birthday vibes for {mention}! Hope it's an awesome day! 🎂",
    "🎉 It's cake time! Happy Birthday {mention}! 🎂",
    "🎂 Sending birthday wishes to {mention}! Enjoy your day! 🎉",
    "🥳 Celebrate big today {mention}! Happy Birthday! 🎂",
    "🎉 The server celebrates you today {mention}! Happy Birthday! 🎂"
]


def load_json_file(path, default):
    try:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return default


def save_json_file(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {path}: {e}")


def now_sg():
    return datetime.now(SG_TZ)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print("🎂 Birthday bot is running in midnight mode")

    if not birthday_check.is_running():
        birthday_check.start()


@tasks.loop(seconds=45)
async def birthday_check():
    now = now_sg()

    # Only send birthday messages at 12:00 AM Singapore time
    if now.hour != 21 or now.minute != 18:
        return

    today_str = now.strftime("%Y-%m-%d")
    month = now.month
    day = now.day

    channel = bot.get_channel(BIRTHDAY_CHANNEL_ID)

    if channel is None:
        print("⚠ Bot cannot access this channel. Check the channel ID and permissions.")
        return

    birthdays = load_json_file(DATA_FILE, [])
    sent_log = load_json_file(SENT_FILE, {})

    for person in birthdays:
        if person.get("month") == month and person.get("day") == day:
            user_id = str(person.get("user_id"))
            name = person.get("name", "Birthday Star")

            # Prevent duplicate birthday messages on the same day
            if sent_log.get(user_id) == today_str:
                continue

            # Try to fetch the member from the server
            try:
                member = await channel.guild.fetch_member(int(user_id))
            except ValueError:
                print(f"⚠ Invalid user_id format for {name}: {user_id}. Skipping.")
                continue
            except discord.NotFound:
                print(f"⚠ Could not find member for user_id {user_id}. Skipping birthday for {name}.")
                continue
            except discord.Forbidden:
                print(f"⚠ Missing permission to fetch member {user_id}.")
                continue
            except Exception as e:
                print(f"⚠ Error fetching member {user_id}: {e}")
                continue

            message = random.choice(BIRTHDAY_MESSAGES).format(mention=member.mention)

            try:
                msg = await channel.send(message)
                await msg.add_reaction("🎂")
                await msg.add_reaction("🎉")
                print(f"✅ Sent birthday message for {name}")
                sent_log[user_id] = today_str
            except discord.Forbidden:
                print("⚠ Bot can see the channel but cannot send messages there.")
                return
            except Exception as e:
                print(f"⚠ Error sending birthday message: {e}")
                return

    save_json_file(SENT_FILE, sent_log)


@birthday_check.before_loop
async def before_birthday_check():
    await bot.wait_until_ready()


bot.run(TOKEN)