import os
import datetime
import discord

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Logs")
LOG_FILE = os.path.join(LOG_DIR, "Bot.log")


def write_log(message: str, *, bot: discord.Client = None, db=None, max_age_days: int = 7):
    """Write a timestamped log line to Logs/Bot.log, prune entries older than max_age_days.

    Parameters:
    - message: the message to log
    - bot: optional discord.Client to allow sending log messages to a configured log channel
    - db: optional Database instance with get_log_channel_id()
    - max_age_days: retention in days
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"

    os.makedirs(LOG_DIR, exist_ok=True)

    # read existing lines and keep recent ones
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = []
            cutoff = datetime.datetime.now() - datetime.timedelta(days=max_age_days)
            for line in lines:
                if line.startswith("["):
                    try:
                        date_str = line.split("]")[0][1:]
                        log_time = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        if log_time >= cutoff:
                            new_lines.append(line)
                    except Exception:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
        else:
            new_lines = []
    except Exception:
        new_lines = []

    new_lines.append(log_line)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # optionally send to discord channel if db and bot provided
    if db is not None and bot is not None:
        try:
            log_channel_id = db.get_log_channel_id()
            if log_channel_id:
                channel = bot.get_channel(log_channel_id)
                if channel:
                    # fire-and-forget
                    import asyncio
                    asyncio.create_task(channel.send(embed=discord.Embed(title="Bot Log", description=message, color=discord.Color.dark_grey())))
        except Exception:
            pass
