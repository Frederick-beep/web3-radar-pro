from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router
from app.api.final_routes import router as final_router
from app.api.airdrop_routes import router as airdrop_router

APP_VERSION = "5.3.0"

app = FastAPI(
    title="Web3 Radar Pro",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)
app.include_router(router)
app.include_router(final_router)
app.include_router(airdrop_router)

# Production SaaS frontend: static SPA served by the same FastAPI origin.
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/app")
async def app_ui():
    return FileResponse("frontend/index.html")

@app.get("/")
async def root():
    return {
        "name": "Web3 Radar Pro",
        "version": APP_VERSION,
        "modules": [
            "bsc_new_token_radar", "airdrop_radar", "smart_money",
            "whale_radar", "token_radar", "dex_radar", "alpha_alert"
        ],
        "chains": [1, 8453, 56],
    }

@app.get("/health")
async def health():
    return {"status": "ok", "version": APP_VERSION, "focus": "bsc_new_token_radar", "airdrop_radar": True}
