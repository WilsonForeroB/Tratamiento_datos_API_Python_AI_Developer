from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import Base, engine
from app.routes import router as analytics_router
from app.routes_calculos import router as route_calculos

app = FastAPI(title="API CSV / SQLite", version="1.0.0")


app.add_middleware(
CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(engine) # asegura la tabla


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(analytics_router)


app.include_router(route_calculos)