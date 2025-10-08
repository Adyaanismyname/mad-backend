from fastapi import FastAPI, status
from core.config import settings
from fastapi.responses import JSONResponse


app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

@app.get("/health")
def health_check():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})




