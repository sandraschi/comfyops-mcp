"""comfy_library portmanteau — recent, search, record."""

import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

from fastmcp import FastMCP

from comfyops_mcp import config as _cfg

logger = logging.getLogger(__name__)


def _db_path() -> Path:
    return Path(_cfg.DATA_DIR) / "library.sqlite3"


def _init_db():
    dbp = _db_path()
    dbp.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(dbp)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id TEXT UNIQUE, workflow_id TEXT, prompt TEXT,
                seed INTEGER, model TEXT, params TEXT, outputs TEXT,
                created_at TEXT
            )
        """)


def register_tools(mcp: FastMCP):
    @mcp.tool(annotations={"readonly": True})
    async def comfy_library(
        operation: Annotated[Literal["recent", "search", "record"],
                             "Operation to perform."],
        limit: Annotated[int | None, "Max results."] = 20,
        query: Annotated[str | None, "Search text."] = None,
        prompt_id: Annotated[str | None, "Prompt ID for record."] = None,
        workflow_id: Annotated[str | None, "Workflow ID for record."] = None,
        prompt_text: Annotated[str | None, "Prompt for record."] = None,
        seed_val: Annotated[int | None, "Seed for record."] = None,
        model: Annotated[str | None, "Model for record."] = None,
        outputs: Annotated[str | None, "JSON outputs for record."] = None,
    ) -> dict:
        """Browse past generations and record new ones.

        ## Return Format
        {"success": bool, "generations": [...], "message": str}

        ## Examples
            comfy_library(operation="recent", limit=10)
            comfy_library(operation="search", query="cat surfing")
        """
        _init_db()

        if operation == "recent":
            with sqlite3.connect(str(_db_path())) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM generations ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return {"success": True, "generations": [dict(r) for r in rows],
                    "message": f"{len(rows)} recent generations."}

        if operation == "search":
            if not query:
                return {"success": False, "error": "query required."}
            with sqlite3.connect(str(_db_path())) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM generations WHERE prompt LIKE ? ORDER BY created_at DESC LIMIT ?",
                    (f"%{query}%", limit),
                ).fetchall()
            return {"success": True, "generations": [dict(r) for r in rows],
                    "message": f"Found {len(rows)} matches."}

        if operation == "record":
            if not prompt_id:
                return {"success": False, "error": "prompt_id required."}
            with sqlite3.connect(str(_db_path())) as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO generations "
                    "(prompt_id, workflow_id, prompt, seed, model, params, outputs, created_at) "
                    "VALUES (?, ?, ?, ?, ?, '{}', ?, ?)",
                    (prompt_id, workflow_id or "", prompt_text or "",
                     seed_val or 0, model or "", outputs or "[]",
                     datetime.now(UTC).isoformat()),
                )
            return {"success": True, "message": "Generation recorded."}

        return {"success": False, "error": f"Unknown operation: {operation}"}
