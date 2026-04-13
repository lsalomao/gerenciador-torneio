from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import Torneio, RegraPontuacao, Fase, Equipe, Partida
from apps.core.services.validation_service import validar_set
from apps.core.services.match_service import iniciar_partida, adicionar_set
from apps.core.services.wo_service import aplicar_wo

User = get_user_model()


class MatchServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@u.com', password='pass')
        self.t = Torneio.objects.create(owner=self.user, nome='T', modalidade='Vôlei', local='X', data_inicio='2026-05-01', hora_inicio='08:00')
        self.regra = RegraPontuacao.objects.create(nome='Melhor de 3 21pts', sets_para_vencer=2, pontos_por_set=21, tem_vantagem=True)
        self.fase = Fase.objects.create(torneio=self.t, regra=self.regra, nome='Fase', tipo='GRUPO', ordem=1)
        self.e1 = Equipe.objects.create(torneio=self.t, nome='A')
        self.e2 = Equipe.objects.create(torneio=self.t, nome='B')
        self.partida = Partida.objects.create(fase=self.fase, equipe_a=self.e1, equipe_b=self.e2)

    def test_validar_set_vantagem_invalido(self):
        res = validar_set(21, 20, self.regra)
        self.assertFalse(res['success'])

    def test_validar_set_vantagem_valido(self):
        res = validar_set(22, 20, self.regra)
        self.assertTrue(res['success'])
        self.assertEqual(res['winner'], 'A')

    def test_iniciar_e_adicionar_sets_e_finalizar(self):
        r = iniciar_partida(self.partida)
        self.assertTrue(r['success'])

        a1 = adicionar_set(self.partida, 1, 21, 10)
        self.assertTrue(a1['success'])
        self.partida.refresh_from_db()
        self.assertEqual(self.partida.status, 'AO_VIVO')

        a2 = adicionar_set(self.partida, 2, 21, 18)
        self.assertTrue(a2['success'])
        # Após dois sets ganhos por equipe A, partida deve finalizar
        self.partida.refresh_from_db()
        self.assertEqual(self.partida.status, 'FINALIZADA')
        self.assertEqual(self.partida.vencedor, self.e1)

    def test_aplicar_wo_sem_sets(self):
        res = aplicar_wo(self.partida, self.e2)
        self.assertTrue(res['success'])
        self.partida.refresh_from_db()
        self.assertTrue(self.partida.is_wo)
        self.assertEqual(self.partida.vencedor, self.e2)

    def test_aplicar_wo_com_sets_bloqueado(self):
        # criar um set manualmente via model
        from apps.core.models import SetResult
        SetResult.objects.create(partida=self.partida, numero_set=1, pontos_a=10, pontos_b=21)
        res = aplicar_wo(self.partida, self.e2)
        self.assertFalse(res['success'])
