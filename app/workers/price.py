import asyncio
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Token
from app.services.price import PriceService
async def main():
    svc=PriceService()
    while True:
        async with SessionLocal() as db:
            tokens=(await db.execute(select(Token).order_by(Token.updated_at.desc()).limit(200))).scalars().all()
            for t in tokens:
                d=await svc.token(t.chain_id,t.address)
                if d:
                    t.price_usd=d["price_usd"];t.liquidity_usd=d["liquidity_usd"];t.volume_24h_usd=d["volume_24h_usd"]
            await db.commit()
        await asyncio.sleep(30)
if __name__=="__main__":asyncio.run(main())
