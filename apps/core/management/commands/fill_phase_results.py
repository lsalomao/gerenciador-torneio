import random
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import Fase, Partida
from apps.core.services.match_service import adicionar_set
from apps.core.services.wo_service import aplicar_wo


class Command(BaseCommand):
    help = 'Preenche resultados para todas as partidas de uma fase (útil para testes).'

    def add_arguments(self, parser):
        parser.add_argument('--fase-id', type=int, help='ID da fase a preencher')
        parser.add_argument('--ordem', type=int, help='Ordem da fase (ex: 1 para primeira fase)')
        parser.add_argument('--random-winner', action='store_true', help='Escolher vencedor aleatório por partida')
        parser.add_argument('--winner', choices=['A', 'B'], help='Forçar vencedor A ou B (aplica-se a todas as partidas)')
        parser.add_argument('--score-winner', type=int, default=21, help='Pontos do vencedor por set (default: 21)')
        parser.add_argument('--score-loser', type=int, default=10, help='Pontos do perdedor por set (default: 10)')
        parser.add_argument('--apply-wo', action='store_true', help='Marcar W.O. em partidas sem sets (ignora adicionar sets)')

    def handle(self, *args, **options):
        fase = None
        if options.get('fase_id'):
            try:
                fase = Fase.objects.get(pk=options['fase_id'])
            except Fase.DoesNotExist:
                self.stdout.write(self.style.ERROR('Fase não encontrada.'))
                return
        elif options.get('ordem') is not None:
            fase = Fase.objects.filter(ordem=options['ordem']).first()
            if not fase:
                self.stdout.write(self.style.ERROR(f'Nenhuma fase com ordem {options["ordem"]}'))
                return
        else:
            fase = Fase.objects.filter(tipo='GRUPO').order_by('ordem').first()
            if not fase:
                self.stdout.write(self.style.ERROR('Nenhuma fase de grupo encontrada.'))
                return

        partidas = fase.partidas.all()
        total = partidas.count()
        filled = 0

        for partida in partidas:
            if partida.status == 'FINALIZADA':
                continue

            if partida.is_wo and not options.get('apply_wo'):
                # já marcado como WO, pular
                continue

            # decidir vencedor
            if options.get('apply_wo'):
                vencedor_choice = options.get('winner')
                if vencedor_choice == 'A':
                    vencedor = partida.equipe_a
                elif vencedor_choice == 'B':
                    vencedor = partida.equipe_b
                else:
                    vencedor = random.choice([partida.equipe_a, partida.equipe_b])
                aplicar_wo(partida, vencedor)
                filled += 1
                self.stdout.write(self.style.SUCCESS(f'W.O. aplicado: {partida} -> {vencedor}'))
                continue

            # normal flow: criar o menor número de sets para definir vencedor
            regra = partida.fase.regra
            sets_para_vencer = regra.sets_para_vencer

            # selecionar vencedor
            if options.get('winner'):
                vencedor_flag = options.get('winner')
                vencedor_team = partida.equipe_a if vencedor_flag == 'A' else partida.equipe_b
            elif options.get('random_winner'):
                vencedor_team = random.choice([partida.equipe_a, partida.equipe_b])
            else:
                vencedor_team = partida.equipe_a

            # definir pontos
            pw = options.get('score_winner')
            pl = options.get('score_loser')

            # adicionar sets
            try:
                for n in range(1, sets_para_vencer + 1):
                    if vencedor_team.id == partida.equipe_a.id:
                        res = adicionar_set(partida, n, pw, pl)
                    else:
                        res = adicionar_set(partida, n, pl, pw)
                    if not res.get('success'):
                        self.stdout.write(self.style.ERROR(f'Erro ao adicionar set na partida {partida}: {res.get("message")}'))
                        break
                else:
                    filled += 1
                    self.stdout.write(self.style.SUCCESS(f'Partida preenchida: {partida} -> vencedor {vencedor_team}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Exceção ao preencher partida {partida}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Preenchimento concluído: {filled}/{total} partidas processadas na fase {fase.nome} (id={fase.id})'))
