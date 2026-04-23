from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class Torneio(models.Model):
    STATUS_CHOICES = [
        ('CRIACAO', 'Criação'),
        ('INSCRICOES', 'Inscrições'),
        ('ANDAMENTO', 'Em Andamento'),
        ('ENCERRADO', 'Encerrado'),
    ]

    QUANTIDADE_TIMES_CHOICES = [
        (4, '4 times'),
        (8, '8 times'),
        (16, '16 times'),
        (32, '32 times'),
    ]

    FORMATO_CHOICES = [
        ('grupos_e_eliminatoria', 'Grupos + Eliminatória'),
        ('so_eliminatoria', 'Só Eliminatória'),
    ]

    TIMES_POR_GRUPO_CHOICES = [
        (4, '4 times por grupo'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='torneios'
    )
    nome = models.CharField(max_length=200)
    modalidade = models.CharField(max_length=100, help_text="Ex: Vôlei de Praia, Beach Tennis")
    local = models.CharField(max_length=255)
    data_inicio = models.DateField()
    hora_inicio = models.TimeField()
    slug = models.SlugField(unique=True, blank=True, max_length=220)
    polling_interval = models.IntegerField(default=10)
    live_url = models.URLField(blank=True, null=True)
    jogadores_por_equipe = models.PositiveIntegerField(default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CRIACAO')
    quantidade_times = models.PositiveIntegerField(
        choices=QUANTIDADE_TIMES_CHOICES,
        null=True,
        blank=True,
        help_text="Quantidade total de times no torneio"
    )
    formato_torneio = models.CharField(
        max_length=30,
        choices=FORMATO_CHOICES,
        null=True,
        blank=True,
        help_text="Formato de disputa do torneio"
    )
    times_por_grupo = models.PositiveIntegerField(
        choices=TIMES_POR_GRUPO_CHOICES,
        default=4,
        help_text="Quantidade de times por grupo (apenas para grupos_e_eliminatoria)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Torneio'
        verbose_name_plural = 'Torneios'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nome)
            slug = base_slug
            counter = 1
            while Torneio.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


class RegraPontuacao(models.Model):
    nome = models.CharField(max_length=100, help_text="Ex: Set Único 21pts, Melhor de 3 com 15pts")
    sets_para_vencer = models.PositiveIntegerField(
        default=1,
        help_text="Quantos sets precisa vencer para ganhar a partida. Ex: 1 para set único, 2 para melhor de 3."
    )
    pontos_por_set = models.PositiveIntegerField(default=21, help_text="Pontos para fechar o set")
    tem_vantagem = models.BooleanField(
        default=True,
        help_text="Se True, precisa abrir 2 pontos de vantagem para vencer o set."
    )
    limite_pontos_diretos = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Se preenchido, ao atingir este valor o time vence direto sem precisar de vantagem. Ex: 18 num set de 15."
    )

    class Meta:
        verbose_name = 'Regra de Pontuação'
        verbose_name_plural = 'Regras de Pontuação'

    def __str__(self):
        return self.nome


class Equipe(models.Model):
    torneio = models.ForeignKey(Torneio, on_delete=models.CASCADE, related_name='equipes')
    nome = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Equipe'
        verbose_name_plural = 'Equipes'
        unique_together = ('torneio', 'nome')

    def __str__(self):
        return f"{self.nome} ({self.torneio.nome})"


class Jogador(models.Model):
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='jogadores')
    nome = models.CharField(max_length=100)
    apelido = models.CharField(max_length=50, blank=True)
    posicao = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Jogador'
        verbose_name_plural = 'Jogadores'

    def __str__(self):
        return self.apelido or self.nome


