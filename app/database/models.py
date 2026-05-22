from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.config import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)

    trechos = relationship("TrechoLivro", back_populates="usuario", cascade="all, delete-orphan")


class TrechoLivro(Base):
    __tablename__ = "trechos_livros"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String(150))
    texto_extraido = Column(Text, nullable=False)
    titulo_livro = Column(String(150), nullable=True, default="Desconhecido")
    criado_em = Column(DateTime, default=datetime.utcnow)

    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    usuario = relationship("User", back_populates="trechos")