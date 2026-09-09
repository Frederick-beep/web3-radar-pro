import asyncio, json
from datetime import datetime
from sqlalchemy import select
from app.database import SessionLocal
from app.models import AirdropProject
from app.services.alerts import send_telegram

async def run():
    while True:
        async with SessionLocal() as db:
            rows = list((await db.execute(select(AirdropProject).where(AirdropProject.status.in_(['claim_live','upcoming','active'])))).scalars())
            now = datetime.utcnow()
            for p in rows:
                changed = False
                if p.deadline_at and p.deadline_at <= now and p.status == 'claim_live':
                    p.status = 'expired'; changed = True
                if changed:
                    await send_telegram(f'🎁 AIRDROP UPDATE\nProject: {p.name}\nStatus: {p.status}\nRisk: {p.risk_level}')
            await db.commit()
        await asyncio.sleep(60)

if __name__ == '__main__': asyncio.run(run())
