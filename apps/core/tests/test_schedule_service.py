from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import Torneio, Fase, Grupo, Equipe, RegraPontuacao, Partida
from apps.core.services.schedule_service import (
    gerar_round_robin,
    gerar_round_robin_fase,
    atribuir_ordem_cronograma,
    reordenar_partidas,
)

User = get_user_model()


class ScheduleServiceTest(TestCase):
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
        
        for equipe in self.equipes:
            self.grupo_a.equipes.add(equipe)
    
    def test_round_robin_calculo_correto(self):
        resultado = gerar_round_robin(self.grupo_a.id)
        
        self.assertTrue(resultado['success'])
        
        num_equipes = 4
        partidas_esperadas = (num_equipes * (num_equipes - 1)) // 2
        
        self.assertEqual(resultado['partidas_criadas'], partidas_esperadas)
        self.assertEqual(Partida.objects.filter(grupo=self.grupo_a).count(), 6)
    
    def test_round_robin_sem_duplicidade(self):
        gerar_round_robin(self.grupo_a.id)
        
        partidas = Partida.objects.filter(grupo=self.grupo_a)
        
        confrontos = set()
        for partida in partidas:
            confronto = tuple(sorted([partida.equipe_a.id, partida.equipe_b.id]))
            self.assertNotIn(confronto, confrontos, "Confronto duplicado encontrado")
            confrontos.add(confronto)
    
    def test_round_robin_sem_auto_jogo(self):
        gerar_round_robin(self.grupo_a.id)
        
        partidas = Partida.objects.filter(grupo=self.grupo_a)
        
        for partida in partidas:
            self.assertNotEqual(
                partida.equipe_a.id,
                partida.equipe_b.id,
                "Encontrado jogo de equipe contra ela mesma"
            )
    
    def test_round_robin_sem_repeticao_na_mesma_rodada(self):
        gerar_round_robin(self.grupo_a.id)

        partidas = Partida.objects.filter(grupo=self.grupo_a)
        rodadas = sorted(set(partidas.values_list('rodada', flat=True)))

        self.assertEqual(rodadas, [1, 2, 3])

        for rodada in rodadas:
            ids_equipes = []
            for partida in partidas.filter(rodada=rodada):
                ids_equipes.extend([partida.equipe_a_id, partida.equipe_b_id])

            self.assertEqual(len(ids_equipes), len(set(ids_equipes)))

    def test_partidas_nascem_agendadas(self):
        gerar_round_robin(self.grupo_a.id)
        
        partidas = Partida.objects.filter(grupo=self.grupo_a)
        
        for partida in partidas:
            self.assertEqual(partida.status, 'AGENDADA')
            self.assertFalse(partida.is_wo)
            self.assertIsNone(partida.vencedor)
    
    def test_grupo_com_menos_de_2_equipes(self):
        grupo_vazio = Grupo.objects.create(
            fase=self.fase_grupo,
            nome='Grupo Vazio'
        )
        
        resultado = gerar_round_robin(grupo_vazio.id)
        
        self.assertFalse(resultado['success'])
        self.assertIn('pelo menos 2 equipes', resultado['message'])
    
    def test_bloqueio_geracao_duplicada(self):
        gerar_round_robin(self.grupo_a.id)
        
        resultado = gerar_round_robin(self.grupo_a.id)
        
        self.assertFalse(resultado['success'])
        self.assertIn('já possui partidas', resultado['message'])
    
    def test_gerar_round_robin_fase(self):
        grupo_b = Grupo.objects.create(
            fase=self.fase_grupo,
            nome='Grupo B'
        )
        
        for i in range(5, 8):
            equipe = Equipe.objects.create(
                torneio=self.torneio,
                nome=f'Equipe {i}'
            )
            grupo_b.equipes.add(equipe)
        
        resultado = gerar_round_robin_fase(self.fase_grupo.id)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['grupos_processados'], 2)
        self.assertEqual(resultado['partidas_criadas'], 9)
    
    def test_ordem_cronograma_em_blocos_por_grupo(self):
        grupo_b = Grupo.objects.create(
            fase=self.fase_grupo,
            nome='Grupo B'
        )
        
        for i in range(5, 9):
            equipe = Equipe.objects.create(
                torneio=self.torneio,
                nome=f'Equipe {i}'
            )
            grupo_b.equipes.add(equipe)
        
        gerar_round_robin_fase(self.fase_grupo.id)
        
        partidas = Partida.objects.filter(fase=self.fase_grupo).order_by('ordem_cronograma')
        grup_names = [p.grupo.nome for p in partidas]
        
        # Com 4 equipes em cada grupo: 6 partidas por grupo, total 12
        self.assertEqual(len(grup_names), 12)

        chunk_size = 2
        for start in range(0, len(grup_names), chunk_size):
            bloco = grup_names[start:start + chunk_size]
            # bloco interno deve conter o mesmo nome de grupo
            self.assertTrue(len(bloco) == chunk_size)
            self.assertEqual(bloco[0], bloco[1])
            # blocos consecutivos devem alternar de grupo
            if start >= chunk_size:
                prev_block_name = grup_names[start - 1]
                self.assertNotEqual(bloco[0], prev_block_name,
                                    f'Esperava alternância entre blocos na posição {start}')
    
    def test_ordem_cronograma_sequencial(self):
        grupo_b = Grupo.objects.create(
            fase=self.fase_grupo,
            nome='Grupo B'
        )
        
        for i in range(5, 8):
            equipe = Equipe.objects.create(
                torneio=self.torneio,
                nome=f'Equipe {i}'
            )
            grupo_b.equipes.add(equipe)
        
        gerar_round_robin_fase(self.fase_grupo.id)
        
        partidas = Partida.objects.filter(fase=self.fase_grupo).order_by('ordem_cronograma')
        
        ordens = [p.ordem_cronograma for p in partidas]
        
        self.assertEqual(ordens, list(range(1, len(ordens) + 1)))
        
        for i in range(len(ordens) - 1):
            self.assertEqual(ordens[i] + 1, ordens[i + 1])
    
    def test_atribuir_ordem_cronograma(self):
        gerar_round_robin(self.grupo_a.id)
        
        resultado = atribuir_ordem_cronograma(self.fase_grupo.id)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['partidas_ordenadas'], 6)
        
        partidas = Partida.objects.filter(fase=self.fase_grupo).order_by('ordem_cronograma')
        for idx, partida in enumerate(partidas, start=1):
            self.assertEqual(partida.ordem_cronograma, idx)
    
    def test_reordenar_partidas(self):
        gerar_round_robin_fase(self.fase_grupo.id)
        
        partidas = list(Partida.objects.filter(fase=self.fase_grupo).order_by('id'))
        ids_originais = [p.id for p in partidas]
        
        nova_ordem = list(reversed(ids_originais))
        
        resultado = reordenar_partidas(self.fase_grupo.id, nova_ordem)
        
        self.assertTrue(resultado['success'])
        
        partidas_reordenadas = Partida.objects.filter(fase=self.fase_grupo).order_by('ordem_cronograma')
        ids_reordenados = [p.id for p in partidas_reordenadas]
        
        self.assertEqual(ids_reordenados, nova_ordem)
    
    def test_fase_eliminatoria_bloqueada(self):
        fase_eliminatoria = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Quartas',
            tipo='ELIMINATORIA',
            ordem=2
        )
        
        resultado = gerar_round_robin_fase(fase_eliminatoria.id)
        
        self.assertFalse(resultado['success'])
        self.assertIn('GRUPO', resultado['message'])
