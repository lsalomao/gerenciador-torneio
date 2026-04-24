from apps.core.models import Jogador, Partida
from apps.core.services.ranking_service import rankear_grupo


def get_active_phase(torneio):
    fase = torneio.fases.filter(is_ativa=True).order_by('ordem').first()
    if fase:
        return fase
    return torneio.fases.order_by('ordem').first()


def get_current_live_match(torneio):
    return Partida.objects.select_related(
        'fase', 'grupo', 'equipe_a', 'equipe_b', 'vencedor'
    ).prefetch_related('sets').filter(
        fase__torneio=torneio,
        status='AO_VIVO'
    ).order_by('ordem_cronograma', 'id').first()


def get_current_highlight(torneio):
    partida_ao_vivo = get_current_live_match(torneio)
    if partida_ao_vivo:
        return partida_ao_vivo

    partida_agendada = Partida.objects.select_related(
        'fase', 'grupo', 'equipe_a', 'equipe_b', 'vencedor'
    ).prefetch_related('sets').filter(
        fase__torneio=torneio,
        status='AGENDADA'
    ).order_by('ordem_cronograma', 'id').first()
    return partida_agendada


def get_upcoming_matches(torneio, exclude_partida_id=None, limit=8):
    fase_ativa = get_active_phase(torneio)
    if not fase_ativa:
        return Partida.objects.none()

    partidas = Partida.objects.select_related(
        'fase', 'grupo', 'equipe_a', 'equipe_b'
    ).filter(
        fase=fase_ativa,
        status='AGENDADA'
    ).order_by('ordem_cronograma', 'id')

    if exclude_partida_id:
        partidas = partidas.exclude(id=exclude_partida_id)

    return partidas[:limit]


def get_dashboard_context(torneio):
    fase = get_active_phase(torneio)
    live_match = get_current_live_match(torneio)
    context = {
        'torneio': {
            'nome': torneio.nome,
            'slug': torneio.slug,
            'live_url': torneio.live_url,
            'polling_interval': torneio.polling_interval,
        },
        'fase_ativa': None,
        'grupos': [],
        'confrontos': [],
        'live_match': None,
        'campeao': None,
        'podio': None,
    }

    if live_match:
        context['live_match'] = {
            'id': live_match.id,
            'grupo_id': live_match.grupo_id,
            'equipe_a': live_match.equipe_a.nome,
            'equipe_b': live_match.equipe_b.nome,
        }

    if not fase:
        return context

    context['fase_ativa'] = {
        'id': fase.id,
        'nome': fase.nome,
        'tipo': fase.tipo,
        'equipes_avancam': fase.equipes_avancam,
    }

    if fase.tipo == 'GRUPO':
        grupos = fase.grupos.prefetch_related('equipes').all()
        for grupo in grupos:
            ranking = rankear_grupo(grupo)
            classificacao = []
            for item in ranking:
                classificacao.append({
                    'posicao': item['posicao'],
                    'equipe': item['equipe'].nome,
                    'jogos': item['jogos'],
                    'vitorias': item['vitorias'],
                    'derrotas': item['derrotas'],
                    'sets_ganhos': item['sets_ganhos'],
                    'sets_perdidos': item['sets_perdidos'],
                    'saldo_sets': item['saldo_sets'],
                    'pontos_feitos': item['pontos_feitos'],
                    'pontos_tomados': item['pontos_tomados'],
                    'saldo_pontos': item['saldo_pontos'],
                })
            context['grupos'].append({
                'id': grupo.id,
                'nome': grupo.nome,
                'classificacao': classificacao,
            })
    else:
        confrontos = fase.partidas.select_related('equipe_a', 'equipe_b', 'vencedor').prefetch_related('sets').order_by('ordem_cronograma', 'id')
        for partida in confrontos:
            context['confrontos'].append({
                'id': partida.id,
                'ordem_cronograma': partida.ordem_cronograma,
                'status': partida.status,
                'equipe_a': partida.equipe_a.nome,
                'equipe_b': partida.equipe_b.nome,
                'vencedor': partida.vencedor.nome if partida.vencedor else None,
                'sets': [
                    {
                        'numero_set': s.numero_set,
                        'pontos_a': s.pontos_a,
                        'pontos_b': s.pontos_b,
                    }
                    for s in partida.sets.all()
                ],
            })

        if fase.nome.strip().lower() == 'final':
            partida_final = confrontos.first()
            if partida_final and partida_final.status == 'FINALIZADA' and partida_final.vencedor_id:
                campeao = partida_final.vencedor
                vice = partida_final.equipe_a if campeao.id == partida_final.equipe_b_id else partida_final.equipe_b
                terceiro = None
                fase_terceiro = torneio.fases.filter(nome__iexact='3º Lugar').first()
                if fase_terceiro:
                    partida_terceiro = fase_terceiro.partidas.select_related('equipe_a', 'equipe_b', 'vencedor').order_by('ordem_cronograma', 'id').first()
                    if partida_terceiro and partida_terceiro.status == 'FINALIZADA' and partida_terceiro.vencedor_id:
                        terceiro = partida_terceiro.vencedor

                equipes_podio = [campeao, vice]
                if terceiro:
                    equipes_podio.append(terceiro)
                jogadores_por_equipe = {}
                for jogador in Jogador.objects.filter(equipe__in=equipes_podio).order_by('nome'):
                    jogadores_por_equipe.setdefault(jogador.equipe_id, []).append(jogador.nome)

                podio = {
                    'campeao': {
                        'id': campeao.id,
                        'nome': campeao.nome,
                        'jogadores': jogadores_por_equipe.get(campeao.id, []),
                    },
                    'vice': {
                        'id': vice.id,
                        'nome': vice.nome,
                        'jogadores': jogadores_por_equipe.get(vice.id, []),
                    },
                    'terceiro': None,
                }
                if terceiro:
                    podio['terceiro'] = {
                        'id': terceiro.id,
                        'nome': terceiro.nome,
                        'jogadores': jogadores_por_equipe.get(terceiro.id, []),
                    }
                context['campeao'] = podio['campeao']
                context['podio'] = podio

    return context
