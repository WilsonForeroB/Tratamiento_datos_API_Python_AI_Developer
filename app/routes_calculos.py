
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
import numpy as np
import torch

router = APIRouter(prefix="/Calc", tags=["Calc"]) 


MAX_ELEMS = 200_000 # para evitar cargas gigantes


class NumpyRequest(BaseModel):
    op: Literal['dot','matmul','add','sub','mean','std']
    a: List[float] | List[List[float]]
    b: Optional[List[float] | List[List[float]]] = None
    axis: Optional[int] = None

@router.post("/numpy")
def numpy_compute(req: NumpyRequest):
    import numpy as _np

    try:
        a = _np.array(req.a, dtype=float)
        b = None if req.b is None else _np.array(req.b, dtype=float)
        elems = a.size + (0 if b is None else b.size)

        if elems > MAX_ELEMS:
            raise HTTPException(status_code=413, detail="Demasiados elementos para procesar")
        if req.op == 'dot':

            if b is None:
                raise HTTPException(400, detail="'dot' requiere 'b'")
            if a.ndim != 1 or b.ndim != 1:
                raise HTTPException(400, detail="'dot' requiere vectores 1D")
            res = _np.dot(a, b)
        elif req.op == 'matmul':
            if b is None:
                raise HTTPException(400, detail="'matmul' requiere 'b'")
            res = _np.matmul(a, b)

        elif req.op == 'add':
            if b is None:
                raise HTTPException(400, detail="'add' requiere 'b'")
            res = _np.add(a, b)
        elif req.op == 'sub':
                if b is None:
                    raise HTTPException(400, detail="'sub' requiere 'b'")
                res = _np.subtract(a, b)
        elif req.op == 'mean':
                res = _np.mean(a, axis=req.axis)
        elif req.op == 'std':
                res = _np.std(a, axis=req.axis)
        else:
            raise HTTPException(400, detail="Operación no soportada")
        if isinstance(res, _np.ndarray):
            return {"result": res.tolist(), "shape": list(res.shape)}
        else:
            return {"result": float(res), "shape": []}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=f"Error Numpy: {e}")


class TorchRequest(BaseModel):
    op: Literal['matmul','add','relu','softmax','linear']
    a: List[float] | List[List[float]]
    b: Optional[List[float] | List[List[float]]] = None
    weight: Optional[List[List[float]]] = None
    bias: Optional[List[float]] = None
    device: Literal['auto','cpu','cuda'] = 'auto'


@router.get("/torch/device")
def torch_device():
    return {"cuda_available": torch.cuda.is_available()}


@router.post("/torch")
def torch_compute(req: TorchRequest):
    dev = 'cuda' if (req.device in ('auto','cuda') and torch.cuda.is_available()) else 'cpu'
    try:
        a = torch.tensor(req.a, dtype=torch.float32, device=dev)
        b = None if req.b is None else torch.tensor(req.b, dtype=torch.float32, device=dev)
        elems = a.numel() + (0 if b is None else b.numel())
        if elems > MAX_ELEMS:
            raise HTTPException(status_code=413, detail="Demasiados elementos para procesar")
        if req.op == 'matmul':
            if b is None:
                raise HTTPException(400, detail="'matmul' requiere 'b'")
                out = torch.matmul(a, b)
            elif req.op == 'add':
                if b is None:
                        raise HTTPException(400, detail="'add' requiere 'b'")
                out = a + b
            elif req.op == 'relu':
                out = torch.relu(a)
            elif req.op == 'softmax':
                out = torch.softmax(a, dim=-1)
            elif req.op == 'linear':
                if req.weight is None:
                    raise HTTPException(400, detail="'linear' requiere 'weight' (matriz [out,in])")
                W = torch.tensor(req.weight, dtype=torch.float32, device=dev)
                bias = None if req.bias is None else torch.tensor(req.bias, dtype=torch.float32, device=dev)
                out = torch.nn.functional.linear(a, W, bias)
            else:
                raise HTTPException(400, detail="Operación no soportada")
            return {"device": dev, "result": out.detach().cpu().tolist(), "shape": list(out.shape), "dtype": str(out.dtype)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=f"Error Torch: {e}")
    



class VectorPair(BaseModel):
    a: List[float]
    b: List[float]


@router.post("/vectors/sum")
def vector_sum(v: VectorPair):

    a = np.asarray(v.a, dtype=float).ravel()
    b = np.asarray(v.b, dtype=float).ravel()

    if a.size + b.size > MAX_ELEMS:
        raise HTTPException(status_code=413, detail="Demasiados elementos para procesar")
    if a.shape != b.shape:
        raise HTTPException(status_code=400, detail=f"Dimensiones incompatibles: {a.shape} vs {b.shape}")
    s = a + b

    return {"result": s.tolist(), "length": int(s.size)}


@router.post("/vectors/similitud")
def vector_similarity(v: VectorPair):

   # [1, 2, 3] = array([1., 2., 3.])
   # [[1, 2, 3]] = array([1., 2., 3.])
   # [[1],[2],[3]] = array([1., 2., 3.])

    a = np.asarray(v.a, dtype=float).ravel()
    b = np.asarray(v.b, dtype=float).ravel()

    if a.size + b.size > MAX_ELEMS:
        raise HTTPException(status_code=413, detail="Demasiados elementos para procesar")
    
    if a.shape != b.shape:
        raise HTTPException(status_code=400, detail=f"Dimensiones incompatibles: {a.shape} vs {b.shape}")
    
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)

    if na == 0 or nb == 0:
        raise HTTPException(status_code=400, detail="No se puede calcular similitud con vector nulo")
    
    dot = float(np.dot(a, b))
    cos = float(dot / (na * nb)) # SIMILITUD DEL COSENO

    return {"coseno": cos, "dot": dot, "norm_a": float(na), "norm_b": float(nb)}