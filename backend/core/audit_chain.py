"""Cryptographic Hash-Chained Audit Trail — SQLite backed with Merkle Tree."""
import hashlib
import hmac
import json
import time
import math
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from config import settings

logger = logging.getLogger("nexus.audit")


class AuditChain:
    """SHA-256 hash-chained decision log with Merkle tree verification and HMAC signatures."""

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
                current_hash TEXT NOT NULL,
                hmac_signature TEXT DEFAULT '',
                authenticated_user TEXT DEFAULT 'system'
            )
        """)
        # Add columns if they don't exist (migration-safe)
        try:
            self.conn.execute("ALTER TABLE decisions ADD COLUMN hmac_signature TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            self.conn.execute("ALTER TABLE decisions ADD COLUMN authenticated_user TEXT DEFAULT 'system'")
        except sqlite3.OperationalError:
            pass
        self.conn.commit()
        self.prev_hash = self._get_last_hash() or "GENESIS_BLOCK"

    def _get_last_hash(self) -> Optional[str]:
        row = self.conn.execute(
            "SELECT current_hash FROM decisions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None

    def _compute_hmac(self, data: str) -> str:
        """Compute HMAC-SHA256 signature for tamper detection."""
        return hmac.new(
            settings.SECRET_KEY.encode(),
            data.encode(),
            hashlib.sha256,
        ).hexdigest()[:32]

    def log_decision(
        self,
        agent: str,
        action: str,
        reasoning: str,
        cdil_state: dict,
        parameters: dict = None,
        authenticated_user: str = "system",
    ) -> dict:
        """Log a decision to the audit chain with HMAC signature. Returns the entry with hash."""
        with self._lock:
            timestamp = datetime.now().isoformat()
            cdil_hash = hashlib.sha256(
                json.dumps(cdil_state, sort_keys=True, default=str).encode()
            ).hexdigest()[:16]

            data_string = (
                f"{timestamp}|{agent}|{action}|{reasoning}|{cdil_hash}|{self.prev_hash}"
            )
            current_hash = hashlib.sha256(data_string.encode()).hexdigest()[:16]

            # HMAC signature for tamper detection
            hmac_sig = self._compute_hmac(data_string + "|" + current_hash)

            self.conn.execute(
                """INSERT INTO decisions
                   (timestamp, agent, action, parameters, reasoning,
                    cdil_state_hash, prev_hash, current_hash,
                    hmac_signature, authenticated_user)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    timestamp,
                    agent,
                    action,
                    json.dumps(parameters) if parameters else "{}",
                    reasoning,
                    cdil_hash,
                    self.prev_hash,
                    current_hash,
                    hmac_sig,
                    authenticated_user,
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
                "hmac_signature": hmac_sig,
                "authenticated_user": authenticated_user,
            }

            self.prev_hash = current_hash
            logger.info(f"[Audit] #{entry['id']} {agent}/{action} → {current_hash}")
            return entry

    def verify_chain(self) -> Tuple[bool, str, int]:
        """Verify entire chain integrity including HMAC signatures. Returns (valid, message, count)."""
        rows = self.conn.execute(
            "SELECT id, timestamp, agent, action, parameters, reasoning, "
            "cdil_state_hash, prev_hash, current_hash, hmac_signature "
            "FROM decisions ORDER BY id"
        ).fetchall()

        if not rows:
            return True, "Empty chain — no decisions recorded yet", 0

        prev = "GENESIS_BLOCK"
        hmac_failures = 0
        for row in rows:
            rid, ts, agent, action, params, reasoning, cdil_hash, prev_hash, cur_hash, hmac_sig = row

            # Verify chain linkage
            if prev_hash != prev:
                return False, f"CHAIN BREAK at decision #{rid} — prev_hash mismatch", rid

            # Recompute hash
            data_string = f"{ts}|{agent}|{action}|{reasoning}|{cdil_hash}|{prev_hash}"
            expected = hashlib.sha256(data_string.encode()).hexdigest()[:16]
            if expected != cur_hash:
                return False, f"TAMPER DETECTED at decision #{rid} by {agent}", rid

            # Verify HMAC signature (if present)
            if hmac_sig:
                expected_hmac = self._compute_hmac(data_string + "|" + cur_hash)
                if expected_hmac != hmac_sig:
                    hmac_failures += 1

            prev = cur_hash

        msg = f"Chain integrity VERIFIED. {len(rows)} decisions audited."
        if hmac_failures > 0:
            msg += f" WARNING: {hmac_failures} HMAC signature mismatches."
        return True, msg, len(rows)

    def compute_merkle_root(self, start_id: int = None, end_id: int = None) -> str:
        """
        Compute Merkle tree root over a range of audit entries.
        Enables efficient subset verification and proof-of-integrity.
        """
        query = "SELECT current_hash FROM decisions"
        params = []
        conditions = []

        if start_id is not None:
            conditions.append("id >= ?")
            params.append(start_id)
        if end_id is not None:
            conditions.append("id <= ?")
            params.append(end_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id"

        rows = self.conn.execute(query, params).fetchall()
        if not rows:
            return hashlib.sha256(b"EMPTY_TREE").hexdigest()[:32]

        # Build Merkle tree
        leaves = [row[0].encode() for row in rows]
        return self._merkle_root(leaves)

    def _merkle_root(self, leaves: list) -> str:
        """Compute Merkle root from list of leaf hashes."""
        if len(leaves) == 0:
            return hashlib.sha256(b"EMPTY").hexdigest()[:32]
        if len(leaves) == 1:
            return hashlib.sha256(leaves[0]).hexdigest()[:32]

        # Build tree level by level
        current = list(leaves)
        while len(current) > 1:
            # Pad to even number
            if len(current) % 2 != 0:
                current.append(current[-1])
            next_level = []
            for i in range(0, len(current), 2):
                combined = current[i] + current[i + 1]
                next_level.append(hashlib.sha256(combined).hexdigest().encode())
            current = next_level

        return current[0].decode()[:32]

    def export_chain_proof(self) -> dict:
        """Export full chain proof for external verification."""
        valid, message, count = self.verify_chain()
        merkle_root = self.compute_merkle_root()

        return {
            "chain_valid": valid,
            "verification_message": message,
            "total_decisions": count,
            "merkle_root": merkle_root,
            "genesis_hash": "GENESIS_BLOCK",
            "latest_hash": self.prev_hash,
            "verification_timestamp": datetime.now().isoformat(),
            "signing_algorithm": "SHA-256 + HMAC-SHA256",
        }

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
