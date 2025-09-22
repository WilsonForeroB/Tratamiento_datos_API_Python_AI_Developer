from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship


DB_URL = "sqlite:///mi_base.db" # archivo en la raíz del proyecto
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# app/models.py
from sqlalchemy import Column, Integer, Float, DateTime, String
from sqlalchemy.sql import func
from .db import Base


class Sales(Base):
    __tablename__ = "sales"


    id = Column(Integer, primary_key=True, index=True)
    numero_ventas = Column(Integer, nullable=False)
    facturacion = Column(Float, nullable=False)
    presupuesto = Column(Float, nullable=False)
    
    clientes_vendidos = Column(Integer, nullable=False)

    ticket_medio = Column(Float)
    margen = Column(Float)
    ratio_clientes_por_venta = Column(Float)
    cumplimiento_presupuesto = Column(Float)


    created_at = Column(DateTime(timezone=True), server_default=func.now())



class User(Base):
    __tablename__ = "users"
    id   = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    id      = Column(Integer, primary_key=True)
    title   = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    author = relationship("User", back_populates="posts")

# Útil para Alembic:
metadata = Base.metadata