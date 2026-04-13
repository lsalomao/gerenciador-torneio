import random
from typing import Dict, List, Tuple
from django.db import transaction
from django.db.models import Count

from apps.core.models import Fase, Grupo, Equipe


def sortear_equipes_automatico(fase_id: int) -> Dict:
    """
    Sorteia equipes automaticamente entre os grupos de uma fase.
    
    Regras:
    - Distribuição balanceada (diferença máxima de 1 equipe entre grupos)
    - Sem duplicidade (uma equipe não pode estar em dois grupos)
    - Apenas para fases tipo GRUPO
    
    Args:
        fase_id: ID da fase
        
    Returns:
        Dict com resultado da operação:
        {
            "success": bool,
            "grupos_preenchidos": int,
            "equipes_distribuidas": int,
            "message": str
        }
    """
    try:
        fase = Fase.objects.select_related('torneio').get(id=fase_id)
    except Fase.DoesNotExist:
        return {
            "success": False,
            "grupos_preenchidos": 0,
            "equipes_distribuidas": 0,
            "message": "Fase não encontrada"
        }
    
    if fase.tipo != 'GRUPO':
        return {
            "success": False,
            "grupos_preenchidos": 0,
            "equipes_distribuidas": 0,
            "message": "Sorteio só é permitido em fases do tipo GRUPO"
        }
    
    grupos = list(fase.grupos.all())
    
    if not grupos:
        return {
            "success": False,
            "grupos_preenchidos": 0,
            "equipes_distribuidas": 0,
            "message": "Nenhum grupo criado para esta fase"
        }
    
    equipes_disponiveis = list(
        Equipe.objects.filter(torneio=fase.torneio)
        .exclude(grupos__fase=fase)
    )
    
    if not equipes_disponiveis:
        return {
            "success": False,
            "grupos_preenchidos": 0,
            "equipes_distribuidas": 0,
            "message": "Nenhuma equipe disponível para sorteio"
        }
    
    random.shuffle(equipes_disponiveis)
    
    num_grupos = len(grupos)
    equipes_por_grupo = len(equipes_disponiveis) // num_grupos
    equipes_extras = len(equipes_disponiveis) % num_grupos
    
    with transaction.atomic():
        idx = 0
        grupos_preenchidos = 0
        
        for i, grupo in enumerate(grupos):
            num_equipes = equipes_por_grupo + (1 if i < equipes_extras else 0)
            
            equipes_para_grupo = equipes_disponiveis[idx:idx + num_equipes]
            if equipes_para_grupo:
                grupo.equipes.add(*equipes_para_grupo)
                grupos_preenchidos += 1
            
            idx += num_equipes
    
    return {
        "success": True,
        "grupos_preenchidos": grupos_preenchidos,
        "equipes_distribuidas": len(equipes_disponiveis),
        "message": f"{len(equipes_disponiveis)} equipes distribuídas em {grupos_preenchidos} grupos"
    }


def validar_distribuicao_equipes(fase_id: int) -> Tuple[bool, str]:
    """
    Valida se a distribuição de equipes nos grupos está correta.
    
    Verifica:
    - Nenhuma equipe está em mais de um grupo da mesma fase
    - Todas as equipes pertencem ao torneio da fase
    
    Args:
        fase_id: ID da fase
        
    Returns:
        Tuple (is_valid: bool, message: str)
    """
    try:
        fase = Fase.objects.select_related('torneio').get(id=fase_id)
    except Fase.DoesNotExist:
        return False, "Fase não encontrada"
    
    grupos = fase.grupos.prefetch_related('equipes').all()
    
    equipes_vistas = set()
    
    for grupo in grupos:
        for equipe in grupo.equipes.all():
            if equipe.torneio_id != fase.torneio_id:
                return False, f"Equipe '{equipe.nome}' não pertence ao torneio desta fase"
            
            if equipe.id in equipes_vistas:
                return False, f"Equipe '{equipe.nome}' está em mais de um grupo"
            
            equipes_vistas.add(equipe.id)
    
    return True, "Distribuição válida"


