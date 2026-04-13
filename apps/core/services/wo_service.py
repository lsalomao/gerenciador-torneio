from typing import Dict
from apps.core.models import Partida, Equipe
from apps.core.services.ranking_service import rankear_grupo
from apps.core.services.advancement_service import processar_finalizacao_partida


def aplicar_wo(partida: Partida, vencedor: Equipe) -> Dict:
    # Não permitir aplicar W.O. em partida já finalizada
    if partida.status == 'FINALIZADA':
        return {"success": False, "message": "Partida já finalizada"}

    # Se já houver sets lançados, bloquear por segurança
    if partida.sets.exists():
        return {"success": False, "message": "Existem sets lançados; remova-os antes de aplicar W.O."}

    partida.is_wo = True
    partida.vencedor_wo = vencedor
    partida.vencedor = vencedor
    partida.status = 'FINALIZADA'
    partida.save()

    # Recalcular ranking do grupo se aplicavel
    if partida.grupo:
        try:
            rankear_grupo(partida.grupo)
        except Exception:
            pass

    try:
        processar_finalizacao_partida(partida)
    except Exception:
        pass

    return {"success": True, "message": "W.O. aplicado e partida finalizada", "vencedor": vencedor.id}
