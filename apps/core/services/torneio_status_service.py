from django.utils import timezone


STATUS_FLOW = ['CRIACAO', 'INSCRICOES', 'ANDAMENTO', 'ENCERRADO']


def _status_index(status):
    try:
        return STATUS_FLOW.index(status)
    except ValueError:
        return 0


def _deve_encerrar(torneio):
    ultima_fase = torneio.fases.order_by('-ordem').first()
    if not ultima_fase:
        return False
    partidas_ultima_fase = ultima_fase.partidas.all()
    if not partidas_ultima_fase.exists():
        return False
    return not partidas_ultima_fase.exclude(status='FINALIZADA').exists()


def _deve_andamento(torneio):
    return torneio.fases.filter(partidas__isnull=False).exists()


def _deve_inscricoes(torneio):
    if torneio.equipes.exists():
        return True
    hoje = timezone.localdate()
    return hoje >= torneio.data_inicio


def calcular_status_automatico_torneio(torneio):
    if _deve_encerrar(torneio):
        return 'ENCERRADO'
    if _deve_andamento(torneio):
        return 'ANDAMENTO'
    if _deve_inscricoes(torneio):
        return 'INSCRICOES'
    return 'CRIACAO'


def atualizar_status_torneio(torneio):
    novo_status = calcular_status_automatico_torneio(torneio)
    if _status_index(novo_status) < _status_index(torneio.status):
        return torneio.status
    if torneio.status != novo_status:
        torneio.status = novo_status
        torneio.save(update_fields=['status'])
    return torneio.status
