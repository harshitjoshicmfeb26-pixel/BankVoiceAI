from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db
from routes import router

# Lifespan context manager to handle startup/shutdown tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database & seed if necessary
    init_db()
    yield

# FastAPI initialization
app = FastAPI(title="Voice Banking Assistant API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(router)

# Mount static folder for HTML/JS frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
