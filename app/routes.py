from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
import io
import math
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


from sqlalchemy.orm import Session
from .db import SessionLocal, engine
from .models import Sales
from . import services as svc


router = APIRouter(prefix="", tags=["analytics"])




# Helpers FastAPI
async def _read_upload(file: UploadFile) -> pd.DataFrame:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Sube un archivo .csv")
    content = await file.read()
    try:
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV inválido: {e}")
    return df




@router.get("/generate-csv", response_class=StreamingResponse)
def generate_csv(rows: int = Query(100, ge=1, le=100000), seed: int | None = None):
    rng = np.random.default_rng(seed)
    numero_ventas = rng.integers(5, 200, size=rows)
    facturacion = rng.uniform(1_000, 100_000, size=rows)
    presupuesto = facturacion * rng.uniform(0.6, 1.2, size=rows)
    clientes_vendidos = np.maximum(1, (numero_ventas * rng.uniform(0.6, 1.0, size=rows))).astype(int)


    df = pd.DataFrame({
        "numero_ventas": numero_ventas,
        "facturacion": facturacion.round(2),
        "presupuesto": presupuesto.round(2),
        "clientes_vendidos": clientes_vendidos,
        })


    buf = svc.dataframe_to_csv_response(df)
    headers = {"Content-Disposition": "attachment; filename=datos_sinteticos.csv"}

    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers=headers)


@router.post("/ingest-csv")
async def ingest_csv(file: UploadFile = File(...)):
    df = await _read_upload(file)


    missing = [c for c in svc.REQUIRED_COLS if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Faltan columnas: {missing}. Se requieren: {svc.REQUIRED_COLS}")


    df = df[svc.REQUIRED_COLS].copy()
    df = svc.ensure_numeric(df)
    df = df.dropna(subset=svc.REQUIRED_COLS).reset_index(drop=True)
    df = svc.compute_metrics(df)


    records = df.to_dict(orient="records")

    with SessionLocal() as db:
        objs = [
        Sales(**{
            "numero_ventas": int(r["numero_ventas"]),
            "facturacion": float(r["facturacion"]),
            "presupuesto": float(r["presupuesto"]),
            "clientes_vendidos": int(r["clientes_vendidos"]),
            "ticket_medio": None if pd.isna(r["ticket_medio"]) else float(r["ticket_medio"]),
            "margen": None if pd.isna(r["margen"]) else float(r["margen"]),
            "ratio_clientes_por_venta": None if pd.isna(r["ratio_clientes_por_venta"]) else float(r["ratio_clientes_por_venta"]),
            "cumplimiento_presupuesto": None if pd.isna(r["cumplimiento_presupuesto"]) else float(r["cumplimiento_presupuesto"])
        }) for r in records
    ]
    db.add_all(objs)
    db.commit()

    summary = {
        "filas_insertadas": len(records),
        "totales": {c: float(df[c].sum()) for c in ["numero_ventas","facturacion","presupuesto","clientes_vendidos"]},
        "medias": {
        "ticket_medio": float(df["ticket_medio"].mean(skipna=True)) if not math.isnan(df["ticket_medio"].mean(skipna=True)) else None,
        "margen": float(df["margen"].mean(skipna=True)) if not math.isnan(df["margen"].mean(skipna=True)) else None,
        "ratio_clientes_por_venta": float(df["ratio_clientes_por_venta"].mean(skipna=True)) if not math.isnan(df["ratio_clientes_por_venta"].mean(skipna=True)) else None,
        "cumplimiento_presupuesto": float(df["cumplimiento_presupuesto"].mean(skipna=True)) if not math.isnan(df["cumplimiento_presupuesto"].mean(skipna=True)) else None,
        },
    }

    return JSONResponse(summary)


@router.get("/devuelvegrafica/{kind}", response_class=StreamingResponse, include_in_schema=True)
def devuelvegrafica(kind: str):
    valid = {"facturacion_vs_presupuesto", "ventas", "clientes_vs_ventas"}

    if kind not in valid:
        raise HTTPException(status_code=400, detail=f"kind debe ser uno de {sorted(valid)}")


    try:
        df = svc.df_from_db()
    except ValueError:
        raise HTTPException(status_code=404, detail="No hay datos en 'sales'. Ingiere primero un CSV.")
    if df.empty:
        raise HTTPException(status_code=404, detail="La tabla 'sales' está vacía.")


    fig, ax = plt.subplots(figsize=(8,5))
    if kind == "facturacion_vs_presupuesto":
        ax.plot(df.index, df["facturacion"], label="Facturación")
        ax.plot(df.index, df["presupuesto"], label="Presupuesto")
        ax.set_title("Facturación vs Presupuesto")
        ax.set_xlabel("Registro"); ax.set_ylabel("Euros"); ax.legend()
    elif kind == "ventas":
        ax.bar(df.index, df["numero_ventas"])
        ax.set_title("Número de ventas por registro")
        ax.set_xlabel("Registro"); ax.set_ylabel("Número de ventas")
    elif kind == "clientes_vs_ventas":
        ax.scatter(df["numero_ventas"], df["clientes_vendidos"])
        ax.set_title("Clientes vendidos vs Número de ventas")
        ax.set_xlabel("Número de ventas"); ax.set_ylabel("Clientes vendidos")


    import io as _io
    buf = _io.BytesIO()
    fig.tight_layout(); fig.savefig(buf, format="png"); plt.close(fig); buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")

@router.get("/data")
def data_preview():
    with engine.connect() as conn:
        try:
            df = pd.read_sql_query("SELECT * FROM sales ORDER BY id DESC LIMIT 1000", conn)
        except Exception:
            raise HTTPException(status_code=404, detail="No hay datos aún.")
        return JSONResponse(df.to_dict(orient="records"))

