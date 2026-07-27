<!-- ========================================================= -->
<!--                           BADGES                          -->
<!-- ========================================================= -->

[PYTHON_BADGE]: https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white
[FASTAPI_BADGE]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[FLASK_BADGE]: https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white
[SQLITE_BADGE]: https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white
[SQLALCHEMY_BADGE]: https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge
[OPENCV_BADGE]: https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white
[TESSERACT_BADGE]: https://img.shields.io/badge/Tesseract-OCR-blue?style=for-the-badge
[EASYOCR_BADGE]: https://img.shields.io/badge/EasyOCR-00C853?style=for-the-badge
[JWT_BADGE]: https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens
[PRS_BADGE]: https://img.shields.io/badge/PRs-Not%20Accepted-red?style=for-the-badge

<h1 align="center">
📚 BookLens - Backend API
</h1>

<p align="center">

![python][PYTHON_BADGE]
![fastapi][FASTAPI_BADGE]
![flask][FLASK_BADGE]
![sqlite][SQLITE_BADGE]
![sqlalchemy][SQLALCHEMY_BADGE]
![opencv][OPENCV_BADGE]
![tesseract][TESSERACT_BADGE]
![easyocr][EASYOCR_BADGE]
![jwt][JWT_BADGE]
![prs][PRS_BADGE]

</p>

<p align="center">

Backend desenvolvido para o projeto <strong>BookLens</strong>, um sistema inteligente para digitalização e extração automática de informações de documentos públicos utilizando Processamento Digital de Imagens (PDI) e Reconhecimento Óptico de Caracteres (OCR).

</p>

---

> ## ⚠️ Aviso
>
> Este repositório é disponibilizado exclusivamente para fins de demonstração acadêmica e portfólio.
>
> O código-fonte é proprietário e não pode ser copiado, modificado, redistribuído ou utilizado sem autorização expressa do autor.

---

# 📑 Sumário

- 🚀 Sobre
- 🎓 Objetivo do Projeto
- ✨ Funcionalidades
- 🛠 Tecnologias
- 🏛 Arquitetura
- 📂 Estrutura do Projeto
- 🚀 Instalação
- ⚙ Configuração
- ▶ Execução
- 📖 Documentação
- 📍 Endpoints
- 🖼 Pipeline de Processamento
- 🔒 Segurança
- 👨‍💻 Desenvolvedor
- 📜 Direitos Autorais

---

# 🚀 Sobre

O **BookLens** é o projeto desenvolvido como Trabalho de Conclusão de Curso (TCC) em Ciência da Computação.

A aplicação foi criada com o objetivo de automatizar a extração de informações de documentos públicos físicos através de técnicas de **Processamento Digital de Imagens (PDI)** e **Reconhecimento Óptico de Caracteres (OCR)**.

O backend é responsável pelo processamento das imagens recebidas pelo frontend, aplicação dos filtros de melhoria, execução do OCR, validação das palavras utilizando um dicionário e gerenciamento dos usuários da aplicação.

---

# 🎓 Objetivo do Projeto

O projeto busca minimizar erros durante a digitalização de informações de documentos públicos, utilizando técnicas computacionais capazes de melhorar significativamente a qualidade da imagem antes da extração textual.

Entre as etapas implementadas estão:

- Correção de contraste
- Conversão para escala de cinza
- Aplicação de filtros de ruído
- Limiarização
- Operações morfológicas
- Correção da inclinação da imagem
- OCR
- Validação por dicionário
- Retorno estruturado para o frontend

---

# ✨ Funcionalidades

- ✅ Cadastro e autenticação de usuários
- ✅ Upload de imagens
- ✅ Processamento Digital de Imagens (PDI)
- ✅ Extração automática de texto (OCR)
- ✅ Correção e validação utilizando dicionário
- ✅ Histórico de processamentos
- ✅ API REST
- ✅ Banco de dados SQLite
- ✅ Documentação automática (FastAPI)

---

# 🛠 Tecnologias

| Tecnologia | Finalidade |
|------------|------------|
| Python | Linguagem |
| FastAPI | API REST |
| Flask | Framework HTTP |
| SQLite | Banco de Dados |
| SQLAlchemy | ORM |
| OpenCV | Processamento de Imagens |
| Tesseract OCR | OCR |
| EasyOCR | OCR baseado em IA |
| JWT | Autenticação |

---

# 🏛 Arquitetura

O backend foi organizado em módulos independentes para facilitar manutenção e escalabilidade.

