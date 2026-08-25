from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database.config import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    documentos = relationship("DocumentoPublico", back_populates="usuario", cascade="all, delete-orphan")


class DocumentoPublico(Base):
    __tablename__ = "documentos_publicos"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String(255))
    texto_extraido = Column(Text, nullable=False)
    titulo_documento = Column(Text, nullable=True, default="Documento sem título")

    elementos_formatados = Column(JSONB, nullable=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    usuario = relationship("User", back_populates="documentos")