import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import json
from datetime import datetime

import yaml
from sqlalchemy import select

from app.database import get_engine, get_session_factory
from app.models import Base, AirdropProject, AirdropTask

DATE_FIELDS = ("snapshot_at", "eligibility_at", "claim_at", "deadline_at", "last_verified_at")

def parse_dt(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    raise ValueError(f"invalid datetime value: {value!r}")

async def main():
    data = yaml.safe_load(Path("config/airdrops.yaml").read_text(encoding="utf-8")) or {}
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with get_session_factory()() as db:
        for item in data.get("projects", []):
            p = (await db.execute(select(AirdropProject).where(AirdropProject.slug == item["slug"]))).scalar_one_or_none()
            fields = {k: item.get(k) for k in [
                "name", "chain_id", "status", "potential_score", "risk_score", "risk_level",
                "official_website", "official_claim_url", "source_type"
            ]}
            fields.update({k: parse_dt(item.get(k)) for k in DATE_FIELDS})
            fields["notes_json"] = json.dumps(item.get("notes", {}), ensure_ascii=False)
            if p:
                for k, v in fields.items():
                    setattr(p, k, v)
            else:
                p = AirdropProject(slug=item["slug"], **fields)
                db.add(p)
                await db.flush()

            existing = list((await db.execute(
                select(AirdropTask).where(AirdropTask.project_id == p.id)
            )).scalars())
            by_title = {t.title: t for t in existing}
            for t in item.get("tasks", []):
                task = by_title.get(t["title"])
                task_fields = dict(
                    title=t["title"], task_type=t.get("task_type", "other"),
                    chain_id=t.get("chain_id"), protocol_address=t.get("protocol_address"),
                    url=t.get("url"), required=t.get("required", True), weight=t.get("weight", 1),
                    status=t.get("status", "active"),
                    notes_json=json.dumps(t.get("notes", {}), ensure_ascii=False),
                )
                if task:
                    for k, v in task_fields.items():
                        setattr(task, k, v)
                else:
                    db.add(AirdropTask(project_id=p.id, **task_fields))
        await db.commit()
    print("airdrop seeds synced")

if __name__ == "__main__":
    asyncio.run(main())
