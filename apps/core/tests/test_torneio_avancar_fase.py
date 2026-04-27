from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.core.models import Torneio, RegraPontuacao, Fase, Equipe, Grupo, Partida, SetResult
from apps.core.services.torneio_setup_service import criar_fases_torneio

User = get_user_model()


class TorneioAvancaFaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Criar usuário e fazer login
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass'
        )
        self.client.login(username='testuser', password='testpass')
        
        # Criar regra
        self.regra = RegraPontuacao.objects.create(
            nome='Test Rule',
            sets_para_vencer=1,
            pontos_por_set=21
        )
        
        # Criar torneio
        self.torneio = Torneio.objects.create(
            owner=self.user,
            nome='Test Tournament',
            modalidade='Vôlei',
            local='Quadra A',
            data_inicio='2026-05-01',
            hora_inicio='10:00'
        )
        
        # Criar fase de grupos (com equipes_avancam=2 para ter 2 classificados)
        self.fase_grupo = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Fase de Grupos',
            tipo='GRUPO',
            ordem=1,
            equipes_avancam=2
        )
        
        # Criar fase eliminatória vazia
        self.fase_elim = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Eliminatória',
            tipo='ELIMINATORIA',
            ordem=2
        )
        
        # Criar 2 grupos e equipes
        self.grupo1 = Grupo.objects.create(fase=self.fase_grupo, nome='Grupo A')
        self.grupo2 = Grupo.objects.create(fase=self.fase_grupo, nome='Grupo B')
        
        self.eq1 = Equipe.objects.create(torneio=self.torneio, nome='Time A')
        self.eq2 = Equipe.objects.create(torneio=self.torneio, nome='Time B')
        self.eq3 = Equipe.objects.create(torneio=self.torneio, nome='Time C')
        self.eq4 = Equipe.objects.create(torneio=self.torneio, nome='Time D')
        
        self.grupo1.equipes.add(self.eq1, self.eq2)
        self.grupo2.equipes.add(self.eq3, self.eq4)
        
        # Criar e finalizar partidas
        self.partida1 = Partida.objects.create(
            fase=self.fase_grupo,
            grupo=self.grupo1,
            equipe_a=self.eq1,
            equipe_b=self.eq2,
            ordem_cronograma=1
        )
        
        SetResult.objects.create(
            partida=self.partida1,
            numero_set=1,
            pontos_a=21,
            pontos_b=10
        )
        
        self.partida1.vencedor = self.eq1
        self.partida1.status = 'FINALIZADA'
        self.partida1.save()
        
        self.partida2 = Partida.objects.create(
            fase=self.fase_grupo,
            grupo=self.grupo2,
            equipe_a=self.eq3,
            equipe_b=self.eq4,
            ordem_cronograma=2
        )
        
        SetResult.objects.create(
            partida=self.partida2,
            numero_set=1,
            pontos_a=21,
            pontos_b=18
        )
        
        self.partida2.vencedor = self.eq3
        self.partida2.status = 'FINALIZADA'
        self.partida2.save()

    def test_torneio_detail_exibe_stepper_sem_botao_avancar_fase(self):
        url = reverse('admin_torneio_detail', kwargs={'pk': self.torneio.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Criação')
        self.assertContains(response, 'Inscrições')
        self.assertContains(response, 'Em Andamento')
        self.assertContains(response, 'Encerrado')
        self.assertNotContains(response, 'Avançar Fase')

    def test_avancar_fase_gera_eliminatoria(self):
        """Testa se clicar no botão gera a fase eliminatória automaticamente."""
        url = reverse('admin_torneio_avancar_fase', kwargs={'pk': self.torneio.pk})
        
        # Verificar que eliminatória está vazia
        self.assertEqual(self.fase_elim.partidas.count(), 0)
        
        # Fazer POST
        response = self.client.post(url)
        
        # Deve redirecionar para a fase eliminatória
        self.assertEqual(response.status_code, 302)
        
        # Verificar que partidas foram criadas
        self.fase_elim.refresh_from_db()
        self.assertGreater(self.fase_elim.partidas.count(), 0)

    def test_avancar_fase_rejeita_grupos_incompletos(self):
        """Verifica se rejeita quando há grupos não finalizados."""
        # Criar terceira partida não finalizada
        eq5 = Equipe.objects.create(torneio=self.torneio, nome='Time E')
        eq6 = Equipe.objects.create(torneio=self.torneio, nome='Time F')
        
        grupo3 = Grupo.objects.create(fase=self.fase_grupo, nome='Grupo C')
        grupo3.equipes.add(eq5, eq6)
        
        partida3 = Partida.objects.create(
            fase=self.fase_grupo,
            grupo=grupo3,
            equipe_a=eq5,
            equipe_b=eq6,
            ordem_cronograma=3,
            status='AGENDADA'
        )
        
        url = reverse('admin_torneio_avancar_fase', kwargs={'pk': self.torneio.pk})
        response = self.client.post(url)
        
        # Deve redirecionar com mensagem de erro
        self.assertEqual(response.status_code, 302)
        
        # Fase eliminatória não deve ter partidas
        self.assertEqual(self.fase_elim.partidas.count(), 0)

    def test_avancar_fase_sem_fase_eliminatoria_configurada(self):
        """Verifica se rejeita quando não há fase eliminatória configurada."""
        # Excluir fase eliminatória
        self.fase_elim.delete()
        
        url = reverse('admin_torneio_avancar_fase', kwargs={'pk': self.torneio.pk})
        response = self.client.post(url)
        
        # Deve redirecionar com mensagem de erro
        self.assertEqual(response.status_code, 302)


class TorneioSetupFaseAtivaTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='setupuser',
            email='setup@test.com',
            password='testpass'
        )
        self.torneio = Torneio.objects.create(
            owner=self.user,
            nome='Setup Tournament',
            modalidade='Vôlei',
            local='Quadra B',
            data_inicio='2026-05-01',
            hora_inicio='10:00',
            quantidade_times=8,
            formato_torneio='grupos_e_eliminatoria'
        )

    def test_criar_fases_torneio_define_primeira_fase_como_ativa(self):
        resultado = criar_fases_torneio(self.torneio)

        self.assertTrue(resultado['sucesso'])

        fases = list(self.torneio.fases.order_by('ordem'))
        self.assertGreater(len(fases), 0)
        self.assertTrue(fases[0].is_ativa)
        self.assertFalse(any(fase.is_ativa for fase in fases[1:]))
