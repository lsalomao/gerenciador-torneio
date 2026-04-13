from typing import Optional
from django.db import models as dj_models
from django.db import transaction
from apps.core.models import Partida, Fase, Equipe


def _gerar_eliminatoria_automatica(fase_grupo: Fase) -> None:
    """Gera automaticamente a fase eliminatória quando a fase de grupos está 100% finalizada.
    
    Busca a próxima fase do tipo ELIMINATORIA na sequência de ordem e a popula com os
    confrontos dos classificados.
    """
    # Verificar se todas as partidas de todos os grupos estão finalizadas
    for grupo in fase_grupo.grupos.all():
        if grupo.partidas.exclude(status='FINALIZADA').exists():
            # Ainda há partidas não finalizadas neste grupo
            return
    
    # Todas as partidas estão finalizadas, procurar próxima fase eliminatória
    proxima_fase_elim = Fase.objects.filter(
        torneio=fase_grupo.torneio,
        ordem__gt=fase_grupo.ordem,
        tipo='ELIMINATORIA'
    ).order_by('ordem').first()
    
    if not proxima_fase_elim:
        # Não há fase eliminatória configurada
        return
    
    # Verificar se já foi gerada (se tem partidas)
    if proxima_fase_elim.partidas.exists():
        # Já foi gerada
        return
    
    # Importar aqui para evitar import circular
    from apps.core.services.bracket_service import gerar_eliminatoria
    
    # Gerar a eliminatória de forma silenciosa (sem mensagens de erro mostradas ao usuário,
    # apenas registradas em logs)
    try:
        with transaction.atomic():
            gerar_eliminatoria(fase_grupo.id, fase_existente=proxima_fase_elim)
    except Exception as e:
        # Log silencioso - não interrompe o fluxo
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao gerar eliminatória automaticamente: {str(e)}")


def processar_finalizacao_partida(partida: Partida) -> None:
    """Processa finalização de uma partida.

    Comportamento:
    - Se for GRUPO: verifica se todos os grupos estão finalizados e gera a próxima fase eliminatória
    - Se for ELIMINATORIA: se todas as partidas da rodada estiverem finalizadas, gera a próxima rodada
      emparelhando os vencedores em ordem de `ordem_cronograma`.
    - Se a rodada finalizada for semifinal (gerando final com 2 equipes), também gera partida de 3º lugar
      com os perdedores das semifinais.
    """
    fase = partida.fase
    
    # Se é fase de grupos, tentar gerar eliminatória automaticamente
    if fase.tipo == 'GRUPO':
        _gerar_eliminatoria_automatica(fase)
        return
    
    # Apenas continuar com lógica eliminatória se for ELIMINATORIA
    if fase.tipo != 'ELIMINATORIA':
        return

    rodada_atual = partida.rodada or 1

    partidas_rodada = fase.partidas.filter(rodada=rodada_atual)
    if partidas_rodada.exclude(status='FINALIZADA').exists():
        # ainda há partidas em andamento nesta rodada
        return

    # coletar vencedores e perdedores na ordem do cronograma
    vencedores = []
    perdedores = []
    partidas_ordenadas = partidas_rodada.order_by('ordem_cronograma')
    for p in partidas_ordenadas:
        if not p.vencedor:
            # não podemos avançar sem vencedor definido
            return
        vencedores.append(p.vencedor)
        # identificar perdedor
        perdedor = p.equipe_a if p.vencedor.id == p.equipe_b.id else p.equipe_b
        perdedores.append(perdedor)

    # se apenas um vencedor, não há próxima rodada
    if len(vencedores) <= 1:
        return

    # criar próxima rodada: rodada_atual + 1
    proxima = rodada_atual + 1
    # determinar próximo ordem_cronograma base
    max_ordem = fase.partidas.aggregate(dj_models.Max('ordem_cronograma'))['ordem_cronograma__max'] or 0
    ordem = max_ordem + 1

    # emparelhar vencedores: 0 vs 1, 2 vs 3, ... (mantendo a ordem)
    for i in range(0, len(vencedores), 2):
        a = vencedores[i]
        b = vencedores[i+1] if i+1 < len(vencedores) else None
        if not b:
            # bye: criar partida com apenas um time (ou pular)
            Partida.objects.create(fase=fase, equipe_a=a, equipe_b=a, ordem_cronograma=ordem, rodada=proxima)
        else:
            Partida.objects.create(fase=fase, equipe_a=a, equipe_b=b, ordem_cronograma=ordem, rodada=proxima)
        ordem += 1

    # Se a rodada atual gerou a final (ou seja, proxima terá 1 partida), e a rodada atual era semifinal,
    # criar também partida de 3º lugar usando os perdedores das semifinais (assumindo perdedores[0] vs perdedores[1]).
    if len(vencedores) == 2 and len(perdedores) >= 2:
        # criar partida de 3º lugar
        Partida.objects.create(fase=fase, equipe_a=perdedores[0], equipe_b=perdedores[1], ordem_cronograma=ordem, rodada=proxima+1)

    return
