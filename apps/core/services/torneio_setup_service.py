"""
Service para criação automática de fases ao criar um torneio.

Configura as fases de um torneio baseado em quantidade_times e formato_torneio.
"""
from apps.core.models import Fase


# Mapeamento: (quantidade_times, formato) -> lista de fases
# Cada tupla é (nome_da_fase, tipo, ordem, equipes_avancam)
FASES_CONFIG = {
    # Só Eliminatória
    (4, 'so_eliminatoria'): [
        ('Semi-Final', 'ELIMINATORIA', 1, None),
        ('3º Lugar', 'ELIMINATORIA', 2, None),
        ('Final', 'ELIMINATORIA', 3, None),
    ],
    (8, 'so_eliminatoria'): [
        ('Quartas de Final', 'ELIMINATORIA', 1, None),
        ('Semi-Final', 'ELIMINATORIA', 2, None),
        ('3º Lugar', 'ELIMINATORIA', 3, None),
        ('Final', 'ELIMINATORIA', 4, None),
    ],
    (16, 'so_eliminatoria'): [
        ('Oitavas de Final', 'ELIMINATORIA', 1, None),
        ('Quartas de Final', 'ELIMINATORIA', 2, None),
        ('Semi-Final', 'ELIMINATORIA', 3, None),
        ('3º Lugar', 'ELIMINATORIA', 4, None),
        ('Final', 'ELIMINATORIA', 5, None),
    ],
    (32, 'so_eliminatoria'): [
        ('Dezesseis Avos', 'ELIMINATORIA', 1, None),
        ('Oitavas de Final', 'ELIMINATORIA', 2, None),
        ('Quartas de Final', 'ELIMINATORIA', 3, None),
        ('Semi-Final', 'ELIMINATORIA', 4, None),
        ('3º Lugar', 'ELIMINATORIA', 5, None),
        ('Final', 'ELIMINATORIA', 6, None),
    ],
    # Grupos + Eliminatória
    (4, 'grupos_e_eliminatoria'): [
        ('Fase de Grupos', 'GRUPO', 1, 2),
        ('Final', 'ELIMINATORIA', 2, None),
    ],
    (8, 'grupos_e_eliminatoria'): [
        ('Fase de Grupos', 'GRUPO', 1, 2),
        ('Semi-Final', 'ELIMINATORIA', 2, None),
        ('3º Lugar', 'ELIMINATORIA', 3, None),
        ('Final', 'ELIMINATORIA', 4, None),
    ],
    (16, 'grupos_e_eliminatoria'): [
        ('Fase de Grupos', 'GRUPO', 1, 2),
        ('Quartas de Final', 'ELIMINATORIA', 2, None),
        ('Semi-Final', 'ELIMINATORIA', 3, None),
        ('3º Lugar', 'ELIMINATORIA', 4, None),
        ('Final', 'ELIMINATORIA', 5, None),
    ],
    (32, 'grupos_e_eliminatoria'): [
        ('Fase de Grupos', 'GRUPO', 1, 2),
        ('Oitavas de Final', 'ELIMINATORIA', 2, None),
        ('Quartas de Final', 'ELIMINATORIA', 3, None),
        ('Semi-Final', 'ELIMINATORIA', 4, None),
        ('3º Lugar', 'ELIMINATORIA', 5, None),
        ('Final', 'ELIMINATORIA', 6, None),
    ],
}


def criar_fases_torneio(torneio):
    """
    Cria automaticamente as fases de um torneio baseado na configuração.
    
    Args:
        torneio: Instância de Torneio já salva no banco
        
    Returns:
        dict com resultado da operação:
            {
                'sucesso': bool,
                'fases_criadas': list de Fase objects criados,
                'aviso': str opcional com avisos (ex: config incomum),
                'erro': str opcional com mensagem de erro
            }
    """
    
    # Validações
    if not torneio.quantidade_times or not torneio.formato_torneio:
        return {
            'sucesso': False,
            'fases_criadas': [],
            'erro': 'Quantidade de times e formato são obrigatórios'
        }
    
    config_key = (torneio.quantidade_times, torneio.formato_torneio)
    
    if config_key not in FASES_CONFIG:
        return {
            'sucesso': False,
            'fases_criadas': [],
            'erro': f'Configuração inválida: {torneio.quantidade_times} times + {torneio.formato_torneio}'
        }
    
    # Avisos para configurações incomuns
    aviso = None
    if config_key == (4, 'grupos_e_eliminatoria'):
        aviso = 'Aviso: 4 times em grupos resulta em apenas a Final. Isso é válido mas incomum.'
    
    # Criar as fases
    fases_config = FASES_CONFIG[config_key]
    fases_criadas = []
    
    for nome, tipo, ordem, equipes_avancam in fases_config:
        fase = Fase.objects.create(
            torneio=torneio,
            nome=nome,
            tipo=tipo,
            ordem=ordem,
            equipes_avancam=equipes_avancam or 0,  # 0 para eliminatórias
            regra=None  # O ADM vincula depois
        )
        fases_criadas.append(fase)
    
    resultado = {
        'sucesso': True,
        'fases_criadas': fases_criadas,
    }
    
    if aviso:
        resultado['aviso'] = aviso
    
    return resultado


def obter_fases_preview(quantidade_times, formato_torneio):
    """
    Retorna a lista de fases que serão criadas para exibição de preview.
    Útil para JavaScript no frontend.
    
    Args:
        quantidade_times: int (4, 8, 16, 32)
        formato_torneio: str ('grupos_e_eliminatoria' ou 'so_eliminatoria')
        
    Returns:
        list de strings com nomes das fases, ou [] se config inválida
    """
    config_key = (quantidade_times, formato_torneio)
    
    if config_key not in FASES_CONFIG:
        return []
    
    fases_config = FASES_CONFIG[config_key]
    return [nome for nome, _, _, _ in fases_config]
