from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import Torneio, RegraPontuacao, Fase, Equipe, Grupo, Partida, SetResult
from apps.core.services.bracket_service import gerar_eliminatoria

User = get_user_model()


class BracketServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@u.com', password='pass')
        self.t = Torneio.objects.create(owner=self.user, nome='T', modalidade='Vôlei', local='X', data_inicio='2026-05-01', hora_inicio='08:00')
        self.regra = RegraPontuacao.objects.create(nome='Melhor de 3 21pts', sets_para_vencer=2, pontos_por_set=21, tem_vantagem=True)
        self.fase = Fase.objects.create(torneio=self.t, regra=self.regra, nome='FaseGrupos', tipo='GRUPO', ordem=1)

        # criar 2 grupos com 2 equipes cada um e partidas finalizadas
        self.g1 = Grupo.objects.create(fase=self.fase, nome='G1')
        self.g2 = Grupo.objects.create(fase=self.fase, nome='G2')

        self.e1 = Equipe.objects.create(torneio=self.t, nome='A')
        self.e2 = Equipe.objects.create(torneio=self.t, nome='B')
        self.e3 = Equipe.objects.create(torneio=self.t, nome='C')
        self.e4 = Equipe.objects.create(torneio=self.t, nome='D')

        self.g1.equipes.add(self.e1, self.e2)
        self.g2.equipes.add(self.e3, self.e4)

        p1 = Partida.objects.create(fase=self.fase, grupo=self.g1, equipe_a=self.e1, equipe_b=self.e2)
        SetResult.objects.create(partida=p1, numero_set=1, pontos_a=21, pontos_b=10)
        SetResult.objects.create(partida=p1, numero_set=2, pontos_a=21, pontos_b=12)
        p1.vencedor = self.e1
        p1.status = 'FINALIZADA'
        p1.save()

        p2 = Partida.objects.create(fase=self.fase, grupo=self.g2, equipe_a=self.e3, equipe_b=self.e4)
        SetResult.objects.create(partida=p2, numero_set=1, pontos_a=21, pontos_b=18)
        SetResult.objects.create(partida=p2, numero_set=2, pontos_a=21, pontos_b=19)
        p2.vencedor = self.e3
        p2.status = 'FINALIZADA'
        p2.save()

    def test_gerar_eliminatoria_sucesso(self):
        resultado = gerar_eliminatoria(self.fase.id, nome_fase='Quartas Test')
        self.assertTrue(resultado['success'])
        self.assertIn('fase_eliminatoria_id', resultado)
