# SiteSentinel Discord Bot

## Übersicht
SiteSentinel ist ein modularer Discord-Bot zur Überwachung von Websites. Statusmeldungen und alle Infos werden als Discord-Embeds in einen frei wählbaren Channel gesendet. Einstellungen und Website-Daten werden in einer SQLite-Datenbank gespeichert und bleiben nach einem Neustart erhalten.

## Features
- Website-Überwachung mit Status-Checks
- Status- und Fehlernachrichten als Discord-Embeds
- Channel für Statusmeldungen per Slash-Command wählbar
- Log-Channel per Slash-Command (Log-Meldungen optional im Discord)
- SQLite-Datenbank für Persistenz
- Logdatei `Logs/Bot.log` wird automatisch gepflegt (ältere Einträge entfernt)

## Projektstruktur

```text
SiteSentinel
├── src
│   ├── command.py        # Slash-Commands (AppCommands) als Cog
│   ├── database.py       # SQLite-Datenbank für Channel-IDs, Log-Channel und Websites
├── bot.py                # Einstiegspunkt, initialisiert und startet den Bot
├── config.yaml           # Konfigurationsdatei für den Discord Token
├── requirements.txt      # Abhängigkeiten des Projekts
├── .gitignore            # Git-Ignore-Datei für sensible und temporäre Daten
├── LICENSE               # Lizenzinformationen (MIT)
├── CODE_OF_CONDUCT.md    # Verhaltensregeln für Mitwirkende
├── Logs
│   └── Bot.log           # Logdatei, enthält nur die letzten X Tage (Standard: 7 Tage)
├── README.md             # Projektdokumentation
```

| Datei/Ordner           | Beschreibung                                                        |
|------------------------|---------------------------------------------------------------------|
| `bot.py`               | Einstiegspunkt, initialisiert und startet den Bot                   |
| `src/command.py`       | Slash-Commands (AppCommands) als Cog                                |
| `src/database.py`      | SQLite-Datenbank für Channel-IDs, Log-Channel und Websites          |
| `config.yaml`          | Konfigurationsdatei für den Discord Token                           |
| `requirements.txt`     | Listet alle benötigten Python-Abhängigkeiten                        |
| `.gitignore`           | Git-Ignore-Datei für sensible und temporäre Daten                   |
| `LICENSE`              | Lizenzinformationen (MIT)                                           |
| `CODE_OF_CONDUCT.md`   | Verhaltensregeln für Mitwirkende                                    |
| `Logs/Bot.log`         | Logdatei, enthält nur die letzten X Tage (Standard: 7 Tage)         |
| `README.md`            | Projektdokumentation                                                |

### Grundlagen zur Konfiguration
Der Discord-Token wird in `config.yaml` gespeichert (YAML):

```yaml
token: DEIN_DISCORD_TOKEN_HIER
```

Zum Laden wird `pyyaml` verwendet:

```python
import yaml
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
TOKEN = config["token"]
```

Installiere Abhängigkeiten:

```bash
pip install -r requirements.txt
```

## Installation & Start
1. Python 3.8+ installieren
2. Abhängigkeiten installieren: `pip install -r requirements.txt`
3. `config.yaml` anlegen und Token eintragen
4. Bot starten:

```bash
python bot.py
```

## Slash-Commands (AppCommands)

- `/setchannel` — Setzt den aktuellen Channel für Statusmeldungen
- `/setlogchannel` — Setzt den Channel für Log-Meldungen (wird in der Datenbank gespeichert)
- `/add <url>` — Fügt eine Website zur Überwachung hinzu (wird in der Datenbank gespeichert)
- `/remove <url>` — Entfernt eine Website aus der Überwachung (wird aus der Datenbank gelöscht)
- `/status` — Zeigt den Status aller überwachten Websites als Embed

## Logging

- Logdatei: `Logs/Bot.log`
- Beim Schreiben entfernt der Bot ältere Einträge (Standard: älter als 7 Tage). Das Verhalten lässt sich über `log_event(..., max_age_days=...)` anpassen.
- Optional werden Log-Meldungen auch als Embed in einen Log-Channel gesendet (per `/setlogchannel` gesetzt).

## Hinweise

- Die Channel-IDs, Log-Channel und überwachte Websites werden in der SQLite-Datenbank gespeichert und bleiben nach Neustarts erhalten.
- Alle Nachrichten an Discord werden als Embeds gesendet.

## Lizenz
CyberSpaceConsulting Public License — siehe `LICENSE`

## CONTRIBUTING
Siehe `CODE_OF_CONDUCT.md` für Verhaltensregeln.
