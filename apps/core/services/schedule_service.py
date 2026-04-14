from typing import Dict, List
from django.db import transaction

from apps.core.models import Fase, Grupo, Partida, Equipe


def gerar_round_robin(grupo_id: int) -> Dict:
    """
    Gera partidas round-robin (todos contra todos) para um grupo.
    
    Regras:
    - Para N equipes: N*(N-1)/2 partidas
    - Não gerar A vs B e B vs A (sem duplicidade)
    - Não gerar A vs A (auto-jogo)
    - Partidas nascem com status='AGENDADA'
    - ordem_cronograma será atribuída depois por atribuir_ordem_cronograma()
    
    Args:
        grupo_id: ID do grupo
        
    Returns:
        Dict com resultado:
        {
            "success": bool,
            "partidas_criadas": int,
            "message": str
        }
    """
    try:
        grupo = Grupo.objects.select_related('fase').prefetch_related('equipes').get(id=grupo_id)
    except Grupo.DoesNotExist:
        return {
            "success": False,
            "partidas_criadas": 0,
            "message": "Grupo não encontrado"
        }
    
    equipes = list(grupo.equipes.all().order_by('id'))

    if len(equipes) < 2:
        return {
            "success": False,
            "partidas_criadas": 0,
            "message": f"Grupo '{grupo.nome}' precisa de pelo menos 2 equipes (possui {len(equipes)})"
        }

    partidas_existentes = Partida.objects.filter(grupo=grupo).exists()
    if partidas_existentes:
        return {
            "success": False,
            "partidas_criadas": 0,
            "message": f"Grupo '{grupo.nome}' já possui partidas. Use 'Resetar Fase' para gerar novamente"
        }

    partidas_criadas = 0
    rotacao = equipes[:]
    if len(rotacao) % 2 != 0:
        rotacao.append(None)

    total_rodadas = len(rotacao) - 1
    jogos_por_rodada = len(rotacao) // 2

    with transaction.atomic():
        for rodada in range(1, total_rodadas + 1):
            for i in range(jogos_por_rodada):
                equipe_a = rotacao[i]
                equipe_b = rotacao[-(i + 1)]

                if equipe_a is None or equipe_b is None:
                    continue

                Partida.objects.create(
                    fase=grupo.fase,
                    grupo=grupo,
                    equipe_a=equipe_a,
                    equipe_b=equipe_b,
                    status='AGENDADA',
                    is_wo=False,
                    ordem_cronograma=0,
                    rodada=rodada,
                )
                partidas_criadas += 1

            rotacao = [rotacao[0], rotacao[-1], *rotacao[1:-1]]

    partidas_esperadas = (len(equipes) * (len(equipes) - 1)) // 2
    
    return {
        "success": True,
        "partidas_criadas": partidas_criadas,
        "message": f"{partidas_criadas} partida(s) criada(s) no {grupo.nome} ({partidas_esperadas} esperadas)"
    }


def gerar_round_robin_fase(fase_id: int) -> Dict:
    """
    Gera partidas round-robin para todos os grupos de uma fase.
    
    Args:
        fase_id: ID da fase
        
    Returns:
        Dict com resultado:
        {
            "success": bool,
            "partidas_criadas": int,
            "grupos_processados": int,
            "message": str,
            "erros": List[str]
        }
    """
    try:
        fase = Fase.objects.get(id=fase_id)
    except Fase.DoesNotExist:
        return {
            "success": False,
            "partidas_criadas": 0,
            "grupos_processados": 0,
            "message": "Fase não encontrada",
            "erros": []
        }
    
    if fase.tipo != 'GRUPO':
        return {
            "success": False,
            "partidas_criadas": 0,
            "grupos_processados": 0,
            "message": "Geração de partidas round-robin só é permitida em fases do tipo GRUPO",
            "erros": []
        }
    
    partidas_existentes = Partida.objects.filter(fase=fase).exists()
    if partidas_existentes:
        return {
            "success": False,
            "partidas_criadas": 0,
            "grupos_processados": 0,
            "message": "Fase já possui partidas. Use 'Resetar Fase' para gerar novamente",
            "erros": []
        }
    
    grupos = fase.grupos.prefetch_related('equipes').all()
    
    if not grupos:
        return {
            "success": False,
            "partidas_criadas": 0,
            "grupos_processados": 0,
            "message": "Nenhum grupo criado para esta fase",
            "erros": []
        }
    
    total_partidas = 0
    grupos_processados = 0
    erros = []
    
    for grupo in grupos:
        resultado = gerar_round_robin(grupo.id)
        
        if resultado["success"]:
            total_partidas += resultado["partidas_criadas"]
            grupos_processados += 1
        else:
            erros.append(f"{grupo.nome}: {resultado['message']}")
    
    if grupos_processados > 0:
        ordem_resultado = atribuir_ordem_cronograma(fase_id)
        
        return {
            "success": True,
            "partidas_criadas": total_partidas,
            "grupos_processados": grupos_processados,
            "message": f"{total_partidas} partida(s) criada(s) em {grupos_processados} grupo(s). Cronograma atribuído.",
            "erros": erros
        }
    else:
        return {
            "success": False,
            "partidas_criadas": 0,
            "grupos_processados": 0,
            "message": "Nenhuma partida foi criada",
            "erros": erros
        }


