#---------------------------------------------------------------------------------------------------
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app_hola_mundo = FastAPI()

# --- Configuración JWT ---
SECRET_KEY = "clave_super_secreta_que_deberias_cambiar"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


Demo_user = {
    "username": "demo",
    "password": "demo123"
}

class credenciales(BaseModel):
    user: str
    password: str
    


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    

@app_hola_mundo.post("/token")
async def login(form_data: credenciales = Depends()):
    if form_data.user == Demo_user["username"] and form_data.password == Demo_user["password"]:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            data={"sub": form_data.user}, 
            expires_delta=access_token_expires
        )
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")



@app_hola_mundo.get("/saludo-seguro")
async def saludo_seguro(token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    return {"mensaje": f"Hola {username}, accediste con JWT"}


#---------------------------------------------------------------------------------------------------


@app_hola_mundo.get("/")
def read_root():
    return {"mensaje": "Hola, FastAPI!"}

@app_hola_mundo.get("/saludo/{nombre}")
def read_item(nombre: str):
    return {"mensaje": f"Hola, {nombre}"}

@app_hola_mundo.get("/devuelveVariable/{var1}")
def devuelveVariable (variable: int ):
    return variable * 7