from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import Torneio, Fase, Grupo, Equipe, RegraPontuacao, Partida, SetResult
from apps.core.services.phase_reset_service import (
    pode_resetar_fase,
    resetar_fase,
    obter_estatisticas_fase,
)
from apps.core.services.schedule_service import gerar_round_robin_fase

User = get_user_model()


class PhaseResetServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.torneio = Torneio.objects.create(
            owner=self.user,
            nome='Torneio Teste',
            modalidade='Vôlei de Praia',
            local='Praia Central',
            data_inicio='2026-05-01',
            hora_inicio='08:00',
            jogadores_por_equipe=2
        )
        
        self.regra = RegraPontuacao.objects.create(
            nome='Set Único 21pts',
            sets_para_vencer=1,
            pontos_por_set=21,
            tem_vantagem=True
        )
        
        self.fase_grupo = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Fase de Grupos',
            tipo='GRUPO',
            ordem=1
        )
        
        self.grupo_a = Grupo.objects.create(
            fase=self.fase_grupo,
            nome='Grupo A'
        )
        
        self.equipes = []
        for i in range(1, 5):
            equipe = Equipe.objects.create(
                torneio=self.torneio,
                nome=f'Equipe {i}'
            )
            self.equipes.append(equipe)
            self.grupo_a.equipes.add(equipe)
        
        gerar_round_robin_fase(self.fase_grupo.id)
    
    def test_pode_resetar_sem_partidas_finalizadas(self):
        pode, mensagem = pode_resetar_fase(self.fase_grupo.id)
        
        self.assertTrue(pode)
        self.assertEqual(mensagem, "Fase pode ser resetada")
    
    def test_bloqueia_reset_com_partidas_finalizadas(self):
        partida = Partida.objects.filter(fase=self.fase_grupo).first()
        partida.status = 'FINALIZADA'
        partida.vencedor = partida.equipe_a
        partida.save()
        
        pode, mensagem = pode_resetar_fase(self.fase_grupo.id)
        
        self.assertFalse(pode)
        self.assertIn('1 partida(s) já foram finalizadas', mensagem)
        self.assertIn(partida.equipe_a.nome, mensagem)
        self.assertIn(partida.equipe_b.nome, mensagem)
    
    def test_bloqueia_reset_com_multiplas_finalizadas(self):
        partidas = Partida.objects.filter(fase=self.fase_grupo)[:3]
        
        for partida in partidas:
            partida.status = 'FINALIZADA'
            partida.vencedor = partida.equipe_a
            partida.save()
        
        pode, mensagem = pode_resetar_fase(self.fase_grupo.id)
        
        self.assertFalse(pode)
        self.assertIn('3 partida(s) já foram finalizadas', mensagem)
    
    def test_resetar_apaga_partidas(self):
        count_antes = Partida.objects.filter(fase=self.fase_grupo).count()
        self.assertGreater(count_antes, 0)
        
        resultado = resetar_fase(self.fase_grupo.id)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['partidas_removidas'], count_antes)
        
        count_depois = Partida.objects.filter(fase=self.fase_grupo).count()
        self.assertEqual(count_depois, 0)
    
    def test_resetar_apaga_sets_por_cascata(self):
        partida = Partida.objects.filter(fase=self.fase_grupo).first()
        
        SetResult.objects.create(
            partida=partida,
            numero_set=1,
            pontos_a=21,
            pontos_b=15
        )
        
        self.assertEqual(SetResult.objects.filter(partida=partida).count(), 1)
        
        resetar_fase(self.fase_grupo.id)
        
        self.assertEqual(SetResult.objects.filter(partida=partida).count(), 0)
    
    def test_resetar_exclui_grupos_na_fase_de_grupos(self):
        grupos_antes = Grupo.objects.filter(fase=self.fase_grupo).count()
        self.assertGreater(grupos_antes, 0)

        resetar_fase(self.fase_grupo.id)

        grupos_depois = Grupo.objects.filter(fase=self.fase_grupo).count()
        self.assertEqual(grupos_depois, 0)
    
    def test_resetar_limpa_equipes_opcional(self):
        equipes_antes = self.grupo_a.equipes.count()
        self.assertGreater(equipes_antes, 0)
        
        resultado = resetar_fase(self.fase_grupo.id, limpar_grupos=True)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['grupos_limpos'], 1)
        
        equipes_depois = self.grupo_a.equipes.count()
        self.assertEqual(equipes_depois, 0)
    
    def test_resetar_nao_limpa_equipes_por_padrao(self):
        equipes_antes = self.grupo_a.equipes.count()
        self.assertGreater(equipes_antes, 0)
        
        resetar_fase(self.fase_grupo.id, limpar_grupos=False)
        
        equipes_depois = self.grupo_a.equipes.count()
        self.assertEqual(equipes_depois, equipes_antes)
    
    def test_obter_estatisticas_fase(self):
        partida = Partida.objects.filter(fase=self.fase_grupo).first()
        partida.status = 'AO_VIVO'
        partida.save()
        
        stats = obter_estatisticas_fase(self.fase_grupo.id)
        
        self.assertTrue(stats['success'])
        self.assertEqual(stats['fase_nome'], 'Fase de Grupos')
        self.assertEqual(stats['fase_tipo'], 'GRUPO')
        self.assertEqual(stats['total_grupos'], 1)
        self.assertEqual(stats['grupos_com_equipes'], 1)
        self.assertEqual(stats['total_equipes_alocadas'], 4)
        self.assertGreater(stats['total_partidas'], 0)
        self.assertEqual(stats['partidas_ao_vivo'], 1)
        self.assertTrue(stats['pode_resetar'])
    
    def test_estatisticas_com_partidas_finalizadas(self):
        partida = Partida.objects.filter(fase=self.fase_grupo).first()
        partida.status = 'FINALIZADA'
        partida.vencedor = partida.equipe_a
        partida.save()
        
        stats = obter_estatisticas_fase(self.fase_grupo.id)
        
        self.assertEqual(stats['partidas_finalizadas'], 1)
        self.assertFalse(stats['pode_resetar'])
        self.assertIn('finalizadas', stats['mensagem_reset'])
