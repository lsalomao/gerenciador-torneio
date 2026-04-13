from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import Torneio, RegraPontuacao, Fase, Equipe, Grupo, Partida, SetResult
from apps.core.services.ranking_service import rankear_grupo

User = get_user_model()


class RankingServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@u.com', password='pass')
        self.t = Torneio.objects.create(owner=self.user, nome='T', modalidade='Vôlei', local='X', data_inicio='2026-05-01', hora_inicio='08:00')
        self.regra = RegraPontuacao.objects.create(nome='Melhor de 3 21pts', sets_para_vencer=2, pontos_por_set=21, tem_vantagem=True)
        self.fase = Fase.objects.create(torneio=self.t, regra=self.regra, nome='Fase', tipo='GRUPO', ordem=1)
        # criar grupo e 3 equipes
        self.grupo = Grupo.objects.create(fase=self.fase, nome='Grupo A')
        self.e1 = Equipe.objects.create(torneio=self.t, nome='A')
        self.e2 = Equipe.objects.create(torneio=self.t, nome='B')
        self.e3 = Equipe.objects.create(torneio=self.t, nome='C')
        self.grupo.equipes.add(self.e1, self.e2, self.e3)

    def test_rank_por_vitorias(self):
        # A vence B, B vence C, A vence C -> A(2), B(1), C(0)
        p1 = Partida.objects.create(fase=self.fase, grupo=self.grupo, equipe_a=self.e1, equipe_b=self.e2)
        SetResult.objects.create(partida=p1, numero_set=1, pontos_a=21, pontos_b=10)
        SetResult.objects.create(partida=p1, numero_set=2, pontos_a=21, pontos_b=12)
        p1.vencedor = self.e1
        p1.status = 'FINALIZADA'
        p1.save()

        p2 = Partida.objects.create(fase=self.fase, grupo=self.grupo, equipe_a=self.e2, equipe_b=self.e3)
        SetResult.objects.create(partida=p2, numero_set=1, pontos_a=21, pontos_b=18)
        SetResult.objects.create(partida=p2, numero_set=2, pontos_a=21, pontos_b=19)
        p2.vencedor = self.e2
        p2.status = 'FINALIZADA'
        p2.save()

        p3 = Partida.objects.create(fase=self.fase, grupo=self.grupo, equipe_a=self.e1, equipe_b=self.e3)
        SetResult.objects.create(partida=p3, numero_set=1, pontos_a=21, pontos_b=15)
        SetResult.objects.create(partida=p3, numero_set=2, pontos_a=21, pontos_b=10)
        p3.vencedor = self.e1
        p3.status = 'FINALIZADA'
        p3.save()

        ranking = rankear_grupo(self.grupo)
        posições = [r['equipe'].id for r in ranking]
        self.assertEqual(posições, [self.e1.id, self.e2.id, self.e3.id])
