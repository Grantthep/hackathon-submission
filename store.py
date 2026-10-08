"""Versioned prompt storage.

Uses Supabase when SUPABASE_URL and SUPABASE_KEY are set, otherwise a local
JSON file. Every update is a new version, so you can see how the prompt learned.

Supabase table (run once in the SQL editor):
    create table prompts (
      id bigint generated always as identity primary key,
      name text not null,
      prompt text not null,
      source text,
      note text,
      created_at timestamptz default now()
    );
"""
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

import prompts as seeds

SEEDS = {"chatbot": seeds.CHATBOT_PROMPT, "editor": seeds.EDITOR_PROMPT}
LOCAL_FILE = Path(__file__).with_name("prompt_store.json")
_lock = threading.Lock()


def _supabase():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not (url and key):
        return None
    from supabase import create_client
    return create_client(url, key).table("prompts")


def backend():
    return "supabase" if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY") else "local"


def _read_local():
    if LOCAL_FILE.exists():
        return json.loads(LOCAL_FILE.read_text(encoding="utf-8"))
    return []


def history(name):
    """All versions of a prompt, oldest first."""
    table = _supabase()
    if table:
        rows = table.select("*").eq("name", name).order("id").execute().data
    else:
        rows = [r for r in _read_local() if r["name"] == name]
    if not rows:
        rows = [{"id": 0, "name": name, "prompt": SEEDS[name], "source": "seed", "note": "", "created_at": None}]
    return rows


def get(name):
    return history(name)[-1]["prompt"]


def save(name, prompt, source, note=""):
    row = {"name": name, "prompt": prompt, "source": source, "note": note}
    table = _supabase()
    if table:
        return table.insert(row).execute().data[0]
    with _lock:
        rows = _read_local()
        row.update(id=len(rows) + 1, created_at=datetime.now(timezone.utc).isoformat())
        rows.append(row)
        LOCAL_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return row
