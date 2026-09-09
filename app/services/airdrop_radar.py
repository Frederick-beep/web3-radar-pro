import json
from datetime import datetime, timezone
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AirdropProject, AirdropTask, AirdropWalletCheck, Transfer, DexSwap


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_address(address: str) -> str:
    if not isinstance(address, str):
        raise ValueError('invalid EVM wallet address')
    address = address.strip().lower()
    if len(address) != 42 or not address.startswith('0x'):
        raise ValueError('invalid EVM wallet address')
    try:
        int(address[2:], 16)
    except ValueError as exc:
        raise ValueError('invalid EVM wallet address') from exc
    return address


def project_dict(p: AirdropProject, tasks=None):
    return {
        'id': p.id,
        'slug': p.slug,
        'name': p.name,
        'chain_id': p.chain_id,
        'status': p.status,
        'potential_score': p.potential_score,
        'risk_score': p.risk_score,
        'risk_level': p.risk_level,
        'official_website': p.official_website,
        'official_claim_url': p.official_claim_url,
        'snapshot_at': p.snapshot_at.isoformat() if p.snapshot_at else None,
        'eligibility_at': p.eligibility_at.isoformat() if p.eligibility_at else None,
        'claim_at': p.claim_at.isoformat() if p.claim_at else None,
        'deadline_at': p.deadline_at.isoformat() if p.deadline_at else None,
        'last_verified_at': p.last_verified_at.isoformat() if p.last_verified_at else None,
        'source_type': p.source_type,
        'notes': json.loads(p.notes_json or '{}'),
        'tasks': [task_dict(t) for t in (tasks or [])],
    }


def task_dict(t: AirdropTask):
    return {
        'id': t.id,
        'project_id': t.project_id,
        'title': t.title,
        'task_type': t.task_type,
        'chain_id': t.chain_id,
        'protocol_address': t.protocol_address,
        'url': t.url,
        'required': t.required,
        'weight': t.weight,
        'status': t.status,
        'notes': json.loads(t.notes_json or '{}'),
    }


async def list_airdrops(db: AsyncSession, status=None, min_score=0, limit=100):
    q = select(AirdropProject).where(AirdropProject.potential_score >= min_score).order_by(desc(AirdropProject.potential_score), desc(AirdropProject.updated_at)).limit(min(limit, 300))
    if status:
        q = q.where(AirdropProject.status == status)
    projects = list((await db.execute(q)).scalars())
    if not projects:
        return []
    ids = [p.id for p in projects]
    tasks = list((await db.execute(select(AirdropTask).where(AirdropTask.project_id.in_(ids), AirdropTask.status == 'active'))).scalars())
    by_project = {}
    for t in tasks:
        by_project.setdefault(t.project_id, []).append(t)
    return [project_dict(p, by_project.get(p.id, [])) for p in projects]


async def airdrop_detail(db: AsyncSession, project_id: int):
    p = (await db.execute(select(AirdropProject).where(AirdropProject.id == project_id))).scalar_one_or_none()
    if not p:
        return None
    tasks = list((await db.execute(select(AirdropTask).where(AirdropTask.project_id == project_id).order_by(AirdropTask.required.desc(), AirdropTask.id))).scalars())
    return project_dict(p, tasks)


async def calendar(db: AsyncSession, limit=100):
    q = select(AirdropProject).where(
        (AirdropProject.snapshot_at.is_not(None)) | (AirdropProject.eligibility_at.is_not(None)) | (AirdropProject.claim_at.is_not(None)) | (AirdropProject.deadline_at.is_not(None))
    ).order_by(AirdropProject.deadline_at.asc().nullslast(), AirdropProject.snapshot_at.asc().nullslast()).limit(min(limit, 300))
    rows = list((await db.execute(q)).scalars())
    out = []
    for p in rows:
        for event_type, dt in [('snapshot', p.snapshot_at), ('eligibility', p.eligibility_at), ('claim', p.claim_at), ('deadline', p.deadline_at)]:
            if dt:
                out.append({'project_id': p.id, 'project': p.name, 'slug': p.slug, 'event': event_type, 'at': dt.isoformat(), 'status': p.status, 'risk_level': p.risk_level})
    return sorted(out, key=lambda x: x['at'])[:limit]