def atribuir_ordem_cronograma(fase_id: int) -> Dict:
    """
    Atribui ordem cronológica sequencial às partidas de uma fase.
    
    A ordem é determinada por:
    1. Grupo (ordem alfabética do nome do grupo)
    2. ID da partida (ordem de criação)
    
    Args:
        fase_id: ID da fase
        
    Returns:
        Dict com resultado:
        {
            "success": bool,
            "partidas_ordenadas": int,
            "message": str
        }
    """
    try:
        fase = Fase.objects.get(id=fase_id)
    except Fase.DoesNotExist:
        return {
            "success": False,
            "partidas_ordenadas": 0,
            "message": "Fase não encontrada"
        }
    
    partidas = Partida.objects.filter(fase=fase).select_related('grupo').order_by('grupo__nome', 'id')
    
    if not partidas.exists():
        return {
            "success": False,
            "partidas_ordenadas": 0,
            "message": "Nenhuma partida encontrada para esta fase"
        }
    
    partidas_por_grupo = {}
    for partida in partidas:
        grupo_nome = partida.grupo.nome
        partidas_por_grupo.setdefault(grupo_nome, []).append(partida)

    grupos_ordenados = sorted(partidas_por_grupo.keys())
    intercaladas = []

    # Agrupar partidas em blocos por grupo (ex.: 2 jogos do Grupo A, 2 do Grupo B, ...)
    chunk_size = 2
    max_partidas = max(len(lista) for lista in partidas_por_grupo.values())

    for start in range(0, max_partidas, chunk_size):
        for grupo_nome in grupos_ordenados:
            grupo_partidas = partidas_por_grupo[grupo_nome]
            bloco = grupo_partidas[start:start + chunk_size]
            if bloco:
                intercaladas.extend(bloco)

    partidas_ordenadas = 0

    with transaction.atomic():
        for ordem, partida in enumerate(intercaladas, start=1):
            partida.ordem_cronograma = ordem
            partida.save(update_fields=['ordem_cronograma'])
            partidas_ordenadas += 1
    
    return {
        "success": True,
        "partidas_ordenadas": partidas_ordenadas,
        "message": f"{partidas_ordenadas} partida(s) ordenada(s) sequencialmente"
    }


def reordenar_partidas(fase_id: int, nova_ordem: List[int]) -> Dict:
    """
    Reordena manualmente as partidas de uma fase.
    
    Args:
        fase_id: ID da fase
        nova_ordem: Lista de IDs de partidas na nova ordem desejada
        
    Returns:
        Dict com resultado
    """
    try:
        fase = Fase.objects.get(id=fase_id)
    except Fase.DoesNotExist:
        return {
            "success": False,
            "message": "Fase não encontrada"
        }
    
    partidas_ids_fase = set(Partida.objects.filter(fase=fase).values_list('id', flat=True))
    
    if set(nova_ordem) != partidas_ids_fase:
        return {
            "success": False,
            "message": "A lista de IDs não corresponde às partidas da fase"
        }
    
    with transaction.atomic():
        for ordem, partida_id in enumerate(nova_ordem, start=1):
            Partida.objects.filter(id=partida_id).update(ordem_cronograma=ordem)
    
    return {
        "success": True,
        "message": f"{len(nova_ordem)} partida(s) reordenada(s)"
    }
