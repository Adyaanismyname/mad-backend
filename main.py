from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from fastapi.responses import JSONResponse
from api.router import router as api_router


app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the API router
app.include_router(api_router)

@app.get("/health")
def health_check():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})