def alocar_equipe_manual(grupo_id: int, equipe_id: int) -> Dict:
    """
    Aloca uma equipe manualmente em um grupo.
    
    Validações:
    - Equipe não pode estar em outro grupo da mesma fase
    - Equipe deve pertencer ao torneio da fase
    - Grupo deve ser de fase tipo GRUPO
    
    Args:
        grupo_id: ID do grupo
        equipe_id: ID da equipe
        
    Returns:
        Dict com resultado:
        {
            "success": bool,
            "message": str
        }
    """
    try:
        grupo = Grupo.objects.select_related('fase__torneio').get(id=grupo_id)
    except Grupo.DoesNotExist:
        return {
            "success": False,
            "message": "Grupo não encontrado"
        }
    
    if grupo.fase.tipo != 'GRUPO':
        return {
            "success": False,
            "message": "Alocação manual só é permitida em fases do tipo GRUPO"
        }
    
    try:
        equipe = Equipe.objects.get(id=equipe_id)
    except Equipe.DoesNotExist:
        return {
            "success": False,
            "message": "Equipe não encontrada"
        }
    
    if equipe.torneio_id != grupo.fase.torneio_id:
        return {
            "success": False,
            "message": f"Equipe '{equipe.nome}' não pertence ao torneio desta fase"
        }
    
    grupos_da_fase = Grupo.objects.filter(fase=grupo.fase, equipes=equipe)
    if grupos_da_fase.exists():
        grupo_existente = grupos_da_fase.first()
        if grupo_existente.id != grupo.id:
            return {
                "success": False,
                "message": f"Equipe '{equipe.nome}' já está alocada no {grupo_existente.nome}"
            }
    
    grupo.equipes.add(equipe)
    
    return {
        "success": True,
        "message": f"Equipe '{equipe.nome}' alocada no {grupo.nome}"
    }


def remover_equipe_grupo(grupo_id: int, equipe_id: int) -> Dict:
    """
    Remove uma equipe de um grupo.
    
    Args:
        grupo_id: ID do grupo
        equipe_id: ID da equipe
        
    Returns:
        Dict com resultado
    """
    try:
        grupo = Grupo.objects.get(id=grupo_id)
    except Grupo.DoesNotExist:
        return {
            "success": False,
            "message": "Grupo não encontrado"
        }
    
    try:
        equipe = Equipe.objects.get(id=equipe_id)
    except Equipe.DoesNotExist:
        return {
            "success": False,
            "message": "Equipe não encontrada"
        }
    
    if not grupo.equipes.filter(id=equipe_id).exists():
        return {
            "success": False,
            "message": f"Equipe '{equipe.nome}' não está no {grupo.nome}"
        }
    
    grupo.equipes.remove(equipe)
    
    return {
        "success": True,
        "message": f"Equipe '{equipe.nome}' removida do {grupo.nome}"
    }


def limpar_grupos_fase(fase_id: int) -> Dict:
    """
    Remove todas as equipes de todos os grupos de uma fase.
    
    Args:
        fase_id: ID da fase
        
    Returns:
        Dict com resultado
    """
    try:
        fase = Fase.objects.get(id=fase_id)
    except Fase.DoesNotExist:
        return {
            "success": False,
            "grupos_limpos": 0,
            "message": "Fase não encontrada"
        }
    
    grupos = fase.grupos.all()
    grupos_limpos = 0
    
    with transaction.atomic():
        for grupo in grupos:
            if grupo.equipes.exists():
                grupo.equipes.clear()
                grupos_limpos += 1
    
    return {
        "success": True,
        "grupos_limpos": grupos_limpos,
        "message": f"{grupos_limpos} grupo(s) limpo(s)"
    }
