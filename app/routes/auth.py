from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import bcrypt

from app.database.config import get_db
from app.database import models

router = APIRouter(prefix="/auth", tags=["Autenticação"])

class UserRegister(BaseModel):
    nome: str
    email: EmailStr
    senha: str


class UserLogin(BaseModel):
    email: EmailStr
    senha: str


def gerar_senha_hash(senha: str) -> str:
    senha_bytes = senha.encode('utf-8')
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(senha_bytes, salt)
    return hash_bytes.decode('utf-8')


def verificar_senha(senha_pura: str, senha_criptografada: str) -> bool:
    try:
        senha_pura_bytes = senha_pura.encode('utf-8')
        senha_hash_bytes = senha_criptografada.encode('utf-8')
        return bcrypt.checkpw(senha_pura_bytes, senha_hash_bytes)
    except Exception:
        return False


# --- ROTAS DA API ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(usuario: UserRegister, db: Session = Depends(get_db)):
    usuario_existente = db.query(models.User).filter(models.User.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este e-mail já está cadastrado no BookLens."
        )

    senha_segura = gerar_senha_hash(usuario.senha)

    novo_usuario = models.User(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=senha_segura
    )

    try:
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)

        return {
            "sucesso": True,
            "message": "Usuário registrado com sucesso!",
            "usuario": {
                "id": novo_usuario.id,
                "nome": novo_usuario.nome,
                "email": novo_usuario.email
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar o usuário no banco: {str(e)}"
        )


@router.post("/login")
async def login(credenciais: UserLogin, db: Session = Depends(get_db)):
    usuario = db.query(models.User).filter(models.User.email == credenciais.email).first()

    if not usuario or not verificar_senha(credenciais.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos."
        )

    return {
        "sucesso": True,
        "message": f"Bem-vindo de volta, {usuario.nome}!",
        "usuario": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email
        }
    }