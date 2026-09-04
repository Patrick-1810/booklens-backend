from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt

from app.database.config import get_db
from app.database import models
from app.core.schemas import UserRegister, UserLogin, RefreshTokenRequest
from app.core.security import (
    criar_access_token,
    criar_refresh_token,
    verificar_refresh_token,
    obter_usuario_atual,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


# --- FUNÇÕES AUXILIARES ---

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


def _gerar_tokens(usuario: models.User) -> dict:
    """Gera o par access_token + refresh_token para um usuário."""
    token_data = {"sub": usuario.email, "user_id": usuario.id}
    access_token = criar_access_token(token_data)
    refresh_token = criar_refresh_token(token_data)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


# --- ROTAS DA API ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(usuario: UserRegister, db: Session = Depends(get_db)):
    """Cadastra um novo usuário e retorna os tokens JWT (login automático)."""
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

        tokens = _gerar_tokens(novo_usuario)

        return {
            "sucesso": True,
            "message": "Usuário registrado com sucesso!",
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
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
    """Autentica o usuário e retorna os tokens JWT."""
    usuario = db.query(models.User).filter(models.User.email == credenciais.email).first()

    if not usuario or not verificar_senha(credenciais.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = _gerar_tokens(usuario)

    return {
        "sucesso": True,
        "message": f"Bem-vindo de volta, {usuario.nome}!",
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": "bearer",
        "usuario": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email
        }
    }


@router.post("/refresh")
async def refresh_token(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Gera um novo par de tokens usando um refresh token válido.
    Implementa rotação de tokens: o refresh token antigo é invalidado
    ao gerar um novo par.
    """
    token_data = verificar_refresh_token(body.refresh_token)

    usuario = db.query(models.User).filter(models.User.id == token_data.user_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = _gerar_tokens(usuario)

    return {
        "sucesso": True,
        "message": "Tokens renovados com sucesso!",
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": "bearer",
    }


@router.get("/me")
async def get_me(usuario_atual: models.User = Depends(obter_usuario_atual)):
    """Retorna os dados do usuário autenticado. Útil para validar o token."""
    return {
        "sucesso": True,
        "usuario": {
            "id": usuario_atual.id,
            "nome": usuario_atual.nome,
            "email": usuario_atual.email,
            "criado_em": usuario_atual.criado_em.isoformat() if usuario_atual.criado_em else None,
        }
    }