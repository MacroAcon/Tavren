from fastapi import FastAPI
from app.routers.static import static_router

app = FastAPI()

app.include_router(static_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 