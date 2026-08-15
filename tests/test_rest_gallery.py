"""Tests for the gallery REST query layer (filters, sort, pagination, delete)."""

from __future__ import annotations

import sqlite3

import pytest

from comfyops_mcp.rest_api import _library_query


def _seed(rows: list[tuple]) -> None:
    from comfyops_mcp.rest_api import _library_db

    dbp = _library_db()
    dbp.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(dbp)) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS generations ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, prompt_id TEXT UNIQUE,"
            "workflow_id TEXT, prompt TEXT, seed INTEGER, model TEXT,"
            "params TEXT, outputs TEXT, created_at TEXT)"
        )
        for pid, wf, prompt, seed, model, ts in rows:
            conn.execute(
                "INSERT OR IGNORE INTO generations (prompt_id, workflow_id, prompt, seed, model, params, outputs, created_at) "
                "VALUES (?, ?, ?, ?, ?, '{}', '[]', ?)",
                (pid, wf, prompt, seed, model, ts),
            )


@pytest.fixture(autouse=True)
def seeded_library(isolated_config):
    _seed(
        [
            ("p1", "flux-klein-t2i", "a cat surfing", 42, "flux1-klein-dev", "2026-08-10T08:00:00+00:00"),
            ("p2", "flux-klein-t2i", "a dog running", 43, "flux1-klein-dev", "2026-08-11T08:00:00+00:00"),
            ("p3", "sd15-t2i", "a bird", 7, "sd_v1-5", "2026-08-12T08:00:00+00:00"),
            ("p4", "sd15-t2i", "a fish", 8, "sd_v1-5", "2026-08-13T08:00:00+00:00"),
        ]
    )


class TestQuery:
    async def test_all_desc(self):
        items, total = _library_query(limit=20)
        assert total == 4
        assert [i["prompt_id"] for i in items] == ["p4", "p3", "p2", "p1"]

    async def test_filter_workflow(self):
        items, total = _library_query(workflow_id="sd15-t2i")
        assert total == 2
        assert {i["prompt_id"] for i in items} == {"p3", "p4"}

    async def test_filter_model(self):
        items, total = _library_query(model="flux1-klein-dev")
        assert total == 2
        assert {i["prompt_id"] for i in items} == {"p1", "p2"}

    async def test_search_q(self):
        items, total = _library_query(q="cat")
        assert total == 1
        assert items[0]["prompt_id"] == "p1"

    async def test_date_range(self):
        items, total = _library_query(date_from="2026-08-12", date_to="2026-08-13")
        assert total == 2
        assert {i["prompt_id"] for i in items} == {"p3", "p4"}

    async def test_sort_seed_asc(self):
        items, _ = _library_query(sort="seed")
        assert [i["seed"] for i in items] == [7, 8, 42, 43]

    async def test_sort_workflow(self):
        items, _ = _library_query(sort="workflow")
        assert items[0]["workflow_id"] == "flux-klein-t2i"

    async def test_pagination(self):
        items, total = _library_query(limit=2, offset=2)
        assert total == 4
        assert [i["prompt_id"] for i in items] == ["p2", "p1"]

    async def test_empty_db(self, tmp_path):
        from unittest.mock import patch

        from comfyops_mcp import config as cfg

        with patch.object(cfg, "DATA_DIR", str(tmp_path)):
            items, total = _library_query()
        assert items == [] and total == 0


class TestDelete:
    async def test_delete_removes_rows(self, isolated_config):
        from comfyops_mcp.rest_api import _library_db

        dbp = _library_db()
        with sqlite3.connect(str(dbp)) as conn:
            deleted = conn.execute("DELETE FROM generations WHERE prompt_id IN ('p1','p3')").rowcount
        assert deleted == 2
        items, total = _library_query()
        assert total == 2
        assert {i["prompt_id"] for i in items} == {"p2", "p4"}

    async def test_delete_missing_id_is_noop(self, isolated_config):
        from comfyops_mcp.rest_api import _library_db

        dbp = _library_db()
        with sqlite3.connect(str(dbp)) as conn:
            deleted = conn.execute("DELETE FROM generations WHERE prompt_id = 'nope'").rowcount
        assert deleted == 0
