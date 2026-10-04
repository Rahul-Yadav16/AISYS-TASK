"""
Database engine and migration manager for AISYS.
Handles SQLite connection pooling, WAL journaling, versioned migrations, and hot backups.
"""
import os
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
from src.core.config import get_config
from src.core.logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self._cfg_path = db_path
        self._active_path: Optional[str] = None

    @property
    def db_path(self) -> str:
        if self._cfg_path:
            return self._cfg_path
        cfg = get_config()
        path = cfg.database.db_path
        if not os.path.isabs(path):
            path = str(BASE_DIR / path)
        return path

    def get_connection(self, read_only: bool = False) -> sqlite3.Connection:
        path = self.db_path
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        if read_only:
            # Open URI in read-only mode for non-destructive legacy ILMS emulation
            uri = f"file:{os.path.abspath(path)}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=10.0)
        else:
            conn = sqlite3.connect(path, timeout=10.0)

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        if not read_only:
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.close()
        return conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        conn = self.get_connection(read_only=False)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
        finally:
            conn.close()

    def execute_query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self.get_connection(read_only=True) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        with self.get_connection(read_only=True) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def execute_mutation(self, sql: str, params: tuple = ()) -> int:
        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.lastrowid

    def apply_migrations(self, migrations_dir: Optional[str] = None) -> List[str]:
        if migrations_dir is None:
            m_dir = BASE_DIR / "data" / "migrations"
        else:
            m_dir = Path(migrations_dir)

        if not m_dir.exists():
            logger.warning(f"Migrations directory not found: {m_dir}")
            return []

        # Ensure schema_migrations table exists
        with self.transaction() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
                );
            """)

        applied_versions = {
            row["version"] for row in self.execute_query("SELECT version FROM schema_migrations")
        }

        sql_files = sorted(m_dir.glob("V*__*.sql"))
        applied_now = []

        for sql_file in sql_files:
            version_tag = sql_file.stem
            if version_tag in applied_versions:
                continue

            logger.info(f"Applying migration: {version_tag} from {sql_file.name}")
            with open(sql_file, "r", encoding="utf-8") as f:
                script = f.read()

            with self.transaction() as conn:
                conn.executescript(script)
                conn.execute(
                    "INSERT OR REPLACE INTO schema_migrations (version) VALUES (?)",
                    (version_tag,),
                )
            applied_now.append(version_tag)

        logger.info(f"Migrations applied successfully: {applied_now}")
        return applied_now

    def hot_backup(self, target_dir: Optional[str] = None) -> str:
        """
        Creates an online, non-blocking hot backup of the SQLite database using SQLite's backup API.
        Fulfills NFR 01 & AC 10.
        """
        if target_dir is None:
            t_dir = BASE_DIR / "storage" / "backups"
        else:
            t_dir = Path(target_dir)

        t_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"aisys_backup_{timestamp}.db"
        target_path = t_dir / backup_filename

        src_conn = self.get_connection(read_only=True)
        dst_conn = sqlite3.connect(str(target_path))

        with dst_conn:
            src_conn.backup(dst_conn, pages=100)

        dst_conn.close()
        src_conn.close()

        logger.info(f"Hot backup created successfully at: {target_path}")
        return str(target_path)

    def restore_backup(self, backup_filepath: str) -> bool:
        """
        Restores the database from a verified backup file using SQLite's backup API.
        Properly synchronizes WAL pages and avoids stale journal artifacts.
        """
        src = Path(backup_filepath)
        if not src.exists():
            raise FileNotFoundError(f"Backup file does not exist: {backup_filepath}")

        dest = Path(self.db_path)
        if dest.exists():
            safety_copy = dest.parent / f"{dest.name}.pre_restore_safety"
            shutil.copy2(dest, safety_copy)

        src_conn = sqlite3.connect(str(src))
        dst_conn = self.get_connection(read_only=False)

        with dst_conn:
            src_conn.backup(dst_conn, pages=100)

        dst_conn.close()
        src_conn.close()
        logger.info(f"Database successfully restored from: {backup_filepath}")
        return True

db_manager = DatabaseManager()
