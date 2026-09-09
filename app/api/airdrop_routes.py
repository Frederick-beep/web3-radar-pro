from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.config import settings
from app.services.airdrop_radar import list_airdrops, airdrop_detail, calendar, check_wallet

router = APIRouter(prefix='/api/v2/airdrops', tags=['Airdrop Radar'])

async def auth(x_api_key: str | None = Header(default=None)):
    if x_api_key in settings.api_key_set:
        return x_api_key
    raise HTTPException(401, 'Invalid API key')

class WalletCheckRequest(BaseModel):
    address: str = Field(min_length=42, max_length=42)
    project_id: int | None = None

@router.get('')
async def airdrops(status: str | None = None, min_score: int = Query(0, ge=0, le=100), limit: int = Query(100, ge=1, le=300), db: AsyncSession = Depends(get_db), _: str = Depends(auth)):
    return await list_airdrops(db, status=status, min_score=min_score, limit=limit)

@router.get('/calendar')
async def airdrop_calendar(limit: int = Query(100, ge=1, le=300), db: AsyncSession = Depends(get_db), _: str = Depends(auth)):
    return await calendar(db, limit)

@router.post('/check-wallet')
async def wallet_check(body: WalletCheckRequest, db: AsyncSession = Depends(get_db), _: str = Depends(auth)):
    try:
        return await check_wallet(db, body.address, body.project_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except LookupError as e:
        raise HTTPException(404, str(e))

@router.get('/wallet/{address}')
async def wallet_history(address: str, project_id: int | None = None, db: AsyncSession = Depends(get_db), _: str = Depends(auth)):
    try:
        return await check_wallet(db, address, project_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except LookupError as e:
        raise HTTPException(404, str(e))

@router.get('/{project_id}')
async def airdrop(project_id: int, db: AsyncSession = Depends(get_db), _: str = Depends(auth)):
    row = await airdrop_detail(db, project_id)
    if row is None:
        raise HTTPException(404, 'Airdrop project not found')
    return row
