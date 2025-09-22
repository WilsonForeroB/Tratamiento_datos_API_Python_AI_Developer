from pydantic import BaseModel
from typing import Optional, List


class SalesBase(BaseModel):
    numero_ventas: int
    facturacion: float
    presupuesto: float
    clientes_vendidos: int


class SalesCreate(SalesBase):
    pass


class SalesRead(SalesBase):
    id: int
    ticket_medio: Optional[float] = None
    margen: Optional[float] = None
    ratio_clientes_por_venta: Optional[float] = None
    cumplimiento_presupuesto: Optional[float] = None


class Config:
    from_attributes = True


class IngestSummary(BaseModel):
    filas_insertadas: int
    totales: dict
    medias: dict