class Fase(models.Model):
    TIPO_CHOICES = [
        ('GRUPO', 'Fase de Grupos'),
        ('ELIMINATORIA', 'Fase Eliminatória'),
    ]

    torneio = models.ForeignKey(Torneio, on_delete=models.CASCADE, related_name='fases')
    regra = models.ForeignKey(
        RegraPontuacao,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Regra de pontuação aplicada a todas as partidas desta fase."
    )
    nome = models.CharField(max_length=100, help_text="Ex: Fase de Grupos, Quartas de Final, Final")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ordem = models.PositiveIntegerField(default=1, help_text="Ordem de execução das fases no torneio")
    equipes_avancam = models.PositiveIntegerField(
        default=2,
        help_text="Quantas equipes de cada grupo avançam para a próxima fase."
    )
    is_ativa = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Fase'
        verbose_name_plural = 'Fases'
        ordering = ['ordem']

    def save(self, *args, **kwargs):
        if self.is_ativa:
            Fase.objects.filter(torneio=self.torneio, is_ativa=True).exclude(pk=self.pk).update(is_ativa=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} — {self.torneio.nome}"


class Grupo(models.Model):
    fase = models.ForeignKey(Fase, on_delete=models.CASCADE, related_name='grupos')
    nome = models.CharField(max_length=50, help_text="Ex: Grupo A, Grupo 1")
    equipes = models.ManyToManyField(Equipe, related_name='grupos', blank=True)

    class Meta:
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'

    def __str__(self):
        return f"{self.nome} — {self.fase.nome}"


class Partida(models.Model):
    STATUS_CHOICES = [
        ('AGENDADA', 'Agendada'),
        ('AO_VIVO', 'Ao Vivo'),
        ('FINALIZADA', 'Finalizada'),
    ]

    fase = models.ForeignKey(Fase, on_delete=models.CASCADE, related_name='partidas')
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='partidas',
        help_text="Preenchido apenas em fases de grupo."
    )
    equipe_a = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='partidas_como_a')
    equipe_b = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='partidas_como_b')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AGENDADA')
    vencedor = models.ForeignKey(
        Equipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vitorias'
    )

    is_wo = models.BooleanField(default=False, help_text="Se True, vitória por W.O. com pontuação máxima automática.")
    vencedor_wo = models.ForeignKey(
        Equipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vitorias_wo'
    )

    ordem_cronograma = models.PositiveIntegerField(default=0, help_text="Ordem de disputa na quadra única.")
    rodada = models.PositiveIntegerField(default=1, help_text="Número da rodada dentro da fase (1=primeira rodada)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Partida'
        verbose_name_plural = 'Partidas'
        ordering = ['ordem_cronograma']

    def __str__(self):
        return f"{self.equipe_a} vs {self.equipe_b} — {self.fase.nome}"

    def save(self, *args, **kwargs):
        # Se alguém tentar marcar FINALIZADA manualmente, exigir vencedor
        if self.status == 'FINALIZADA' and not self.vencedor:
            raise ValidationError('Não é permitido finalizar partida sem vencedor definido')
        super().save(*args, **kwargs)


class SetResult(models.Model):
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='sets')
    numero_set = models.PositiveIntegerField(help_text="Número do set. Ex: 1, 2, 3")
    pontos_a = models.PositiveIntegerField(default=0)
    pontos_b = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Set'
        verbose_name_plural = 'Sets'
        ordering = ['numero_set']
        unique_together = ('partida', 'numero_set')

    def __str__(self):
        return f"Set {self.numero_set}: {self.pontos_a} x {self.pontos_b}"

    def clean(self):
        # Não permitir manipular sets de partida finalizada
        if self.partida and self.partida.status == 'FINALIZADA':
            raise ValidationError('Não é permitido adicionar/editar sets em partida finalizada')


        regra = self.partida.fase.regra

        # Importar localmente para evitar import circular
        from apps.core.services.validation_service import validar_set

        # Validar pontos segundo a regra
        result = validar_set(self.pontos_a, self.pontos_b, regra)
        if not result.get('success'):
            raise ValidationError(f"Set inválido: {result.get('message')}")

        # Verificar limite máximo de sets
        max_sets = regra.sets_para_vencer * 2 - 1
        if self.numero_set > max_sets:
            raise ValidationError('Número do set excede o máximo permitido pela regra')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.partida and self.partida.status == 'FINALIZADA':
            raise ValidationError('Não é permitido remover sets de partida finalizada')
        super().delete(*args, **kwargs)

