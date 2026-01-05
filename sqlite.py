from loguru import logger
from config import Config
import sqlite3
import os

class sqlite:
    def __init__(self, db_path="db/words.db"):
        self.db_path = db_path
        folder = os.path.dirname(db_path)
        os.makedirs(folder, exist_ok=True)
        self._init_table()

    def _init_table(self):
        """Creates table and index safely."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dictionary (
                    word TEXT PRIMARY KEY,
                    length INTEGER,
                    acknowledged BOOLEAN,
                    hanbang BOOLEAN
                )
            """)
            """Try adding hanbang"""
            try:
                cursor.execute("ALTER TABLE dictionary ADD COLUMN hanbang BOOLEAN")
            except Exception as e:
                pass
            """Indexing"""
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_word ON dictionary (word)")
            conn.commit()

    def addWords(self, words):
        if not words: 
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for word, ack in words:
                    word = word.strip()
                    cursor.execute(
                        "INSERT OR IGNORE INTO dictionary (word, length, acknowledged, hanbang) VALUES (?, ?, ?, ?)", 
                        (word, len(word), ack, False)
                    )
                conn.commit()
                logger.success(f"Added {len(words)} words into '{self.db_path}'")
        except Exception as e:
            logger.error(f"Failed to add word '{word}': {e}")
    
    def addTuples(self, tuples):
        if not tuples: return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for tup in tuples:
                    word = tup[0].strip()
                    cursor.execute(
                        "INSERT OR IGNORE INTO dictionary (word, length, acknowledged, hanbang) VALUES (?, ?, ?, ?)", 
                        (word, len(word), tup[1], False)
                    )
                conn.commit()
                logger.success(f"Pushed {cursor.rowcount} word(s) into '{self.db_path}'")
        except Exception as e:
            logger.error(e)
            return
    
    def deleteWords(self, words):
        if not words: return
        lst = [(word.strip(),) for word in words]
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany("DELETE FROM dictionary WHERE word = ?", lst)
                conn.commit()
                logger.warning(f"Deleted {cursor.rowcount} word(s) from '{self.db_path}'")
        except Exception as e:
            logger.error(e)

    def markHanbang(self, words):
        if not words: return
        lst = [(word.strip(),) for word in words]
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany("UPDATE dictionary SET hanbang = 1 WHERE word = ?", lst)
                conn.commit()
                logger.info(f"Marked {cursor.rowcount} words as hanbang.")
        except Exception as e:
            logger.error(e)

    def getWords(self, start_char: str, ack: bool, manner: bool):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = """
                    SELECT word 
                    FROM dictionary 
                    WHERE word LIKE ?
                """
                params = [f"{start_char}%"]
                if not ack:
                    query += "AND acknowledged = ?"
                    params.append(ack)
                if manner:
                    query += "AND hanbang IS NOT ?"
                    params.append(manner)
                query += """
                    ORDER BY length DESC
                """
                if Config.getWordLimit != 50:
                    query += """ LIMIT """
                    query += str(Config.getWordLimit)
                cursor.execute(query, params)
                res = cursor.fetchall()
                if res:
                    return [word[0] for word in res]
                return None
        except Exception as e:
            logger.error(e)
            return None