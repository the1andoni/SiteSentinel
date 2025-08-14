import discord
from discord import app_commands
from logger import write_log


class CustomCommands(discord.ext.commands.Cog):
    def __init__(self, bot, db, monitor):
        self.bot = bot
        self.db = db
        self.monitor = monitor

    async def cog_load(self):
        # Registriere App-Commands beim Bot CommandTree
        self.bot.tree.add_command(self.setlogchannel)
        self.bot.tree.add_command(self.setchannel)
        self.bot.tree.add_command(self.add)
        self.bot.tree.add_command(self.remove)
        self.bot.tree.add_command(self.status)

    @app_commands.command(name="setlogchannel", description="Setzt den Channel für Log-Meldungen")
    @app_commands.describe(channel="Text-Channel für Log-Meldungen")
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        channel_id = channel.id
        prev = self.db.get_log_channel_id()
        self.db.set_log_channel_id(channel_id)
        write_log(f"Log-Channel gesetzt: {channel_id} (vorher: {prev})", bot=self.bot, db=self.db)
        desc = f"Log-Meldungen werden jetzt in <#{channel_id}> gesendet."
        if prev:
            desc = f"Ersetzt <#{prev}> — " + desc
        embed = discord.Embed(title="Log-Channel gesetzt", description=desc, color=discord.Color.dark_grey())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setchannel", description="Setzt den Channel für Statusnachrichten")
    @app_commands.describe(channel="Text-Channel für Statusnachrichten")
    async def setchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        channel_id = channel.id
        prev = self.db.get_channel_id()
        self.db.set_channel_id(channel_id)
        write_log(f"Status-Channel gesetzt: {channel_id} (vorher: {prev})", bot=self.bot, db=self.db)
        desc = f"Statusnachrichten werden jetzt in <#{channel_id}> gesendet."
        if prev:
            desc = f"Ersetzt <#{prev}> — " + desc
        embed = discord.Embed(title="Channel gesetzt", description=desc, color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add", description="Fügt eine Website zur Überwachung hinzu")
    @app_commands.describe(url="URL der Website")
    async def add(self, interaction: discord.Interaction, url: str):
        self.monitor.add_site(url)
        self.db.save_site(url)
        write_log(f"Website hinzugefügt via Command: {url}", bot=self.bot, db=self.db)
        embed = discord.Embed(title="Website hinzugefügt", description=f"{url} wird jetzt überwacht.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="remove", description="Entfernt eine Website aus der Überwachung")
    @app_commands.describe(url="URL der Website")
    async def remove(self, interaction: discord.Interaction, url: str):
        self.monitor.remove_site(url)
        self.db.delete_site(url)
        write_log(f"Website entfernt via Command: {url}", bot=self.bot, db=self.db)
        embed = discord.Embed(title="Website entfernt", description=f"{url} wird nicht mehr überwacht.", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="status", description="Zeigt den Status aller überwachten Websites als Embed")
    async def status(self, interaction: discord.Interaction):
        status = self.monitor.get_status()
        embed = discord.Embed(title="Status der Websites", color=discord.Color.purple())
        for url, up in status.items():
            emoji = "✅" if up else "❌"
            embed.add_field(name=url, value=emoji, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Zeigt Bot- und Server-Informationen")
    async def ping(self, interaction: discord.Interaction):
        # websocket latency
        latency_ms = round(self.bot.latency * 1000)

        # TCP ping to 8.8.8.8:53 to estimate network latency
        tcp_latency_ms = None
        try:
            import socket, time
            start = time.perf_counter()
            sock = socket.create_connection(("8.8.8.8", 53), timeout=3)
            sock.close()
            end = time.perf_counter()
            tcp_latency_ms = round((end - start) * 1000)
        except Exception:
            tcp_latency_ms = None

        # Public IP and geolocation (optional)
        public_ip = None
        location = None
        try:
            import requests
            r = requests.get("https://ipinfo.io/json", timeout=3)
            if r.status_code == 200:
                info = r.json()
                public_ip = info.get("ip")
                loc = info.get("city")
                region = info.get("region")
                country = info.get("country")
                if loc or region or country:
                    location = ", ".join([x for x in [loc, region, country] if x])
        except Exception:
            pass

        # Hostname and local IP
        hostname = None
        local_ip = None
        try:
            import socket
            hostname = socket.gethostname()
            # try to get primary local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            except Exception:
                local_ip = socket.gethostbyname(hostname)
            finally:
                s.close()
        except Exception:
            pass

        embed = discord.Embed(title="Pong 🏓", color=discord.Color.green())
        embed.add_field(name="Bot Latency (WS)", value=f"{latency_ms} ms", inline=True)
        if tcp_latency_ms is not None:
            embed.add_field(name="TCP Ping (8.8.8.8:53)", value=f"{tcp_latency_ms} ms", inline=True)
        if public_ip:
            embed.add_field(name="Public IP", value=public_ip, inline=True)
        if location:
            embed.add_field(name="Standort (approx)", value=location, inline=True)
        if hostname:
            embed.add_field(name="Hostname", value=hostname, inline=True)
        if local_ip:
            embed.add_field(name="Lokale IP", value=local_ip, inline=True)


        await interaction.response.send_message(embed=embed)
