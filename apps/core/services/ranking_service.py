from typing import List, Dict
from collections import defaultdict

from apps.core.models import Grupo, Partida, SetResult, Equipe


def _init_stats(equipe: Equipe) -> Dict:
    return {
        'equipe': equipe,
        'jogos': 0,
        'vitorias': 0,
        'derrotas': 0,
        'sets_ganhos': 0,
        'sets_perdidos': 0,
        'saldo_sets': 0,
        'pontos_feitos': 0,
        'pontos_tomados': 0,
        'saldo_pontos': 0,
    }


def calcular_estatisticas_grupo(grupo: Grupo) -> List[Dict]:
    """Calcula estatísticas por equipe para todas as partidas FINALIZADAS do grupo."""
    equipes = list(grupo.equipes.all())
    stats = {e.id: _init_stats(e) for e in equipes}

    partidas = grupo.partidas.filter(status='FINALIZADA').prefetch_related('sets', 'fase__regra')

    for partida in partidas:
        # identificar equipes
        a = partida.equipe_a
        b = partida.equipe_b

        # preparar base
        s_a = stats[a.id]
        s_b = stats[b.id]

        # contabiliza jogos
        s_a['jogos'] += 1
        s_b['jogos'] += 1

        if partida.is_wo:
            # W.O.: atribuir placar lógico baseado na regra da fase
            pontos = partida.fase.regra.pontos_por_set
            sets_para_vencer = partida.fase.regra.sets_para_vencer

            # vencedor_wo pode ser None, fallback para partida.vencedor
            vencedor = partida.vencedor_wo or partida.vencedor
            if not vencedor:
                continue

            if vencedor.id == a.id:
                s_a['vitorias'] += 1
                s_b['derrotas'] += 1
                s_a['sets_ganhos'] += sets_para_vencer
                s_b['sets_perdidos'] += sets_para_vencer
                s_a['pontos_feitos'] += pontos * sets_para_vencer
                s_b['pontos_tomados'] += pontos * sets_para_vencer
                s_b['pontos_feitos'] += 0
                s_a['pontos_tomados'] += 0
            else:
                s_b['vitorias'] += 1
                s_a['derrotas'] += 1
                s_b['sets_ganhos'] += sets_para_vencer
                s_a['sets_perdidos'] += sets_para_vencer
                s_b['pontos_feitos'] += pontos * sets_para_vencer
                s_a['pontos_tomados'] += pontos * sets_para_vencer
            continue

        # Jogos normais: iterar sets existentes
        sets = list(partida.sets.all())
        ganhos_a = ganhos_b = 0
        pts_a = pts_b = 0
        for s in sets:
            pts_a += s.pontos_a
            pts_b += s.pontos_b
            if s.pontos_a > s.pontos_b:
                ganhos_a += 1
            elif s.pontos_b > s.pontos_a:
                ganhos_b += 1

        # atribui vitoria/derrota
        if ganhos_a > ganhos_b:
            s_a['vitorias'] += 1
            s_b['derrotas'] += 1
        elif ganhos_b > ganhos_a:
            s_b['vitorias'] += 1
            s_a['derrotas'] += 1

        s_a['sets_ganhos'] += ganhos_a
        s_a['sets_perdidos'] += ganhos_b
        s_b['sets_ganhos'] += ganhos_b
        s_b['sets_perdidos'] += ganhos_a

        s_a['pontos_feitos'] += pts_a
        s_a['pontos_tomados'] += pts_b
        s_b['pontos_feitos'] += pts_b
        s_b['pontos_tomados'] += pts_a

    # calcular saldos
    resultado = []
    for e_id, s in stats.items():
        s['saldo_sets'] = s['sets_ganhos'] - s['sets_perdidos']
        s['saldo_pontos'] = s['pontos_feitos'] - s['pontos_tomados']
        resultado.append(s)

    return resultado


