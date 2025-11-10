from __future__ import annotations
import json
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from app.core.db import db

router = APIRouter()

def _get(conn, sid: str):
    cur = conn.cursor()
    cur.execute("SELECT id, name, owner_id, data FROM scenarios WHERE id=?", (sid,))
    row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "owner_id": row["owner_id"],
        "objetos": json.loads(row["data"]).get("objetos", []),
    }

@router.get("/scenarios")
def list_scenarios():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT id, name, owner_id FROM scenarios ORDER BY id")
    out = [{"id": r["id"], "name": r["name"], "owner_id": r["owner_id"]} for r in cur.fetchall()]
    conn.close()
    return out

@router.get("/scenario/{sid}")
def get_scenario(sid: str):
    conn = db()
    data = _get(conn, sid)
    conn.close()
    if not data:
        raise HTTPException(status_code=404, detail="Not found")
    return data

@router.post("/scenario")
def upsert_scenario(payload: Dict[str, Any]):
    sid = payload.get("id")
    name = payload.get("name", "")
    owner_id = payload.get("owner_id", "anon")
    objetos = payload.get("objetos", [])
    if not sid:
        raise HTTPException(status_code=400, detail="Missing id")

    conn = db(); cur = conn.cursor()
    enc = json.dumps({"objetos": objetos}, ensure_ascii=False)
    cur.execute("SELECT 1 FROM scenarios WHERE id=?", (sid,))
    if cur.fetchone():
        cur.execute("UPDATE scenarios SET name=?, owner_id=?, data=? WHERE id=?",
                    (name, owner_id, enc, sid))
    else:
        cur.execute("INSERT INTO scenarios(id, name, owner_id, data) VALUES(?,?,?,?)",
                    (sid, name, owner_id, enc))
    conn.commit(); conn.close()
    return {"id": sid, "name": name, "owner_id": owner_id, "objetos": objetos}

@router.delete("/scenario/{sid}")
def delete_scenario(sid: str):
    conn = db(); cur = conn.cursor()
    cur.execute("DELETE FROM scenarios WHERE id=?", (sid,))
    conn.commit(); conn.close()
    return {"ok": True, "id": sid}
