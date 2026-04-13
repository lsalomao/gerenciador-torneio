import random
from typing import List, Dict, Tuple

from django.db import transaction

from apps.core.models import Fase, Grupo, Partida, Equipe
from apps.core.services.ranking_service import rankear_grupo


def _verificar_grupos_finalizados(fase: Fase) -> Tuple[bool, str]:
    grupos = fase.grupos.all()
    for g in grupos:
        # verificar se todas as partidas do grupo estão finalizadas
        if g.partidas.exclude(status='FINALIZADA').exists():
            return False, f"Existem partidas não finalizadas no grupo {g.nome}"
    return True, 'OK'


def obter_classificados_da_fase(fase: Fase) -> List[Equipe]:
    """Retorna lista de equipes classificadas (por grupo) baseado em `equipes_avancam`."""
    classificados = []
    for grupo in fase.grupos.all():
        ranking = rankear_grupo(grupo)
        n = fase.equipes_avancam
        top = [r['equipe'] for r in ranking[:n]]
        classificados.extend(top)
    return classificados


def calcular_seed(classificados: List[Equipe], fase_grupo: Fase) -> List[Dict]:
    """Calcula o seed global dos classificados.

    Usa critérios: %vitórias, média saldo de sets por jogo, média saldo de pontos por jogo.
    """
    # reutilizar rankear_grupo para obter stats por grupo
    seed = []
    for equipe in classificados:
        # buscar grupo onde a equipe está na fase anterior
        grupo = fase_grupo.grupos.filter(equipes=equipe).first()
        if not grupo:
            continue
        stats = rankear_grupo(grupo)
        entrada = next((s for s in stats if s['equipe'].id == equipe.id), None)
        if not entrada:
            continue

        jogos = entrada['jogos'] or 1
        pct_vitorias = entrada['vitorias'] / jogos
        avg_saldo_sets = entrada['saldo_sets'] / jogos
        avg_saldo_pontos = entrada['saldo_pontos'] / jogos

        seed.append({
            'equipe': equipe,
            'pct_vitorias': pct_vitorias,
            'avg_saldo_sets': avg_saldo_sets,
            'avg_saldo_pontos': avg_saldo_pontos,
        })

    # ordenar
    random.shuffle(seed)  # para desempates aleatórios estáveis
    seed.sort(key=lambda s: (-s['pct_vitorias'], -s['avg_saldo_sets'], -s['avg_saldo_pontos']))
    return seed


def _pair_seeds(seed_list: List[Dict]) -> List[Tuple[Dict, Dict]]:
    n = len(seed_list)
    pairs = []
    for i in range(n // 2):
        pairs.append((seed_list[i], seed_list[n - 1 - i]))
    return pairs


@transaction.atomic
def gerar_eliminatoria(fase_grupo_id: int, nome_fase: str = None, fase_existente: Fase = None) -> Dict:
    fase_grupo = Fase.objects.get(pk=fase_grupo_id)

    ok, msg = _verificar_grupos_finalizados(fase_grupo)
    if not ok:
        return {'success': False, 'message': msg}

    classificados = obter_classificados_da_fase(fase_grupo)
    if not classificados:
        return {'success': False, 'message': 'Nenhum classificado encontrado'}

    seed = calcular_seed(classificados, fase_grupo)

    # usar fase existente ou criar nova
    if fase_existente:
        fase_elim = fase_existente
    else:
        nome = nome_fase or f"Eliminatória — {fase_grupo.torneio.nome}"
        fase_elim = Fase.objects.create(torneio=fase_grupo.torneio, regra=fase_grupo.regra, nome=nome, tipo='ELIMINATORIA', ordem=fase_grupo.ordem+1)

    # gerar partidas das quartas/primeira rodada
    pairs = _pair_seeds(seed)
    ordem = 1
    for a, b in pairs:
        Partida.objects.create(
            fase=fase_elim,
            equipe_a=a['equipe'],
            equipe_b=b['equipe'],
            ordem_cronograma=ordem
        )
        ordem += 1

    return {'success': True, 'message': 'Eliminatória gerada', 'fase_eliminatoria_id': fase_elim.id}