```text
Frontend

│

▼

API REST

│

▼

Rotas

│

▼

Processamento de Imagens

│

▼

OCR

│

▼

Validação por Dicionário

│

▼

Banco de Dados
```

---

# 📂 Estrutura do Projeto

```text
booklens-backend/

├── app
│
├── core
│   └── processor.py
│
├── database
│   ├── config.py
│   ├── models.py
│   └── __init__.py
│
├── routes
│   ├── auth.py
│   ├── dictionary.py
│   └── ocr.py
│
├── models
│
├── images_test
│
├── debug_images
│
├── booklens.db
│
└── main.py
```

---

# ⚙ Principais Módulos

### 📷 processor.py

Responsável por toda a etapa de Processamento Digital de Imagens (PDI), incluindo aplicação de filtros, remoção de ruídos, ajuste de contraste e preparação da imagem para o OCR.

---

### 🔍 ocr.py

Recebe imagens enviadas pelo frontend, executa o pipeline de processamento e realiza a extração automática do texto.

---

### 📖 dictionary.py

Realiza validação das palavras extraídas utilizando o dicionário da aplicação, sugerindo possíveis correções.

---

### 🔐 auth.py

Gerencia cadastro, autenticação de usuários e geração de Tokens JWT.

---

### 💾 database/

Responsável pela configuração do banco SQLite e definição das entidades da aplicação.

---

# 🚀 Instalação

Clone o projeto

```bash
git clone https://github.com/Patrick-1810/booklens-backend.git

cd booklens-backend
```

---

## Crie um ambiente virtual

### Linux/macOS

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv

.venv\Scripts\Activate.ps1
```

---

## Instale as dependências

```bash
pip install -r requirements.txt
```

---

# ⚙ Configuração

Caso utilize o Tesseract OCR, configure corretamente o caminho do executável de acordo com seu sistema operacional.

Exemplo (Windows):

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

---

# ▶ Execução

FastAPI

```bash
uvicorn app.main:app --reload
```

ou

Flask

```bash
python app/main.py
```

---

# 📖 Documentação

Após iniciar o servidor, a documentação da API estará disponível em:

### Swagger

```
http://localhost:8000/docs
```

---

# 📍 Endpoints

## 🔐 Autenticação

| Método | Endpoint | Descrição |
|---------|----------|-----------|
| POST | `/auth/register` | Cadastro de usuário |
| POST | `/auth/login` | Login |

---

## 📷 OCR

| Método | Endpoint | Descrição |
|---------|-----------|------------|
| POST | `/ocr/upload` | Upload e processamento da imagem |
| POST | `/ocr/extract` | Extração do texto |

---

## 📖 Dicionário

| Método | Endpoint | Descrição |
|---------|-----------|------------|
| GET | `/dictionary` | Consulta palavras |
| POST | `/dictionary` | Cadastro de palavras |

---

# 🖼 Pipeline de Processamento

O fluxo de processamento das imagens ocorre da seguinte forma:

```text
Imagem

↓

Escala de Cinza

↓

Correção de Contraste

↓

Remoção de Ruídos

↓

Limiarização

↓

Operações Morfológicas

↓

Correção da Inclinação

↓

OCR

↓

Validação por Dicionário

↓

Texto Final
```

---

# 🔒 Segurança

A API implementa:

- Autenticação JWT
- Hash de senhas
- Separação por camadas
- Tratamento de exceções
- Persistência segura utilizando SQLAlchemy
- Organização modular para escalabilidade

---

# 👨‍💻 Desenvolvedor

<p align="center">
<a href="https://patrickprestes-developer-amber.vercel.app">
<img src="https://github.com/Patrick-1810.png" width="150px" alt="Patrick Prestes"/>
</a>
</p>

<h3 align="center">
Patrick Prestes
</h3>

<p align="center">

<a href="https://patrickprestes-developer-amber.vercel.app">
<img src="https://img.shields.io/badge/🌐-Portfólio-4F46E5?style=for-the-badge">
</a>

</p>

---

# 📜 Direitos Autorais

**© 2026 Patrick Prestes. Todos os direitos reservados.**

Este software foi desenvolvido como Trabalho de Conclusão de Curso (TCC) do curso de Ciência da Computação.

O código-fonte deste repositório é disponibilizado exclusivamente para fins de demonstração acadêmica e composição de portfólio.

É proibida a reprodução, modificação, redistribuição ou utilização deste projeto, total ou parcialmente, sem autorização prévia e expressa do autor.

O acesso público ao código não concede qualquer licença de uso sobre este software.
