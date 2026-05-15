from fastapi import APIRouter

router = APIRouter()

@router.post("/register")
async def register():
    return {"message": "Usuário registrado!"}

@router.post("/login")
async def login():
    return {"message": "Login realizado!"}