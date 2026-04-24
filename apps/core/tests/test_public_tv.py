from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core.models import Torneio

User = get_user_model()


class PublicTvViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tvuser', email='tv@u.com', password='pass')
        self.torneio = Torneio.objects.create(
            owner=self.user,
            nome='Copa TV',
            modalidade='Vôlei',
            local='Arena',
            data_inicio='2026-05-01',
            hora_inicio='08:00',
            polling_interval=12,
            live_url='https://youtube.com/live/xyz',
        )

    def test_public_tv_page_is_accessible_without_login(self):
        url = reverse('public_torneio_tv', kwargs={'slug': self.torneio.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Copa TV')
        self.assertContains(response, 'const intervalMs = 12000;')
        self.assertContains(response, f'/api/v1/public/torneio/{self.torneio.slug}/dashboard/')
        self.assertContains(response, f'/api/v1/public/torneio/{self.torneio.slug}/live/')
        self.assertContains(response, 'Entrar em Tela Cheia')
        self.assertContains(response, 'id="tv-clock"')
        self.assertContains(response, 'ASSISTA AO VIVO')

    def test_public_tv_layout_adapts_when_live_url_is_empty(self):
        self.torneio.live_url = ''
        self.torneio.save(update_fields=['live_url'])

        url = reverse('public_torneio_tv', kwargs={'slug': self.torneio.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="tv-screen no-live"')
        self.assertNotContains(response, 'ASSISTA AO VIVO')

    def test_public_tv_page_returns_404_for_invalid_slug(self):
        url = reverse('public_torneio_tv', kwargs={'slug': 'slug-inexistente'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
