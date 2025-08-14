import discord
from discord.ext import commands, tasks
import aiohttp
import yaml
import os
import datetime
from database import Database
from command import CustomCommands
from logger import write_log

# Token aus config.yaml laden (versuche Projekt-Root, dann src/)
config_path = os.path.join(os.getcwd(), "config.yaml")
if not os.path.exists(config_path):
    # fallback: src/config.yaml
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    config_path = os.path.normpath(config_path)

with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

TOKEN = config.get("token")

CHECK_INTERVAL = 60  # Sekunden

db = Database()


class SiteMonitor:
    def __init__(self, db):
        self.db = db
        self.sites = self.db.load_sites()  # Lade aus DB
        self.stats = {}
        self.downtime_log = {}

    def add_site(self, url):
        self.sites[url] = True
        self.db.save_site(url)
        self.stats.setdefault(url, {"up": 0, "down": 0, "response_times": []})
        self.downtime_log.setdefault(url, [])
        write_log(f"Website hinzugefügt: {url}", db=db)

    def remove_site(self, url):
        self.sites.pop(url, None)
        self.db.delete_site(url)
        self.stats.pop(url, None)
        self.downtime_log.pop(url, None)
        write_log(f"Website entfernt: {url}", db=db)

    def get_status(self):
        return self.sites

    def log_downtime(self, url, timestamp):
        self.downtime_log.setdefault(url, []).append(timestamp)
        write_log(f"Downtime bei {url} um {timestamp}", db=db)


monitor = SiteMonitor(db)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot online als {bot.user}")
    write_log(f"Bot online als {bot.user}", bot=bot, db=db)
    await bot.add_cog(CustomCommands(bot, db, monitor))
    # Globale Synchronisation der App-Commands (ersetzt guild-spezifische Sync)
    try:
        synced = await bot.tree.sync()
        write_log(f"App-Commands global synchronisiert: {len(synced)} commands", bot=bot, db=db)
    except Exception as e:
        write_log(f"Fehler beim globalen Sync der App-Commands: {e}", bot=bot, db=db)
    check_websites.start()


@tasks.loop(seconds=CHECK_INTERVAL)
async def check_websites():
    async with aiohttp.ClientSession() as session:
        for url in list(monitor.sites.keys()):
            try:
                async with session.get(url, timeout=10) as resp:
                    response_time = None
                    try:
                        response_time = resp.elapsed.total_seconds()
                    except Exception:
                        response_time = None
                    if resp.status == 200:
                        monitor.stats.setdefault(url, {"up": 0, "down": 0, "response_times": []})
                        monitor.stats[url]["up"] += 1
                        if response_time:
                            monitor.stats[url]["response_times"].append(response_time)
                        monitor.sites[url] = True
                    else:
                        monitor.stats.setdefault(url, {"up": 0, "down": 0, "response_times": []})
                        monitor.stats[url]["down"] += 1
                        monitor.sites[url] = False
                        await notify_downtime(url)
                        monitor.log_downtime(url, discord.utils.utcnow())
                        write_log(f"Seite offline: {url}", db=db)
            except Exception as e:
                monitor.stats.setdefault(url, {"up": 0, "down": 0, "response_times": []})
                monitor.stats[url]["down"] += 1
                monitor.sites[url] = False
                await notify_downtime(url)
                monitor.log_downtime(url, discord.utils.utcnow())
                write_log(f"Fehler beim Check von {url}: {e}", db=db)


async def notify_downtime(url):
    channel_id = db.get_channel_id()
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if channel:
        embed = discord.Embed(title="Seite offline", description=f"{url}", color=discord.Color.red())
        await channel.send(embed=embed)


if __name__ == "__main__":
    bot.run(TOKEN)
