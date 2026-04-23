from typing import Optional
from django.db import models as dj_models
from django.db import transaction
from apps.core.models import Partida, Fase, Equipe


def _fase_esta_concluida(fase: Fase) -> bool:
    if not fase.partidas.exists():
        return False
    return not fase.partidas.exclude(status='FINALIZADA').exists()


def _ativar_proxima_fase_disponivel(fase_atual: Fase) -> None:
    if not _fase_esta_concluida(fase_atual):
        return

    fases_futuras = Fase.objects.filter(
        torneio=fase_atual.torneio,
        ordem__gt=fase_atual.ordem,
    ).order_by('ordem')

    for fase in fases_futuras:
        if fase.partidas.exclude(status='FINALIZADA').exists():
            if not fase.is_ativa:
                fase.is_ativa = True
                fase.save(update_fields=['is_ativa'])
            return


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
        _ativar_proxima_fase_disponivel(fase)
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

    # caso de semifinal: criar FINAL e 3º LUGAR em fases seguintes (quando existirem)
    if len(vencedores) == 2 and len(perdedores) >= 2:
        fases_futuras = Fase.objects.filter(
            torneio=fase.torneio,
            tipo='ELIMINATORIA',
            ordem__gt=fase.ordem,
        ).order_by('ordem')

        fase_final = fases_futuras.filter(nome__icontains='final').exclude(nome__icontains='semi').first()
        fase_terceiro = fases_futuras.filter(
            dj_models.Q(nome__icontains='3') | dj_models.Q(nome__icontains='terceiro')
        ).first()

        if not fase_final:
            fase_final = fases_futuras.first()

        if not fase_terceiro:
            fase_terceiro = fases_futuras.exclude(pk=getattr(fase_final, 'pk', None)).first()

        if fase_final and not fase_final.partidas.exists():
            ordem_final = (fase_final.partidas.aggregate(dj_models.Max('ordem_cronograma'))['ordem_cronograma__max'] or 0) + 1
            Partida.objects.create(
                fase=fase_final,
                equipe_a=vencedores[0],
                equipe_b=vencedores[1],
                ordem_cronograma=ordem_final,
                rodada=1,
            )
            if not fase_final.is_ativa:
                fase_final.is_ativa = True
                fase_final.save(update_fields=['is_ativa'])

        if fase_terceiro and not fase_terceiro.partidas.exists():
            ordem_terceiro = (fase_terceiro.partidas.aggregate(dj_models.Max('ordem_cronograma'))['ordem_cronograma__max'] or 0) + 1
            Partida.objects.create(
                fase=fase_terceiro,
                equipe_a=perdedores[0],
                equipe_b=perdedores[1],
                ordem_cronograma=ordem_terceiro,
                rodada=1,
            )

        _ativar_proxima_fase_disponivel(fase)
        return

    # criar próxima rodada dentro da mesma fase eliminatória
    proxima = rodada_atual + 1
    max_ordem = fase.partidas.aggregate(dj_models.Max('ordem_cronograma'))['ordem_cronograma__max'] or 0
    ordem = max_ordem + 1

    for i in range(0, len(vencedores), 2):
        a = vencedores[i]
        b = vencedores[i+1] if i+1 < len(vencedores) else None
        if not b:
            Partida.objects.create(fase=fase, equipe_a=a, equipe_b=a, ordem_cronograma=ordem, rodada=proxima)
        else:
            Partida.objects.create(fase=fase, equipe_a=a, equipe_b=b, ordem_cronograma=ordem, rodada=proxima)
        ordem += 1

    _ativar_proxima_fase_disponivel(fase)
    return
