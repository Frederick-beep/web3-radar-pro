from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Numeric, DateTime, Boolean, Text, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass

class ChainState(Base):
    __tablename__ = "chain_states"
    chain_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_block: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Token(Base):
    __tablename__ = "tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_id: Mapped[int] = mapped_column(Integer, index=True)
    address: Mapped[str] = mapped_column(String(42), index=True)
    symbol: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str | None] = mapped_column(String(128))
    decimals: Mapped[int | None] = mapped_column(Integer)
    price_usd: Mapped[float] = mapped_column(Numeric(30, 10), default=0)
    liquidity_usd: Mapped[float] = mapped_column(Numeric(30, 2), default=0)
    volume_24h_usd: Mapped[float] = mapped_column(Numeric(30, 2), default=0)
    first_seen_block: Mapped[int] = mapped_column(BigInteger)
    last_seen_block: Mapped[int] = mapped_column(BigInteger)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("chain_id", "address", name="uq_token_chain_address"),)

class Transfer(Base):
    __tablename__ = "transfers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_id: Mapped[int] = mapped_column(Integer, index=True)
    block_number: Mapped[int] = mapped_column(BigInteger, index=True)
    tx_hash: Mapped[str] = mapped_column(String(66))
    log_index: Mapped[int] = mapped_column(Integer)
    token_address: Mapped[str] = mapped_column(String(42), index=True)
    from_address: Mapped[str] = mapped_column(String(42), index=True)
    to_address: Mapped[str] = mapped_column(String(42), index=True)
    amount_raw: Mapped[int] = mapped_column(Numeric(78, 0))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("chain_id", "tx_hash", "log_index", name="uq_transfer"), Index("ix_transfer_token_block", "token_address", "block_number"))

class Wallet(Base):
    __tablename__ = "wallets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_id: Mapped[int] = mapped_column(Integer, index=True)
    address: Mapped[str] = mapped_column(String(42), index=True)
    transfer_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_tokens: Mapped[int] = mapped_column(Integer, default=0)
    inbound_count: Mapped[int] = mapped_column(Integer, default=0)
    outbound_count: Mapped[int] = mapped_column(Integer, default=0)
    whale_events: Mapped[int] = mapped_column(Integer, default=0)
    smart_money_score: Mapped[int] = mapped_column(Integer, default=0)
    is_smart_money: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    last_activity_block: Mapped[int] = mapped_column(BigInteger, default=0)
    __table_args__ = (UniqueConstraint("chain_id", "address", name="uq_wallet_chain_address"),)

class WalletToken(Base):
    __tablename__ = "wallet_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_id: Mapped[int] = mapped_column(Integer)
    wallet_address: Mapped[str] = mapped_column(String(42), index=True)
    token_address: Mapped[str] = mapped_column(String(42), index=True)
    inbound_raw: Mapped[int] = mapped_column(Numeric(78, 0), default=0)
    outbound_raw: Mapped[int] = mapped_column(Numeric(78, 0), default=0)
    transfers: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (UniqueConstraint("chain_id", "wallet_address", "token_address", name="uq_wallet_token"),)

class DexPool(Base):
    __tablename__ = "dex_pools"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_id: Mapped[int] = mapped_column(Integer, index=True)
    factory: Mapped[str] = mapped_column(String(42))
    dex_name: Mapped[str] = mapped_column(String(64))
    pair_address: Mapped[str] = mapped_column(String(42), index=True)
    token0: Mapped[str] = mapped_column(String(42))
    token1: Mapped[str] = mapped_column(String(42))
    created_block: Mapped[int] = mapped_column(BigInteger)
    __table_args__ = (UniqueConstraint("chain_id", "pair_address", name="uq_pool"),)

