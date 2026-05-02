from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from fastapi.responses import JSONResponse
from api.router import router as api_router
import logging

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Override any existing config
)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
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




