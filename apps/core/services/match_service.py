from typing import Dict, Union
from django.db import transaction
from apps.core.models import Partida, SetResult
from apps.core.services.validation_service import validar_set
from apps.core.services.ranking_service import rankear_grupo
from apps.core.services.advancement_service import processar_finalizacao_partida
from apps.core.services.torneio_status_service import atualizar_status_torneio


def iniciar_partida(partida: Partida) -> Dict:
    if partida.status != 'AGENDADA':
        return {"success": False, "message": "Partida não está em estado AGENDADA"}
    partida.status = 'AO_VIVO'
    partida.save()
    atualizar_status_torneio(partida.fase.torneio)
    return {"success": True, "message": "Partida iniciada"}


def adicionar_set(partida: Partida, numero_set: int, pontos_a: int, pontos_b: int) -> Dict:
    # Bloquear se já finalizada
    if partida.status == 'FINALIZADA':
        return {"success": False, "message": "Não é possível adicionar set em partida finalizada"}

    regra = partida.fase.regra

    # Checar sequência de sets
    ultimo = partida.sets.order_by('-numero_set').first()
    esperado = 1 if ultimo is None else ultimo.numero_set + 1
    if numero_set != esperado:
        return {"success": False, "message": f"Número de set inválido. Esperado {esperado}"}

    max_sets = regra.sets_para_vencer * 2 - 1
    if numero_set > max_sets:
        return {"success": False, "message": "Número de set excede o máximo permitido pela regra"}

    # Validar pontuação
    valid = validar_set(pontos_a, pontos_b, regra)
    if not valid["success"]:
        return {"success": False, "message": f"Set inválido: {valid['message']}"}

    # Não permitir adicionar se já houver vencedor lógico
    if partida.vencedor is not None:
        return {"success": False, "message": "Partida já tem vencedor; não é permitido sets extras"}

    with transaction.atomic():
        set_obj = SetResult.objects.create(
            partida=partida,
            numero_set=numero_set,
            pontos_a=pontos_a,
            pontos_b=pontos_b,
        )

        # Recalcular sets ganhos
        sets = partida.sets.all()
        ganhos_a = 0
        ganhos_b = 0
        for s in sets:
            v = validar_set(s.pontos_a, s.pontos_b, regra)
            if v.get('winner') == 'A':
                ganhos_a += 1
            elif v.get('winner') == 'B':
                ganhos_b += 1

        # Persistir vencedor se atingiu sets_para_vencer
        if ganhos_a >= regra.sets_para_vencer:
            partida.vencedor = partida.equipe_a
            partida.status = 'FINALIZADA'
            partida.save()
            # Recalcular ranking da fase/grupo quando aplicável
            if partida.grupo:
                try:
                    rankear_grupo(partida.grupo)
                except Exception:
                    pass
            # Processar avanço em eliminatórias
            try:
                processar_finalizacao_partida(partida)
            except Exception:
                pass
            atualizar_status_torneio(partida.fase.torneio)
            return {"success": True, "message": "Set adicionado. Partida finalizada (equipe A venceu).", "set": set_obj}

        if ganhos_b >= regra.sets_para_vencer:
            partida.vencedor = partida.equipe_b
            partida.status = 'FINALIZADA'
            partida.save()
            if partida.grupo:
                try:
                    rankear_grupo(partida.grupo)
                except Exception:
                    pass
            try:
                processar_finalizacao_partida(partida)
            except Exception:
                pass
            atualizar_status_torneio(partida.fase.torneio)
            return {"success": True, "message": "Set adicionado. Partida finalizada (equipe B venceu).", "set": set_obj}

        return {"success": True, "message": "Set adicionado", "set": set_obj}
