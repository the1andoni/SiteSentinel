import sqlite3

class Database:
    def __init__(self, db_path="data.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS websites (
                url TEXT PRIMARY KEY,
                status TEXT,
                last_checked TEXT
            )
        """)
        self.conn.commit()

    def set_log_channel_id(self, channel_id):
        cursor = self.conn.cursor()
        cursor.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", ("log_channel_id", str(channel_id)))
        self.conn.commit()

    def get_log_channel_id(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key=?", ("log_channel_id",))
        result = cursor.fetchone()
        return int(result[0]) if result else None

    def set_channel_id(self, channel_id):
        cursor = self.conn.cursor()
        cursor.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", ("channel_id", str(channel_id)))
        self.conn.commit()

    def get_channel_id(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key=?", ("channel_id",))
        result = cursor.fetchone()
        return int(result[0]) if result else None

    def save_site(self, url):
        cursor = self.conn.cursor()
        cursor.execute("REPLACE INTO websites (url, status, last_checked) VALUES (?, ?, ?)", (url, 'unknown', ''))
        self.conn.commit()

    def delete_site(self, url):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM websites WHERE url=?", (url,))
        self.conn.commit()

    def load_sites(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM websites")
        rows = cursor.fetchall()
        # Returniere nur die URLs, nicht den Status (wird im SiteMonitor auf None gesetzt)
        return [row[0] for row in rows]
