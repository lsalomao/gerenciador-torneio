from typing import Optional, Dict

from apps.core.models import RegraPontuacao


def validar_set(pontos_a: int, pontos_b: int, regra: RegraPontuacao) -> Dict:
    """Valida um set segundo a regra de pontuação.

    Retorna dict com keys: success (bool), message (str), winner ('A'|'B'|None)
    """
    pontos_para_fechar = regra.pontos_por_set
    tem_vantagem = regra.tem_vantagem
    limite = regra.limite_pontos_diretos

    # Empates não são permitidos
    if pontos_a == pontos_b:
        return {"success": False, "message": "Empate não permitido", "winner": None}

    # Quem primeiro atingir condição vence
    def vence(a, b):
        # limite direto vence independentemente da diferença
        if limite is not None and a >= limite:
            return True
        # Caso alcance pontos para fechar
        if a < pontos_para_fechar:
            return False
        if tem_vantagem:
            return (a - b) >= 2
        return True

    a_vence = vence(pontos_a, pontos_b)
    b_vence = vence(pontos_b, pontos_a)

    # Consistência: apenas um pode vencer
    if a_vence and not b_vence:
        return {"success": True, "message": "Set válido", "winner": "A"}
    if b_vence and not a_vence:
        return {"success": True, "message": "Set válido", "winner": "B"}

    return {"success": False, "message": "Pontuação inválida para a regra", "winner": None}
