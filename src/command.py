import discord
from discord import app_commands
from logger import write_log


class CustomCommands(discord.ext.commands.Cog):
    def __init__(self, bot, db, monitor):
        self.bot = bot
        self.db = db
        self.monitor = monitor

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
        await interaction.response.defer()
        
        status = self.monitor.get_status()
        if not status:
            embed = discord.Embed(
                title="Status der Websites", 
                description="Keine Websites werden überwacht.",
                color=discord.Color.gray()
            )
            await interaction.followup.send(embed=embed)
            return
            
        embed = discord.Embed(title="Status der Websites", color=discord.Color.purple())
        
        # Favicon-Helper Funktion
        async def get_favicon_url(url):
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                return f"https://www.google.com/s2/favicons?domain={parsed.netloc}&sz=16"
            except:
                return None
        
        for url, up in status.items():
            emoji = "🟢" if up else "🔴"
            status_text = "Online" if up else "Offline"
            
            # Statistiken hinzufügen falls verfügbar
            stats_text = status_text
            if url in self.monitor.stats:
                stats = self.monitor.stats[url]
                uptime_total = stats["up"] + stats["down"]
                if uptime_total > 0:
                    uptime_percent = round((stats["up"] / uptime_total) * 100, 1)
                    stats_text += f" ({uptime_percent}% Uptime)"
                    
                    # Durchschnittliche Response-Zeit
                    if stats["response_times"]:
                        avg_response = round(sum(stats["response_times"]) / len(stats["response_times"]) * 1000)
                        stats_text += f"\n⚡ {avg_response}ms avg"
            
            embed.add_field(name=f"{emoji} {url}", value=stats_text, inline=False)
        
        embed.set_footer(text="Site Sentinel", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ping", description="Testet eine URL und zeigt Response-Informationen")
    @app_commands.describe(url="URL der Website die getestet werden soll")
    async def ping(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        
        import aiohttp
        import time
        from urllib.parse import urlparse
        
        # URL validieren und formatieren
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Favicon URL generieren
        try:
            parsed = urlparse(url)
            favicon_url = f"https://www.google.com/s2/favicons?domain={parsed.netloc}&sz=32"
        except:
            favicon_url = None
        
        try:
            start_time = time.perf_counter()
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    end_time = time.perf_counter()
                    response_time_ms = round((end_time - start_time) * 1000)
                    
                    # Response-Daten sammeln
                    status_code = response.status
                    content_type = response.headers.get('Content-Type', 'N/A')
                    content_length = response.headers.get('Content-Length', 'N/A')
                    server = response.headers.get('Server', 'N/A')
                    last_modified = response.headers.get('Last-Modified', 'N/A')
                    
                    # Status-Farbe bestimmen
                    if 200 <= status_code < 300:
                        color = discord.Color.green()
                        status_emoji = "🟢"
                    elif 300 <= status_code < 400:
                        color = discord.Color.yellow()
                        status_emoji = "�"
                    elif 400 <= status_code < 500:
                        color = discord.Color.orange()
                        status_emoji = "🟠"
                    else:
                        color = discord.Color.red()
                        status_emoji = "🔴"
                    
                    embed = discord.Embed(
                        title=f"Ping Ergebnis",
                        description=f"**{url}**", 
                        color=color,
                        timestamp=discord.utils.utcnow()
                    )
                    
                    embed.add_field(name="Status", value=f"{status_emoji} {status_code}", inline=True)
                    embed.add_field(name="Response Time", value=f"⚡ {response_time_ms} ms", inline=True)
                    embed.add_field(name="Content-Type", value=content_type[:50], inline=True)
                    
                    if content_length != 'N/A':
                        # Formatierte Größe
                        try:
                            size_bytes = int(content_length)
                            if size_bytes < 1024:
                                size_str = f"{size_bytes} B"
                            elif size_bytes < 1024*1024:
                                size_str = f"{size_bytes/1024:.1f} KB"
                            else:
                                size_str = f"{size_bytes/(1024*1024):.1f} MB"
                            embed.add_field(name="Content-Length", value=size_str, inline=True)
                        except:
                            embed.add_field(name="Content-Length", value=content_length, inline=True)
                    
                    if server != 'N/A':
                        embed.add_field(name="Server", value=server[:50], inline=True)
                    
                    if last_modified != 'N/A':
                        embed.add_field(name="Last-Modified", value=last_modified[:50], inline=True)
                    
                    if favicon_url:
                        embed.set_thumbnail(url=favicon_url)
                    
                    embed.set_footer(text="Site Sentinel", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
                    
        except aiohttp.ClientTimeout:
            embed = discord.Embed(
                title=f"Ping Ergebnis",
                description=f"**{url}**", 
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Fehler", value="🔴 Timeout (>10s)", inline=False)
            if favicon_url:
                embed.set_thumbnail(url=favicon_url)
            embed.set_footer(text="Site Sentinel")
            
        except aiohttp.ClientError as e:
            embed = discord.Embed(
                title=f"Ping Ergebnis",
                description=f"**{url}**", 
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Fehler", value=f"🔴 Client Error: {str(e)}", inline=False)
            if favicon_url:
                embed.set_thumbnail(url=favicon_url)
            embed.set_footer(text="Site Sentinel")
            
        except Exception as e:
            embed = discord.Embed(
                title=f"Ping Ergebnis",
                description=f"**{url}**", 
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Fehler", value=f"🔴 {str(e)}", inline=False)
            if favicon_url:
                embed.set_thumbnail(url=favicon_url)
            embed.set_footer(text="Site Sentinel")

        await interaction.followup.send(embed=embed)
