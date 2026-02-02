from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from fastapi.responses import JSONResponse
from api.router import router as api_router
from contextlib import asynccontextmanager
from core.background_worker import get_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup: Start the background worker
    worker = get_worker()
    worker.start()
    
    yield
    
    # Shutdown: Stop the background worker
    await worker.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS (allow all origins for dev purposes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# Include the API router
app.include_router(api_router)

@app.get("/health")
def health_check():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})




