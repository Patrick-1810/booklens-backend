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

    documentos = relationship("DocumentoPublico", back_populates="usuario", cascade="all, delete-orphan")


class DocumentoPublico(Base):
    __tablename__ = "documentos_publicos"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String(150))
    texto_extraido = Column(Text, nullable=False)
    titulo_documento = Column(String(150), nullable=True, default="Documento sem título")
    criado_em = Column(DateTime, default=datetime.utcnow)

    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    usuario = relationship("User", back_populates="documentos")