from typing import Dict, Tuple, Optional
from django.db import transaction

from apps.core.models import Fase, Partida


def pode_resetar_fase(fase_id: int) -> Tuple[bool, str]:
    """
    Verifica se uma fase pode ser resetada.
    
    Regra de bloqueio:
    - Se existir qualquer partida com status='FINALIZADA', não pode resetar
    
    Args:
        fase_id: ID da fase
        
    Returns:
        Tuple (pode_resetar: bool, mensagem: str)
    """
    try:
        fase = Fase.objects.get(id=fase_id)
    except Fase.DoesNotExist:
        return False, "Fase não encontrada"
    
    partidas_finalizadas = Partida.objects.filter(
        fase=fase,
        status='FINALIZADA'
    ).select_related('equipe_a', 'equipe_b')
    
    count = partidas_finalizadas.count()
    
    if count > 0:
        partidas_info = []
        for p in partidas_finalizadas[:5]:
            partidas_info.append(f"{p.equipe_a.nome} vs {p.equipe_b.nome}")
        
        if count > 5:
            partidas_info.append(f"... e mais {count - 5} partida(s)")
        
        mensagem = (
            f"Não é possível resetar. {count} partida(s) já foram finalizadas:\n"
            + "\n".join(f"- {info}" for info in partidas_info)
        )
        return False, mensagem
    
    return True, "Fase pode ser resetada"


def resetar_fase(fase_id: int, limpar_grupos: Optional[bool] = None) -> Dict:
    """
    Reseta uma fase.
    
    O que é feito:
    - Remove todas as partidas da fase (SetResult são deletados em cascata)
    - Se limpar_grupos=None (comportamento padrão legado): em fase de grupos, remove os grupos criados
    - Se limpar_grupos=True: remove associações de equipes dos grupos
    - Se limpar_grupos=False: preserva grupos e equipes
    
    Args:
        fase_id: ID da fase
        limpar_grupos: Define política de limpeza dos grupos
        
    Returns:
        Dict com resultado:
        {
            "success": bool,
            "partidas_removidas": int,
            "grupos_limpos": int,
            "message": str
        }
    """
    pode, mensagem = pode_resetar_fase(fase_id)
    
    if not pode:
        return {
            "success": False,
            "partidas_removidas": 0,
            "grupos_limpos": 0,
            "message": mensagem
        }
    
    try:
        fase = Fase.objects.prefetch_related('grupos').get(id=fase_id)
    except Fase.DoesNotExist:
        return {
            "success": False,
            "partidas_removidas": 0,
            "grupos_limpos": 0,
            "message": "Fase não encontrada"
        }
    
    with transaction.atomic():
        partidas_count = Partida.objects.filter(fase=fase).count()
        Partida.objects.filter(fase=fase).delete()

        grupos_limpos = 0
        if limpar_grupos is None:
            if fase.tipo == 'GRUPO':
                grupos_limpos = fase.grupos.count()
                fase.grupos.all().delete()
        elif limpar_grupos:
            for grupo in fase.grupos.all():
                if grupo.equipes.exists():
                    grupo.equipes.clear()
                    grupos_limpos += 1

    if limpar_grupos is None and fase.tipo == 'GRUPO':
        mensagem_grupos = f" e {grupos_limpos} grupo(s) excluído(s)"
    elif limpar_grupos:
        mensagem_grupos = f" e {grupos_limpos} grupo(s) limpo(s)"
    else:
        mensagem_grupos = ""
    
    return {
        "success": True,
        "partidas_removidas": partidas_count,
        "grupos_limpos": grupos_limpos,
        "message": f"{partidas_count} partida(s) removida(s){mensagem_grupos}"
    }


def obter_estatisticas_fase(fase_id: int) -> Dict:
    """
    Obtém estatísticas sobre uma fase.
    
    Args:
        fase_id: ID da fase
        
    Returns:
        Dict com estatísticas
    """
    try:
        fase = Fase.objects.get(id=fase_id)
    except Fase.DoesNotExist:
        return {
            "success": False,
            "message": "Fase não encontrada"
        }
    
    total_partidas = Partida.objects.filter(fase=fase).count()
    partidas_agendadas = Partida.objects.filter(fase=fase, status='AGENDADA').count()
    partidas_ao_vivo = Partida.objects.filter(fase=fase, status='AO_VIVO').count()
    partidas_finalizadas = Partida.objects.filter(fase=fase, status='FINALIZADA').count()
    
    grupos = fase.grupos.prefetch_related('equipes').all()
    total_grupos = grupos.count()
    grupos_com_equipes = sum(1 for g in grupos if g.equipes.exists())
    
    total_equipes_alocadas = sum(g.equipes.count() for g in grupos)
    
    pode_resetar, msg_reset = pode_resetar_fase(fase_id)
    
    return {
        "success": True,
        "fase_nome": fase.nome,
        "fase_tipo": fase.tipo,
        "total_grupos": total_grupos,
        "grupos_com_equipes": grupos_com_equipes,
        "total_equipes_alocadas": total_equipes_alocadas,
        "total_partidas": total_partidas,
        "partidas_agendadas": partidas_agendadas,
        "partidas_ao_vivo": partidas_ao_vivo,
        "partidas_finalizadas": partidas_finalizadas,
        "pode_resetar": pode_resetar,
        "mensagem_reset": msg_reset
    }
