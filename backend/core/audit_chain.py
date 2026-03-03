"""Cryptographic Hash-Chained Audit Trail — SQLite backed."""
import hashlib
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("nexus.audit")


class AuditChain:
    """SHA-256 hash-chained decision log. Every agent decision is immutably recorded."""

    def __init__(self, db_path: str = "data/audit.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent TEXT NOT NULL,
                action TEXT NOT NULL,
                parameters TEXT,
                reasoning TEXT NOT NULL,
                cdil_state_hash TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                current_hash TEXT NOT NULL
            )
        """)
        self.conn.commit()
        self.prev_hash = self._get_last_hash() or "GENESIS_BLOCK"

    def _get_last_hash(self) -> Optional[str]:
        row = self.conn.execute(
            "SELECT current_hash FROM decisions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None

    def log_decision(
        self,
        agent: str,
        action: str,
        reasoning: str,
        cdil_state: dict,
        parameters: dict = None,
    ) -> dict:
        """Log a decision to the audit chain. Returns the entry with hash."""
        with self._lock:
            timestamp = datetime.now().isoformat()
            cdil_hash = hashlib.sha256(
                json.dumps(cdil_state, sort_keys=True, default=str).encode()
            ).hexdigest()[:16]

            data_string = (
                f"{timestamp}|{agent}|{action}|{reasoning}|{cdil_hash}|{self.prev_hash}"
            )
            current_hash = hashlib.sha256(data_string.encode()).hexdigest()[:16]

            self.conn.execute(
                """INSERT INTO decisions
                   (timestamp, agent, action, parameters, reasoning,
                    cdil_state_hash, prev_hash, current_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    timestamp,
                    agent,
                    action,
                    json.dumps(parameters) if parameters else "{}",
                    reasoning,
                    cdil_hash,
                    self.prev_hash,
                    current_hash,
                ),
            )
            self.conn.commit()

            entry = {
                "id": self.conn.execute("SELECT last_insert_rowid()").fetchone()[0],
                "timestamp": timestamp,
                "agent": agent,
                "action": action,
                "parameters": parameters,
                "reasoning": reasoning,
                "cdil_state_hash": cdil_hash,
                "prev_hash": self.prev_hash,
                "hash": current_hash,
            }

            self.prev_hash = current_hash
            logger.info(f"[Audit] #{entry['id']} {agent}/{action} → {current_hash}")
            return entry

    def verify_chain(self) -> Tuple[bool, str, int]:
        """Verify entire chain integrity. Returns (valid, message, count)."""
        rows = self.conn.execute(
            "SELECT id, timestamp, agent, action, parameters, reasoning, "
            "cdil_state_hash, prev_hash, current_hash "
            "FROM decisions ORDER BY id"
        ).fetchall()

        if not rows:
            return True, "Empty chain — no decisions recorded yet", 0

        prev = "GENESIS_BLOCK"
        for row in rows:
            rid, ts, agent, action, params, reasoning, cdil_hash, prev_hash, cur_hash = row

            # Verify chain linkage
            if prev_hash != prev:
                return False, f"CHAIN BREAK at decision #{rid} — prev_hash mismatch", rid

            # Recompute hash
            data_string = f"{ts}|{agent}|{action}|{reasoning}|{cdil_hash}|{prev_hash}"
            expected = hashlib.sha256(data_string.encode()).hexdigest()[:16]
            if expected != cur_hash:
                return False, f"TAMPER DETECTED at decision #{rid} by {agent}", rid

            prev = cur_hash

        return True, f"Chain integrity VERIFIED. {len(rows)} decisions audited.", len(rows)

    def get_recent(self, n: int = 20) -> List[dict]:
        """Get the last N audit entries."""
        rows = self.conn.execute(
            "SELECT id, timestamp, agent, action, parameters, reasoning, "
            "cdil_state_hash, prev_hash, current_hash "
            "FROM decisions ORDER BY id DESC LIMIT ?",
            (n,),
        ).fetchall()

        return [
            {
                "id": r[0],
                "timestamp": r[1],
                "agent": r[2],
                "action": r[3],
                "parameters": json.loads(r[4]) if r[4] else None,
                "reasoning": r[5],
                "cdil_state_hash": r[6],
                "prev_hash": r[7],
                "hash": r[8],
            }
            for r in reversed(rows)
        ]

    def get_full_chain(self) -> List[dict]:
        """Get entire chain."""
        return self.get_recent(n=10000)

    def get_count(self) -> int:
        """Get total number of decisions."""
        row = self.conn.execute("SELECT COUNT(*) FROM decisions").fetchone()
        return row[0] if row else 0