class DexSwap(Base):
    __tablename__ = "dex_swaps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_id: Mapped[int] = mapped_column(Integer, index=True)
    pair_address: Mapped[str] = mapped_column(String(42), index=True)
    tx_hash: Mapped[str] = mapped_column(String(66))
    log_index: Mapped[int] = mapped_column(Integer)
    sender: Mapped[str] = mapped_column(String(42), index=True)
    amount0_in: Mapped[int] = mapped_column(Numeric(78, 0))
    amount1_in: Mapped[int] = mapped_column(Numeric(78, 0))
    amount0_out: Mapped[int] = mapped_column(Numeric(78, 0))
    amount1_out: Mapped[int] = mapped_column(Numeric(78, 0))
    block_number: Mapped[int] = mapped_column(BigInteger, index=True)
    __table_args__ = (UniqueConstraint("chain_id", "tx_hash", "log_index", name="uq_swap"),)

class Signal(Base):
    __tablename__ = "signals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_id: Mapped[int] = mapped_column(Integer, index=True)
    signal_type: Mapped[str] = mapped_column(String(64), index=True)
    token_address: Mapped[str | None] = mapped_column(String(42), index=True)
    wallet_address: Mapped[str | None] = mapped_column(String(42), index=True)
    score: Mapped[int] = mapped_column(Integer, index=True)
    reason: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key_hash: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    plan: Mapped[str] = mapped_column(String(32), default="free")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ContractScan(Base):
    __tablename__ = "contract_scans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_id: Mapped[int] = mapped_column(Integer, index=True)
    token_address: Mapped[str] = mapped_column(String(42), index=True)
    owner_address: Mapped[str | None] = mapped_column(String(42))
    mint_capable_hint: Mapped[bool] = mapped_column(Boolean, default=False)
    pause_capable_hint: Mapped[bool] = mapped_column(Boolean, default=False)
    blacklist_hint: Mapped[bool] = mapped_column(Boolean, default=False)
    proxy_hint: Mapped[bool] = mapped_column(Boolean, default=False)
    delegatecall_hint: Mapped[bool] = mapped_column(Boolean, default=False)
    selfdestruct_hint: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_score: Mapped[int] = mapped_column(Integer, index=True, default=0)
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    notes_json: Mapped[str] = mapped_column(Text, default="[]")
    scanned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (UniqueConstraint("chain_id", "token_address", name="uq_contract_scan"),)

class AirdropProject(Base):
    __tablename__ = "airdrop_projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(96), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    chain_id: Mapped[int] = mapped_column(Integer, index=True, default=56)
    status: Mapped[str] = mapped_column(String(32), index=True, default="upcoming")
    potential_score: Mapped[int] = mapped_column(Integer, index=True, default=0)
    risk_score: Mapped[int] = mapped_column(Integer, index=True, default=0)
    risk_level: Mapped[str] = mapped_column(String(16), default="unknown")
    official_website: Mapped[str | None] = mapped_column(String(512))
    official_claim_url: Mapped[str | None] = mapped_column(String(512))
    snapshot_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    eligibility_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    claim_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    source_type: Mapped[str] = mapped_column(String(32), default="curated")
    notes_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AirdropTask(Base):
    __tablename__ = "airdrop_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(256))
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    chain_id: Mapped[int | None] = mapped_column(Integer, index=True)
    protocol_address: Mapped[str | None] = mapped_column(String(42), index=True)
    url: Mapped[str | None] = mapped_column(String(512))
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    weight: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    notes_json: Mapped[str] = mapped_column(Text, default="{}")

class AirdropWalletCheck(Base):
    __tablename__ = "airdrop_wallet_checks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    wallet_address: Mapped[str] = mapped_column(String(42), index=True)
    confidence: Mapped[int] = mapped_column(Integer, index=True, default=0)
    eligibility: Mapped[str] = mapped_column(String(24), index=True, default="unknown")
    activity_score: Mapped[int] = mapped_column(Integer, default=0)
    task_coverage: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (UniqueConstraint("project_id", "wallet_address", name="uq_airdrop_wallet_project"),)
