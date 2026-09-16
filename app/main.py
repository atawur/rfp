import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
import app.db.base  # Register all SQLAlchemy models
from app.api.routes import auth, users, websites, rfps, agent_configs, notification_receivers
from app.core.scheduler import start_scheduler, shutdown_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(websites.router, prefix="/websites", tags=["websites"])
api_router.include_router(rfps.router, prefix="/rfps", tags=["rfps"])
api_router.include_router(agent_configs.router, prefix="/agent-configs", tags=["agent-configs"])
api_router.include_router(
    notification_receivers.router,
    prefix="/notification-receivers",
    tags=["notification-receivers"],
)


app.include_router(api_router, prefix=settings.API_V1_STR)
