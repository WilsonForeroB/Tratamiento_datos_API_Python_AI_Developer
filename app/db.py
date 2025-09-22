from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Usa tu fichero real. Relativo a la RAÍZ del proyecto.
DB_URL = "sqlite:///mi_base.db"

# Para SQLite + FastAPI (evita error de threads)
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()