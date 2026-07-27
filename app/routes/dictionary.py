from fastapi import APIRouter, Query
from spellchecker import SpellChecker

router = APIRouter(prefix="/dicionario", tags=["Dicionário e Autocompletar"])

spell = SpellChecker(language='pt')

@router.get("/autocompletar")
async def autocompletar(q: str = Query(..., min_length=2, description="Prefixo ou palavra parcial")):
    termo = q.lower().strip()

    sugestoes = []
    for palavra in spell.word_frequency:
        if palavra.startswith(termo):
            sugestoes.append(palavra)
            if len(sugestoes) >= 10:
                break

    return {
        "termo_buscado": q,
        "sugestoes": sugestoes
    }