from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core.models import Equipe, Fase, Grupo, Jogador, Partida, RegraPontuacao, SetResult, Torneio

User = get_user_model()


class PublicApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='publicu', email='public@u.com', password='pass')
        self.regra = RegraPontuacao.objects.create(
            nome='Set Único 21',
            sets_para_vencer=1,
            pontos_por_set=21,
            tem_vantagem=True,
        )
        self.torneio = Torneio.objects.create(
            owner=self.user,
            nome='Copa Pública',
            modalidade='Vôlei',
            local='Quadra Central',
            data_inicio='2026-05-01',
            hora_inicio='08:00',
            polling_interval=15,
            live_url='https://youtube.com/live/abc',
        )

    def test_dashboard_endpoint_grupo(self):
        fase = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Fase de Grupos',
            tipo='GRUPO',
            ordem=1,
            equipes_avancam=2,
            is_ativa=True,
        )
        grupo = Grupo.objects.create(fase=fase, nome='Grupo A')
        e1 = Equipe.objects.create(torneio=self.torneio, nome='Time A')
        e2 = Equipe.objects.create(torneio=self.torneio, nome='Time B')
        grupo.equipes.add(e1, e2)
        partida = Partida.objects.create(
            fase=fase,
            grupo=grupo,
            equipe_a=e1,
            equipe_b=e2,
            status='AGENDADA',
            ordem_cronograma=1,
        )
        SetResult.objects.create(partida=partida, numero_set=1, pontos_a=21, pontos_b=18)
        partida.status = 'FINALIZADA'
        partida.vencedor = e1
        partida.save(update_fields=['status', 'vencedor'])

        url = reverse('public_dashboard_data', kwargs={'slug': self.torneio.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['torneio']['nome'], 'Copa Pública')
        self.assertEqual(data['torneio']['polling_interval'], 15)
        self.assertEqual(data['fase_ativa']['tipo'], 'GRUPO')
        self.assertEqual(data['fase_ativa']['equipes_avancam'], 2)
        self.assertEqual(len(data['grupos']), 1)
        self.assertEqual(data['grupos'][0]['nome'], 'Grupo A')

    def test_dashboard_endpoint_eliminatoria(self):
        fase = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Semi Final',
            tipo='ELIMINATORIA',
            ordem=2,
            is_ativa=True,
        )
        e1 = Equipe.objects.create(torneio=self.torneio, nome='Alpha')
        e2 = Equipe.objects.create(torneio=self.torneio, nome='Beta')
        Partida.objects.create(
            fase=fase,
            equipe_a=e1,
            equipe_b=e2,
            status='AGENDADA',
            ordem_cronograma=3,
        )

        url = reverse('public_dashboard_data', kwargs={'slug': self.torneio.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['fase_ativa']['tipo'], 'ELIMINATORIA')
        self.assertIn('equipes_avancam', data['fase_ativa'])
        self.assertEqual(len(data['confrontos']), 1)
        self.assertEqual(data['confrontos'][0]['equipe_a'], 'Alpha')

    def test_live_endpoint_prioritizes_ao_vivo_then_agendada(self):
        fase = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Fase de Grupos',
            tipo='GRUPO',
            ordem=1,
            is_ativa=True,
        )
        e1 = Equipe.objects.create(torneio=self.torneio, nome='T1')
        e2 = Equipe.objects.create(torneio=self.torneio, nome='T2')
        e3 = Equipe.objects.create(torneio=self.torneio, nome='T3')
        e4 = Equipe.objects.create(torneio=self.torneio, nome='T4')

        agendada = Partida.objects.create(
            fase=fase,
            equipe_a=e1,
            equipe_b=e2,
            status='AGENDADA',
            ordem_cronograma=1,
        )
        ao_vivo = Partida.objects.create(
            fase=fase,
            equipe_a=e3,
            equipe_b=e4,
            status='AO_VIVO',
            ordem_cronograma=2,
        )
        SetResult.objects.create(partida=ao_vivo, numero_set=1, pontos_a=21, pontos_b=19)

        url = reverse('public_dashboard_data', kwargs={'slug': self.torneio.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNotNone(data['live_match'])
        self.assertEqual(data['live_match']['id'], ao_vivo.id)
        self.assertEqual(data['live_match']['equipe_a'], 'T3')

        url = reverse('public_live_data', kwargs={'slug': self.torneio.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['highlight']['id'], ao_vivo.id)

        ao_vivo.status = 'FINALIZADA'
        ao_vivo.vencedor = e3
        ao_vivo.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['highlight']['id'], agendada.id)

    def test_only_one_active_phase_per_torneio(self):
        fase1 = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Fase 1',
            tipo='GRUPO',
            ordem=1,
            is_ativa=True,
        )
        fase2 = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Fase 2',
            tipo='ELIMINATORIA',
            ordem=2,
            is_ativa=True,
        )

        fase1.refresh_from_db()
        fase2.refresh_from_db()

        self.assertFalse(fase1.is_ativa)
        self.assertTrue(fase2.is_ativa)

    def test_live_endpoint_returns_upcoming_matches_without_highlight_duplication(self):
        fase = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Fase de Grupos',
            tipo='GRUPO',
            ordem=1,
            is_ativa=True,
        )
        e1 = Equipe.objects.create(torneio=self.torneio, nome='T1')
        e2 = Equipe.objects.create(torneio=self.torneio, nome='T2')
        e3 = Equipe.objects.create(torneio=self.torneio, nome='T3')
        e4 = Equipe.objects.create(torneio=self.torneio, nome='T4')

        primeiro = Partida.objects.create(
            fase=fase,
            equipe_a=e1,
            equipe_b=e2,
            status='AGENDADA',
            ordem_cronograma=1,
        )
        segundo = Partida.objects.create(
            fase=fase,
            equipe_a=e3,
            equipe_b=e4,
            status='AGENDADA',
            ordem_cronograma=2,
        )

        url = reverse('public_live_data', kwargs={'slug': self.torneio.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['highlight']['id'], primeiro.id)
        self.assertEqual(len(data['upcoming_matches']), 1)
        self.assertEqual(data['upcoming_matches'][0]['id'], segundo.id)

    def test_dashboard_endpoint_returns_campeao_on_final_finished(self):
        fase = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Final',
            tipo='ELIMINATORIA',
            ordem=3,
            is_ativa=True,
        )
        e1 = Equipe.objects.create(torneio=self.torneio, nome='Tubarões')
        e2 = Equipe.objects.create(torneio=self.torneio, nome='Águias')
        Jogador.objects.create(equipe=e1, nome='Jogador 2')
        Jogador.objects.create(equipe=e1, nome='Jogador 1')
        Partida.objects.create(
            fase=fase,
            equipe_a=e1,
            equipe_b=e2,
            status='FINALIZADA',
            vencedor=e1,
            ordem_cronograma=1,
        )

        url = reverse('public_dashboard_data', kwargs={'slug': self.torneio.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['campeao']['nome'], 'Tubarões')
        self.assertEqual(data['campeao']['jogadores'], ['Jogador 1', 'Jogador 2'])
        self.assertEqual(data['podio']['campeao']['nome'], 'Tubarões')
        self.assertEqual(data['podio']['campeao']['jogadores'], ['Jogador 1', 'Jogador 2'])
        self.assertEqual(data['podio']['vice']['nome'], 'Águias')
        self.assertEqual(data['podio']['vice']['jogadores'], [])
        self.assertIsNone(data['podio']['terceiro'])

    def test_dashboard_endpoint_returns_podio_with_third_place_when_available(self):
        fase_terceiro = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='3º Lugar',
            tipo='ELIMINATORIA',
            ordem=2,
            is_ativa=False,
        )
        fase_final = Fase.objects.create(
            torneio=self.torneio,
            regra=self.regra,
            nome='Final',
            tipo='ELIMINATORIA',
            ordem=3,
            is_ativa=True,
        )
        e1 = Equipe.objects.create(torneio=self.torneio, nome='Lobos')
        e2 = Equipe.objects.create(torneio=self.torneio, nome='Falcões')
        e3 = Equipe.objects.create(torneio=self.torneio, nome='Leões')
        e4 = Equipe.objects.create(torneio=self.torneio, nome='Panteras')
        Jogador.objects.create(equipe=e1, nome='Atila')
        Jogador.objects.create(equipe=e2, nome='Breno')
        Jogador.objects.create(equipe=e4, nome='Caio')

        Partida.objects.create(
            fase=fase_final,
            equipe_a=e1,
            equipe_b=e2,
            status='FINALIZADA',
            vencedor=e2,
            ordem_cronograma=1,
        )
        Partida.objects.create(
            fase=fase_terceiro,
            equipe_a=e3,
            equipe_b=e4,
            status='FINALIZADA',
            vencedor=e4,
            ordem_cronograma=2,
        )

        url = reverse('public_dashboard_data', kwargs={'slug': self.torneio.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['podio']['campeao']['nome'], 'Falcões')
        self.assertEqual(data['podio']['campeao']['jogadores'], ['Breno'])
        self.assertEqual(data['podio']['vice']['nome'], 'Lobos')
        self.assertEqual(data['podio']['vice']['jogadores'], ['Atila'])
        self.assertEqual(data['podio']['terceiro']['nome'], 'Panteras')
        self.assertEqual(data['podio']['terceiro']['jogadores'], ['Caio'])

    def test_public_endpoints_are_read_only(self):
        dashboard_url = reverse('public_dashboard_data', kwargs={'slug': self.torneio.slug})
        live_url = reverse('public_live_data', kwargs={'slug': self.torneio.slug})

        self.assertEqual(self.client.post(dashboard_url).status_code, 405)
        self.assertEqual(self.client.post(live_url).status_code, 405)