def _confronto_direto_miniranking(grupo: Grupo, equipes_ids: List[int]) -> List[int]:
    """Retorna lista de equipe ids ordenada pelo confronto direto (mini-tabela).

    Critérios simples: vitórias no mini-grupo, saldo de sets, saldo de pontos.
    """
    mini_stats = {eid: {
        'equipe_id': eid,
        'vitorias': 0,
        'sets_ganhos': 0,
        'sets_perdidos': 0,
        'pontos_feitos': 0,
        'pontos_tomados': 0,
    } for eid in equipes_ids}

    partidas = grupo.partidas.filter(status='FINALIZADA')
    for p in partidas:
        a_id = p.equipe_a.id
        b_id = p.equipe_b.id
        if a_id not in equipes_ids or b_id not in equipes_ids:
            continue

        if p.is_wo:
            pontos = p.fase.regra.pontos_por_set * p.fase.regra.sets_para_vencer
            vencedor = p.vencedor_wo or p.vencedor
            if not vencedor:
                continue
            if vencedor.id == a_id:
                mini_stats[a_id]['vitorias'] += 1
                mini_stats[a_id]['sets_ganhos'] += p.fase.regra.sets_para_vencer
                mini_stats[a_id]['pontos_feitos'] += pontos
                mini_stats[b_id]['sets_perdidos'] += p.fase.regra.sets_para_vencer
                mini_stats[b_id]['pontos_tomados'] += pontos
            else:
                mini_stats[b_id]['vitorias'] += 1
                mini_stats[b_id]['sets_ganhos'] += p.fase.regra.sets_para_vencer
                mini_stats[b_id]['pontos_feitos'] += pontos
                mini_stats[a_id]['sets_perdidos'] += p.fase.regra.sets_para_vencer
                mini_stats[a_id]['pontos_tomados'] += pontos
            continue

        # normal
        ganhos_a = ganhos_b = 0
        pts_a = pts_b = 0
        for s in p.sets.all():
            pts_a += s.pontos_a
            pts_b += s.pontos_b
            if s.pontos_a > s.pontos_b:
                ganhos_a += 1
            elif s.pontos_b > s.pontos_a:
                ganhos_b += 1

        if ganhos_a > ganhos_b:
            mini_stats[a_id]['vitorias'] += 1
        elif ganhos_b > ganhos_a:
            mini_stats[b_id]['vitorias'] += 1

        mini_stats[a_id]['sets_ganhos'] += ganhos_a
        mini_stats[a_id]['sets_perdidos'] += ganhos_b
        mini_stats[b_id]['sets_ganhos'] += ganhos_b
        mini_stats[b_id]['sets_perdidos'] += ganhos_a

        mini_stats[a_id]['pontos_feitos'] += pts_a
        mini_stats[a_id]['pontos_tomados'] += pts_b
        mini_stats[b_id]['pontos_feitos'] += pts_b
        mini_stats[b_id]['pontos_tomados'] += pts_a

    # ordenar por: vitorias desc, saldo_sets desc, saldo_pontos desc
    def key_fn(x):
        return (
            -mini_stats[x]['vitorias'],
            -(mini_stats[x]['sets_ganhos'] - mini_stats[x]['sets_perdidos']),
            -((mini_stats[x]['pontos_feitos'] - mini_stats[x]['pontos_tomados']))
        )

    ordenado = sorted(equipes_ids, key=key_fn)
    return ordenado


def rankear_grupo(grupo: Grupo) -> List[Dict]:
    """Retorna lista ordenada com as estatísticas e posição por equipe.

    Aplica critérios na ordem: vitórias, saldo_sets, saldo_pontos, confronto direto.
    """
    stats = calcular_estatisticas_grupo(grupo)

    # mapa id->stats
    mapa = {s['equipe'].id: s for s in stats}

    # ordenação inicial por vitórias, saldo_sets, saldo_pontos
    def key_global(s):
        return (-s['vitorias'], -s['saldo_sets'], -s['saldo_pontos'])

    stats.sort(key=key_global)

    # resolver empates aplicando confronto direto quando necessário
    i = 0
    resultado_final = []
    pos = 1
    while i < len(stats):
        # encontrar bloco de empate por (vitorias, saldo_sets, saldo_pontos)
        bloco = [stats[i]]
        j = i + 1
        while j < len(stats) and (
            stats[j]['vitorias'] == stats[i]['vitorias'] and
            stats[j]['saldo_sets'] == stats[i]['saldo_sets'] and
            stats[j]['saldo_pontos'] == stats[i]['saldo_pontos']
        ):
            bloco.append(stats[j])
            j += 1

        if len(bloco) == 1:
            s = bloco[0]
            s_out = s.copy()
            s_out['posicao'] = pos
            resultado_final.append(s_out)
            pos += 1
        else:
            # aplicar confronto direto entre ids do bloco
            ids = [b['equipe'].id for b in bloco]
            ordem_ids = _confronto_direto_miniranking(grupo, ids)
            for eid in ordem_ids:
                s = mapa[eid]
                s_out = s.copy()
                s_out['posicao'] = pos
                resultado_final.append(s_out)
                pos += 1

        i = j

    return resultado_final
