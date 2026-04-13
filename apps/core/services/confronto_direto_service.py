from typing import List
from apps.core.services.ranking_service import _confronto_direto_miniranking
from apps.core.models import Grupo


def confronto_direto(grupo: Grupo, equipes_ids: List[int]) -> List[int]:
    """Wrapper para calcular ordem por confronto direto entre equipes dentro do grupo."""
    return _confronto_direto_miniranking(grupo, equipes_ids)
