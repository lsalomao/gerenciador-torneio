from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.core.models import Torneio, Fase, Partida, SetResult
from apps.core.services.advancement_service import processar_finalizacao_partida


class Command(BaseCommand):
    help = '''Dispara a geração automática da Fase Eliminatória finalizando as partidas de grupos.
    
    Uso:
    - python manage.py trigger_eliminatory_phase --torneio-id 1
      Finaliza um torneio específico
      
    - python manage.py trigger_eliminatory_phase --torneio-id 1 --dry-run
      Mostra o que seria feito sem executar
    '''

    def add_arguments(self, parser):
        parser.add_argument(
            '--torneio-id',
            type=int,
            required=True,
            help='ID do torneio a processar'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a execução sem fazer alterações'
        )
        parser.add_argument(
            '--grupo-id',
            type=int,
            help='Opcional: ID do grupo específico a finalizar (senão finaliza todos)'
        )

    def handle(self, *args, **options):
        torneio_id = options['torneio_id']
        dry_run = options['dry_run']
        grupo_id = options.get('grupo_id')

        try:
            torneio = Torneio.objects.get(pk=torneio_id)
        except Torneio.DoesNotExist:
            raise CommandError(f'Torneio com ID {torneio_id} não encontrado')

        self.stdout.write(f'Processando torneio: {torneio.nome}')
        self.stdout.write(f'Modo: {"DRY-RUN (simulação)" if dry_run else "EXECUÇÃO"}')
        self.stdout.write('')

        # Encontrar fase de grupos
        fase_grupo = Fase.objects.filter(torneio=torneio, tipo='GRUPO').first()
        if not fase_grupo:
            raise CommandError(f'Nenhuma fase de GRUPO encontrada para {torneio.nome}')

        self.stdout.write(self.style.SUCCESS(f'✓ Fase de Grupos encontrada: {fase_grupo.nome}'))
        self.stdout.write('')

        # Filtrar grupos (opcionalmente)
        grupos = fase_grupo.grupos.all()
        if grupo_id:
            grupos = grupos.filter(pk=grupo_id)
            if not grupos.exists():
                raise CommandError(f'Grupo com ID {grupo_id} não encontrado')

        # Listar partidas não finalizadas
        partidas_pendentes = []
        for grupo in grupos:
            pendentes = grupo.partidas.exclude(status='FINALIZADA')
            partidas_pendentes.extend(list(pendentes))

        if not partidas_pendentes:
            self.stdout.write(self.style.WARNING('⚠ Nenhuma partida pendente encontrada'))
            return

        self.stdout.write(f'Partidas pendentes a finalizar: {len(partidas_pendentes)}')
        self.stdout.write('')

        for partida in partidas_pendentes:
            self.stdout.write(f'  • {partida.equipe_a.nome} vs {partida.equipe_b.nome}')

        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN: Nenhuma alteração será feita'))
            return

        # Confirmar execução
        self.stdout.write(self.style.WARNING('Confirmando execução...'))
        resposta = input('Deseja continuar? (s/n): ').lower().strip()
        if resposta != 's':
            self.stdout.write('Operação cancelada')
            return

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Executando...'))
        self.stdout.write('')

        try:
            with transaction.atomic():
                finalizadas = 0
                for partida in partidas_pendentes:
                    # Criar sets test (vitória fácil: 2-0)
                    regra = partida.fase.regra
                    sets_para_vencer = regra.sets_para_vencer or 1

                    for i in range(1, sets_para_vencer + 1):
                        SetResult.objects.create(
                            partida=partida,
                            numero_set=i,
                            pontos_a=21,
                            pontos_b=10
                        )

                    # Marcar vencedor
                    partida.vencedor = partida.equipe_a
                    partida.status = 'FINALIZADA'
                    partida.save()

                    self.stdout.write(
                        f'  ✓ Finalizada: {partida.equipe_a.nome} (2x0) vs {partida.equipe_b.nome}'
                    )

                    # Processar finalização (dispara automação)
                    processar_finalizacao_partida(partida)
                    finalizadas += 1

                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS(f'✓ {finalizadas} partidas finalizadas'))

                # Verificar se eliminatória foi gerada
                fase_elim = Fase.objects.filter(
                    torneio=torneio,
                    tipo='ELIMINATORIA',
                    ordem__gt=fase_grupo.ordem
                ).order_by('ordem').first()

                if fase_elim and fase_elim.partidas.exists():
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Fase Eliminatória gerada automaticamente: {fase_elim.nome}'
                        )
                    )
                    self.stdout.write(
                        f'  Confrontos criados: {fase_elim.partidas.count()}'
                    )
                    self.stdout.write('')
                    for p in fase_elim.partidas.all():
                        self.stdout.write(f'    • {p.equipe_a.nome} vs {p.equipe_b.nome}')
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            '⚠ Fase Eliminatória NÃO foi gerada (pré-requisitos não atendidos)'
                        )
                    )

        except Exception as e:
            raise CommandError(f'Erro durante execução: {str(e)}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ Operação concluída com sucesso'))
