# Web3 Radar Pro FINAL 5.1

## BSC New Token Radar — production-oriented foundation

This release is intentionally BSC-first. Ethereum/Base remain available as general ingestion chains, while the premium product path centers on **BSC new-token discovery, DEX activity, anomaly scoring, and contract-risk filtering**.

### Core pipeline

BSC -> PancakeSwap V2 PairCreated -> new WBNB pair -> Swap direction -> buyer/seller breadth -> liquidity/volume -> contract-risk scan -> anomaly/risk score -> HOT/WATCH/FILTER -> Telegram/API.

### Included
- Ethereum / Base / BSC collectors
- BSC PancakeSwap V2 pair discovery
- ERC-20 Transfer ingestion
- Swap parsing and buy/sell direction
- Buyer/seller breadth
- Smart-money and wallet intelligence foundation
- Contract bytecode risk heuristics
- Token price/liquidity/volume adapter
- Redis Streams + PostgreSQL + async SQLAlchemy
- FastAPI v1 + v2 BSC-first endpoints
- Docker Compose
- GitHub Actions CI
- Telegram alerts
- Unit tests

### Important accuracy boundary
The local contract scanner is a **heuristic risk detector**, not a formal audit. Buy/sell tax and honeypot behavior require an execution-simulation or trusted external security provider; this release does not pretend a static opcode scan proves that a token is safe or sellable. Do not treat Alpha/Risk scores as investment advice.

### Run

```bash
cp .env.example .env
# fill BSC_RPC_URL

docker compose up -d --build
```

Open `/docs` and use `X-API-Key: demo-key` (change this before production).

### BSC endpoints
- `GET /api/v2/bsc/launches`
- `GET /api/v2/bsc/hot`
- `GET /api/v2/bsc/overview`
- `GET /api/v2/bsc/risk/{token}`

### Production checklist
- Replace demo API key with hashed keys and per-plan quotas.
- Use Alembic migrations.
- Add a trusted honeypot/tax simulation provider.
- Persist block timestamps and reorg-safe cursors.
- Add websocket/SSE dashboard updates.
- Backtest every alert against 1m/5m/15m/1h/6h/24h outcomes before marketing performance claims.


## 🎁 Airdrop Radar

5.1 restores Airdrop Radar as a first-class module. It is deliberately separated from the BSC new-token engine:

- curated airdrop/project discovery with verified-source fields
- task tracking: protocol interaction, chain activity and custom task types
- Airdrop Calendar: Snapshot / Eligibility / Claim / Deadline
- public-address wallet eligibility heuristic; no private keys and no signing
- `likely / possible / unlikely` confidence instead of claiming guaranteed eligibility
- risk fields for official website / claim URL / project risk
- Telegram lifecycle alert worker

### Airdrop API

- `GET /api/v2/airdrops`
- `GET /api/v2/airdrops/{project_id}`
- `GET /api/v2/airdrops/calendar`
- `POST /api/v2/airdrops/check-wallet`
- `GET /api/v2/airdrops/wallet/{address}`

The initial data source is `config/airdrops.yaml`. This avoids inventing live airdrops. Replace the demo seed with verified official projects, contracts and dates. The wallet checker analyzes only public on-chain history already indexed by Radar and is not an official eligibility oracle.

## 🖥️ Web SaaS UI (5.3)

The project now includes a production-oriented single-origin SaaS dashboard under `frontend/`, served directly by FastAPI.

- `/app` — Web SaaS dashboard
- `/frontend/*` — static UI assets
- Dashboard, BSC New Token Radar, Airdrop Radar, Smart Money, Whale Radar, Token Intelligence, DEX Radar and Alpha Alerts
- Uses the existing FastAPI endpoints with `X-API-Key`
- API key is stored only in browser localStorage when changed in Settings; do not put secrets into source control
- Airdrop wallet analysis is clearly presented as heuristic, not official eligibility

For a separate frontend deployment, the `frontend/` directory can also be served by any static web server. Set the API base URL in `frontend/app.js` via `state.base` if frontend and API are hosted on different origins.
