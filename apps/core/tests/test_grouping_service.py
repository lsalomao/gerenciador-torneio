from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import Torneio, Fase, Grupo, Equipe, RegraPontuacao
from apps.core.services.grouping_service import (
    sortear_equipes_automatico,
    validar_distribuicao_equipes,
    alocar_equipe_manual,
    remover_equipe_grupo,
    limpar_grupos_fase,
)

User = get_user_model()


class GroupingServiceTest(TestCase):
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
        
        self.fase_eliminatoria = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Quartas de Final',
            tipo='ELIMINATORIA',
            ordem=2
        )
        
        self.grupo_a = Grupo.objects.create(
            fase=self.fase_grupo,
            nome='Grupo A'
        )
        
        self.grupo_b = Grupo.objects.create(
            fase=self.fase_grupo,
            nome='Grupo B'
        )
        
        self.equipes = []
        for i in range(1, 9):
            equipe = Equipe.objects.create(
                torneio=self.torneio,
                nome=f'Equipe {i}'
            )
            self.equipes.append(equipe)
    
    def test_sortear_equipes_balanceado(self):
        resultado = sortear_equipes_automatico(self.fase_grupo.id)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['equipes_distribuidas'], 8)
        self.assertEqual(resultado['grupos_preenchidos'], 2)
        
        equipes_grupo_a = self.grupo_a.equipes.count()
        equipes_grupo_b = self.grupo_b.equipes.count()
        
        self.assertEqual(equipes_grupo_a, 4)
        self.assertEqual(equipes_grupo_b, 4)
        self.assertLessEqual(abs(equipes_grupo_a - equipes_grupo_b), 1)
    
    def test_sortear_equipes_sem_duplicidade(self):
        resultado = sortear_equipes_automatico(self.fase_grupo.id)
        
        self.assertTrue(resultado['success'])
        
        todas_equipes = set()
        for grupo in [self.grupo_a, self.grupo_b]:
            for equipe in grupo.equipes.all():
                self.assertNotIn(equipe.id, todas_equipes, "Equipe duplicada encontrada")
                todas_equipes.add(equipe.id)
    
    def test_sortear_fase_eliminatoria_bloqueado(self):
        resultado = sortear_equipes_automatico(self.fase_eliminatoria.id)
        
        self.assertFalse(resultado['success'])
        self.assertIn('GRUPO', resultado['message'])
    
    def test_sortear_fase_sem_grupos(self):
        fase_nova = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Fase Vazia',
            tipo='GRUPO',
            ordem=3
        )
        
        resultado = sortear_equipes_automatico(fase_nova.id)
        
        self.assertFalse(resultado['success'])
        self.assertIn('grupo', resultado['message'].lower())
    
    def test_alocar_equipe_manual_sucesso(self):
        resultado = alocar_equipe_manual(self.grupo_a.id, self.equipes[0].id)
        
        self.assertTrue(resultado['success'])
        self.assertIn(self.equipes[0], self.grupo_a.equipes.all())
    
    def test_alocar_equipe_outro_torneio(self):
        outro_torneio = Torneio.objects.create(
            owner=self.user,
            nome='Outro Torneio',
            modalidade='Beach Tennis',
            local='Praia Norte',
            data_inicio='2026-06-01',
            hora_inicio='09:00'
        )
        
        equipe_outro_torneio = Equipe.objects.create(
            torneio=outro_torneio,
            nome='Equipe Forasteira'
        )
        
        resultado = alocar_equipe_manual(self.grupo_a.id, equipe_outro_torneio.id)
        
        self.assertFalse(resultado['success'])
        self.assertIn('torneio', resultado['message'].lower())
    
    def test_alocar_equipe_duplicada_bloqueado(self):
        self.grupo_a.equipes.add(self.equipes[0])
        
        resultado = alocar_equipe_manual(self.grupo_b.id, self.equipes[0].id)
        
        self.assertFalse(resultado['success'])
        self.assertIn('alocada', resultado['message'].lower())
    
    def test_validar_distribuicao_ok(self):
        self.grupo_a.equipes.add(self.equipes[0], self.equipes[1])
        self.grupo_b.equipes.add(self.equipes[2], self.equipes[3])
        
        valido, mensagem = validar_distribuicao_equipes(self.fase_grupo.id)
        
        self.assertTrue(valido)
        self.assertEqual(mensagem, "Distribuição válida")
    
    def test_validar_distribuicao_duplicada(self):
        self.grupo_a.equipes.add(self.equipes[0])
        self.grupo_b.equipes.add(self.equipes[0])
        
        valido, mensagem = validar_distribuicao_equipes(self.fase_grupo.id)
        
        self.assertFalse(valido)
        self.assertIn('mais de um grupo', mensagem.lower())
    
    def test_remover_equipe_grupo(self):
        self.grupo_a.equipes.add(self.equipes[0])
        
        resultado = remover_equipe_grupo(self.grupo_a.id, self.equipes[0].id)
        
        self.assertTrue(resultado['success'])
        self.assertNotIn(self.equipes[0], self.grupo_a.equipes.all())
    
    def test_limpar_grupos_fase(self):
        self.grupo_a.equipes.add(self.equipes[0], self.equipes[1])
        self.grupo_b.equipes.add(self.equipes[2], self.equipes[3])
        
        resultado = limpar_grupos_fase(self.fase_grupo.id)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['grupos_limpos'], 2)
        self.assertEqual(self.grupo_a.equipes.count(), 0)
        self.assertEqual(self.grupo_b.equipes.count(), 0)