async def check_wallet(db: AsyncSession, address: str, project_id: int | None = None):
    wallet = normalize_address(address)
    if project_id is not None:
        p = (await db.execute(select(AirdropProject).where(AirdropProject.id == project_id))).scalar_one_or_none()
        if p is None:
            raise LookupError('Airdrop project not found')
        projects = [p]
    else:
        projects = list((await db.execute(
            select(AirdropProject).where(
                AirdropProject.status.in_(['active', 'upcoming', 'claim_live'])
            )
        )).scalars())

    # Public on-chain behavior only. This is a heuristic, not proof of eligibility.
    transfers = list((await db.execute(
        select(Transfer)
        .where((Transfer.from_address == wallet) | (Transfer.to_address == wallet))
        .order_by(desc(Transfer.block_number))
        .limit(1000)
    )).scalars())
    swaps = list((await db.execute(
        select(DexSwap)
        .where(DexSwap.sender == wallet)
        .order_by(desc(DexSwap.block_number))
        .limit(1000)
    )).scalars())
    chains = sorted({x.chain_id for x in transfers} | {x.chain_id for x in swaps})
    unique_tokens = len({x.token_address for x in transfers})
    tx_count = len({x.tx_hash for x in transfers} | {x.tx_hash for x in swaps})
    activity_score = min(100, tx_count * 2 + len(chains) * 8 + min(unique_tokens, 20))

    results = []
    for p in projects:
        tasks = list((await db.execute(
            select(AirdropTask)
            .where(AirdropTask.project_id == p.id, AirdropTask.status == 'active')
            .order_by(AirdropTask.required.desc(), AirdropTask.id)
        )).scalars())
        matched = []
        required_total = sum(max(1, t.weight) for t in tasks if t.required)
        required_hit = 0
        for t in tasks:
            hit = False
            reason = 'not enough public evidence'
            target_chain = t.chain_id
            if target_chain is not None and target_chain not in chains:
                reason = 'no activity found on target chain'
            elif target_chain is not None and target_chain in chains:
                reason = 'wallet has activity on target chain'
                # Chain presence alone is weak evidence; do not mark a protocol task as complete.
                hit = t.protocol_address is None

            if t.protocol_address:
                pa = t.protocol_address.lower()
                transfer_hit = any(
                    x.chain_id == target_chain and (x.from_address == pa or x.to_address == pa)
                    for x in transfers
                ) if target_chain is not None else any(
                    x.from_address == pa or x.to_address == pa for x in transfers
                )
                swap_hit = any(
                    x.chain_id == target_chain and x.pair_address.lower() == pa
                    for x in swaps
                ) if target_chain is not None else any(
                    x.pair_address.lower() == pa for x in swaps
                )
                if transfer_hit or swap_hit:
                    hit = True
                    reason = 'wallet interacted with task protocol address'

            if hit and t.required:
                required_hit += max(1, t.weight)
            matched.append({
                'task_id': t.id, 'title': t.title, 'required': t.required,
                'matched': hit, 'reason': reason
            })

        coverage = round((required_hit / required_total) * 100, 2) if required_total else activity_score
        confidence = min(100, round(coverage * 0.75 + activity_score * 0.25))
        label = 'likely' if confidence >= 75 else 'possible' if confidence >= 40 else 'unlikely'
        result = {
            'project_id': p.id, 'project': p.name, 'wallet': wallet, 'eligibility': label,
            'confidence': confidence, 'task_coverage': coverage, 'activity_score': activity_score,
            'tx_count': tx_count, 'unique_tokens': unique_tokens, 'chains_active': chains,
            'matched_tasks': matched,
            'warning': 'Heuristic only. Official eligibility must be confirmed by the project claim/eligibility page.'
        }
        results.append(result)
        row = (await db.execute(select(AirdropWalletCheck).where(
            AirdropWalletCheck.project_id == p.id,
            AirdropWalletCheck.wallet_address == wallet
        ))).scalar_one_or_none()
        payload = json.dumps(result, ensure_ascii=False)
        if row:
            row.confidence = confidence
            row.eligibility = label
            row.activity_score = activity_score
            row.task_coverage = coverage
            row.details_json = payload
            row.checked_at = _now()
        else:
            db.add(AirdropWalletCheck(
                project_id=p.id, wallet_address=wallet, confidence=confidence,
                eligibility=label, activity_score=activity_score, task_coverage=coverage,
                details_json=payload
            ))
    await db.commit()
    return results
