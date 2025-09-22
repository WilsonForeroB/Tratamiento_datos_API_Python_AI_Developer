import io
import math
import numpy as np
import pandas as pd
from typing import Iterable
from .db import engine


REQUIRED_COLS = [
    "numero_ventas",
    "facturacion",
    "presupuesto",
    "clientes_vendidos",
    ]

def ensure_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in REQUIRED_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        return df




def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df["ticket_medio"] = np.where(df["numero_ventas"] > 0, df["facturacion"] / df["numero_ventas"], np.nan)
    df["margen"] = df["facturacion"] - df["presupuesto"]
    df["ratio_clientes_por_venta"] = np.where(df["numero_ventas"] > 0, df["clientes_vendidos"] / df["numero_ventas"], np.nan)
    df["cumplimiento_presupuesto"] = np.where(df["presupuesto"] != 0, df["facturacion"] / df["presupuesto"], np.nan)
    return df




def df_from_db() -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql_table("sales", conn)




def dataframe_to_csv_response(df: pd.DataFrame) -> io.StringIO:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf