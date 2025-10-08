from fastapi import FastAPI, status
from core.config import settings
from fastapi.responses import JSONResponse
from api.router import router as api_router


app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

# Include the API router
app.include_router(api_router)

@app.get("/health")
def health_check():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})




