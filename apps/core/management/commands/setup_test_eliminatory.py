from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import Torneio, RegraPontuacao, Fase, Equipe, Grupo, Partida, SetResult


class Command(BaseCommand):
    help = 'Cria um ambiente de teste para disparar a automação de eliminatória'

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write(self.style.SUCCESS('🔧 Criando ambiente de teste...'))
        self.stdout.write('')

        # Criar usuário
        user, _ = User.objects.get_or_create(
            username='teste_auto',
            defaults={'email': 'teste@test.com', 'password': 'test'}
        )
        self.stdout.write(f'  ✓ Usuário: {user.username}')

        # Criar regra
        regra, _ = RegraPontuacao.objects.get_or_create(
            nome='Test - Set único 21pts',
            defaults={'sets_para_vencer': 1, 'pontos_por_set': 21, 'tem_vantagem': True}
        )
        self.stdout.write(f'  ✓ Regra: {regra.nome}')

        # Criar torneio
        torneio, _ = Torneio.objects.get_or_create(
            slug='torneio-teste-auto',
            defaults={
                'owner': user,
                'nome': 'Torneio Teste Auto',
                'modalidade': 'Vôlei de Praia',
                'local': 'Quadra de Teste',
                'data_inicio': '2026-05-01',
                'hora_inicio': '08:00'
            }
        )
        self.stdout.write(f'  ✓ Torneio: {torneio.nome} (ID: {torneio.id})')

        # Criar fase de grupos
        fase_grupo, _ = Fase.objects.get_or_create(
            torneio=torneio,
            ordem=1,
            defaults={
                'regra': regra,
                'nome': 'Fase de Grupos - Teste',
                'tipo': 'GRUPO',
                'equipes_avancam': 1
            }
        )
        self.stdout.write(f'  ✓ Fase de Grupos: {fase_grupo.nome}')

        # Criar fase eliminatória (vazia)
        fase_elim, _ = Fase.objects.get_or_create(
            torneio=torneio,
            ordem=2,
            defaults={
                'regra': regra,
                'nome': 'Eliminatória - Teste',
                'tipo': 'ELIMINATORIA'
            }
        )
        self.stdout.write(f'  ✓ Fase Eliminatória (vazia): {fase_elim.nome}')

        # Criar grupos
        g1, _ = Grupo.objects.get_or_create(
            fase=fase_grupo,
            nome='Grupo A'
        )
        g2, _ = Grupo.objects.get_or_create(
            fase=fase_grupo,
            nome='Grupo B'
        )
        self.stdout.write(f'  ✓ Grupos: {g1.nome}, {g2.nome}')

        # Criar equipes
        equipes = []
        nomes = ['Time A', 'Time B', 'Time C', 'Time D']
        for nome in nomes:
            eq, _ = Equipe.objects.get_or_create(
                torneio=torneio,
                nome=nome
            )
            equipes.append(eq)
        self.stdout.write(f'  ✓ Equipes: {", ".join([e.nome for e in equipes])}')

        # Alocar equipes aos grupos
        g1.equipes.set([equipes[0], equipes[1]])
        g2.equipes.set([equipes[2], equipes[3]])
        self.stdout.write(f'  ✓ Equipes alocadas aos grupos')

        # Criar partidas
        p1, _ = Partida.objects.get_or_create(
            fase=fase_grupo,
            grupo=g1,
            equipe_a=equipes[0],
            equipe_b=equipes[1],
            defaults={'ordem_cronograma': 1}
        )
        p2, _ = Partida.objects.get_or_create(
            fase=fase_grupo,
            grupo=g2,
            equipe_a=equipes[2],
            equipe_b=equipes[3],
            defaults={'ordem_cronograma': 2}
        )
        self.stdout.write(f'  ✓ Partidas: 2 criadas')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ Ambiente pronto para teste!'))
        self.stdout.write('')
        self.stdout.write('Próxima etapa:')
        self.stdout.write(f'  docker compose exec web python manage.py trigger_eliminatory_phase --torneio-id {torneio.id}')
