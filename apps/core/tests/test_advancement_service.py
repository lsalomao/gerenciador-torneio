from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import Torneio, RegraPontuacao, Fase, Equipe, Grupo, Partida, SetResult
from apps.core.services.advancement_service import processar_finalizacao_partida

User = get_user_model()


class AdvancementServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@u.com', password='pass')
        self.t = Torneio.objects.create(
            owner=self.user, nome='T', modalidade='Vôlei', local='X',
            data_inicio='2026-05-01', hora_inicio='08:00'
        )
        self.regra = RegraPontuacao.objects.create(
            nome='Melhor de 3 21pts', sets_para_vencer=2, pontos_por_set=21, tem_vantagem=True
        )
        
        # Criar fase de grupos
        self.fase_grupo = Fase.objects.create(
            torneio=self.t, regra=self.regra, nome='Fase de Grupos',
            tipo='GRUPO', ordem=1, equipes_avancam=1
        )
        
        # Criar fase eliminatória vazia (será populada automaticamente)
        self.fase_elim = Fase.objects.create(
            torneio=self.t, regra=self.regra, nome='Eliminatória',
            tipo='ELIMINATORIA', ordem=2
        )
        
        # Criar 2 grupos com partidas
        self.g1 = Grupo.objects.create(fase=self.fase_grupo, nome='G1')
        self.g2 = Grupo.objects.create(fase=self.fase_grupo, nome='G2')
        
        self.e1 = Equipe.objects.create(torneio=self.t, nome='A')
        self.e2 = Equipe.objects.create(torneio=self.t, nome='B')
        self.e3 = Equipe.objects.create(torneio=self.t, nome='C')
        self.e4 = Equipe.objects.create(torneio=self.t, nome='D')
        
        self.g1.equipes.add(self.e1, self.e2)
        self.g2.equipes.add(self.e3, self.e4)
        
        # Criar partidas
        self.p1 = Partida.objects.create(
            fase=self.fase_grupo, grupo=self.g1, equipe_a=self.e1, equipe_b=self.e2
        )
        self.p2 = Partida.objects.create(
            fase=self.fase_grupo, grupo=self.g2, equipe_a=self.e3, equipe_b=self.e4
        )

    def test_gerar_eliminatoria_automatica_quando_grupos_finalizados(self):
        """Testa se a eliminatória é gerada automaticamente quando todos os grupos finalizam."""
        # Verificar que ainda não tem partidas na eliminatória
        self.assertEqual(self.fase_elim.partidas.count(), 0)
        
        # Finalizar primeira partida
        SetResult.objects.create(partida=self.p1, numero_set=1, pontos_a=21, pontos_b=10)
        SetResult.objects.create(partida=self.p1, numero_set=2, pontos_a=21, pontos_b=12)
        self.p1.vencedor = self.e1
        self.p1.status = 'FINALIZADA'
        self.p1.save()
        processar_finalizacao_partida(self.p1)
        
        # Eliminatória ainda não deve ter partidas (segunda partida não terminou)
        self.assertEqual(self.fase_elim.partidas.count(), 0)
        
        # Finalizar segunda partida
        SetResult.objects.create(partida=self.p2, numero_set=1, pontos_a=21, pontos_b=18)
        SetResult.objects.create(partida=self.p2, numero_set=2, pontos_a=21, pontos_b=19)
        self.p2.vencedor = self.e3
        self.p2.status = 'FINALIZADA'
        self.p2.save()
        processar_finalizacao_partida(self.p2)
        
        # Agora a eliminatória deve ter e com as partidas dos classificados
        self.fase_elim.refresh_from_db()
        self.assertGreater(self.fase_elim.partidas.count(), 0)
        
        # Verificar que as équipes classificadas estão nas partidas
        equipes_nas_partidas = set()
        for partida in self.fase_elim.partidas.all():
            equipes_nas_partidas.add(partida.equipe_a.id)
            equipes_nas_partidas.add(partida.equipe_b.id)
        
        # Deve estar vazio ou com os classificados (neste caso e1 e e3)
        # depending de how seeding works
        self.assertIn(self.e1.id, equipes_nas_partidas)
        self.assertIn(self.e3.id, equipes_nas_partidas)

    def test_nao_gera_eliminatoria_sem_proxima_fase_configurada(self):
        """Testa que nada acontece se não há próxima fase eliminatória configurada."""
        # Remover a fase eliminatória
        self.fase_elim.delete()
        
        # Finalizar ambas as partidas
        SetResult.objects.create(partida=self.p1, numero_set=1, pontos_a=21, pontos_b=10)
        SetResult.objects.create(partida=self.p1, numero_set=2, pontos_a=21, pontos_b=12)
        self.p1.vencedor = self.e1
        self.p1.status = 'FINALIZADA'
        self.p1.save()
        processar_finalizacao_partida(self.p1)
        
        SetResult.objects.create(partida=self.p2, numero_set=1, pontos_a=21, pontos_b=18)
        SetResult.objects.create(partida=self.p2, numero_set=2, pontos_a=21, pontos_b=19)
        self.p2.vencedor = self.e3
        self.p2.status = 'FINALIZADA'
        self.p2.save()
        
        # Isso não deve lançar erro, apenas retornar silenciosamente
        processar_finalizacao_partida(self.p2)
