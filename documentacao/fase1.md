# Plano de Execução — Fase 1: Fundação do Projeto e Modelagem de Dados

## Contexto do Projeto

Sistema web para gerenciamento de torneios esportivos (Vôlei de Praia, Futevôlei, Beach Tennis).\
Desenvolvido em Python + Django com templates, PostgreSQL, Docker e Nginx.

**Stack obrigatória:**

* Python 3.11+

* Django 5.x (Django Templates — sem DRF no MVP)

* PostgreSQL

* Docker + docker-compose

* Nginx (proxy reverso)

* Tailwind CSS (via CDN ou CLI)

* Variáveis de ambiente via `.env`

---

## Estrutura de Apps

O projeto terá dois apps Django:

* `users` → autenticação, modelo de usuário customizado

* `core` → toda a lógica de torneio (torneios, fases, grupos, partidas, etc.)

---

## Objetivo da Fase 1

Criar a base do projeto com:

1. Estrutura de pastas e configuração do Django

2. Docker + PostgreSQL funcionando

3. Modelo de usuário customizado

4. Todos os models do sistema

5. Django Admin configurado para cadastro manual

6. Migrações aplicadas e sistema rodando

---

## 1\. Estrutura de Pastas Esperada

```
gerenciador_torneio/
├── config/                  # Configurações do Django (settings, urls, wsgi)
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/               # App de autenticação
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   └── migrations/
│   └── core/                # App principal do torneio
│       ├── models.py
│       ├── admin.py
│       ├── apps.py
│       └── migrations/
├── templates/               # Templates HTML globais
│   └── base.html
├── static/                  # Arquivos estáticos
├── .env                     # Variáveis de ambiente (não versionar)
├── .env.example             # Exemplo de variáveis (versionar)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── manage.py
```

---

## 2\. Dependências (requirements.txt)

```
Django>=5.0,<6.0
psycopg2-binary>=2.9
django-environ>=0.11
whitenoise>=6.6
gunicorn>=21.2
```

---

## 3\. Variáveis de Ambiente (.env.example)

```
DEBUG=True
SECRET_KEY=sua-chave-secreta-aqui
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=torneio_db
DB_USER=torneio_user
DB_PASSWORD=torneio_pass
DB_HOST=db
DB_PORT=5432
```

---

## 4\. [settings.py](http://settings.py)

Configurar obrigatoriamente:

```python
import environ
from pathlib import Path

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps do projeto
    'apps.users',
    'apps.core',
]

# Modelo de usuário customizado (OBRIGATÓRIO antes da primeira migração)
AUTH_USER_MODEL = 'users.User'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/admin-area/'
LOGOUT_REDIRECT_URL = '/auth/login/'
```

---

## 5\. Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### docker-compose.yml

```yaml
version: '3.9'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"

  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./staticfiles:/app/staticfiles
    depends_on:
      - web

volumes:
  postgres_data:
```

### nginx.conf

```nginx
server {
    listen 80;

    location /static/ {
        alias /app/staticfiles/;
    }

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 6\. Model de Usuário Customizado (apps/users/models.py)

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Usuário customizado. Usar sempre este model no lugar do User padrão do Django.
    Preparado para expansão futura (ex: telefone para notificações).
    """
    telefone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username
```

---

## 7\. Models do Core (apps/core/models.py)

```python
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Torneio(models.Model):
    """
    Entidade principal. Cada torneio pertence a um ADM (owner).
    """
    STATUS_CHOICES = [
        ('CRIACAO', 'Criação'),
        ('INSCRICOES', 'Inscrições'),
        ('ANDAMENTO', 'Em Andamento'),
        ('ENCERRADO', 'Encerrado'),
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
    jogadores_por_equipe = models.PositiveIntegerField(default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CRIACAO')
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
    """
    Define como um jogo é vencido dentro de uma fase.
    Permite configuração flexível por torneio amador.
    """
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
    """
    Equipe exclusiva de um torneio. Não é reutilizada entre torneios.
    """
    torneio = models.ForeignKey(Torneio, on_delete=models.CASCADE, related_name='equipes')
    nome = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Equipe'
        verbose_name_plural = 'Equipes'
        unique_together = ('torneio', 'nome')

    def __str__(self):
        return f"{self.nome} ({self.torneio.nome})"


class Jogador(models.Model):
    """
    Jogador vinculado a uma equipe de um torneio específico.
    """
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
    """
    Fase do torneio. Pode ser de Grupo ou Eliminatória.
    Cada fase tem sua própria regra de pontuação.
    """
    TIPO_CHOICES = [
        ('GRUPO', 'Fase de Grupos'),
        ('ELIMINATORIA', 'Fase Eliminatória'),
    ]

    torneio = models.ForeignKey(Torneio, on_delete=models.CASCADE, related_name='fases')
    regra = models.ForeignKey(
        RegraPontuacao,
        on_delete=models.PROTECT,
        help_text="Regra de pontuação aplicada a todas as partidas desta fase."
    )
    nome = models.CharField(max_length=100, help_text="Ex: Fase de Grupos, Quartas de Final, Final")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ordem = models.PositiveIntegerField(default=1, help_text="Ordem de execução das fases no torneio")
    equipes_avancam = models.PositiveIntegerField(
        default=2,
        help_text="Quantas equipes de cada grupo avançam para a próxima fase."
    )

    class Meta:
        verbose_name = 'Fase'
        verbose_name_plural = 'Fases'
        ordering = ['ordem']

    def __str__(self):
        return f"{self.nome} — {self.torneio.nome}"


class Grupo(models.Model):
    """
    Grupo dentro de uma fase de grupos.
    Contém as equipes que jogarão entre si.
    """
    fase = models.ForeignKey(Fase, on_delete=models.CASCADE, related_name='grupos')
    nome = models.CharField(max_length=50, help_text="Ex: Grupo A, Grupo 1")
    equipes = models.ManyToManyField(Equipe, related_name='grupos', blank=True)

    class Meta:
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'

    def __str__(self):
        return f"{self.nome} — {self.fase.nome}"


class Partida(models.Model):
    """
    Partida entre duas equipes dentro de uma fase.
    Pode pertencer a um grupo (fase de grupos) ou ser eliminatória.
    Após FINALIZADA, não pode ser editada.
    """
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Partida'
        verbose_name_plural = 'Partidas'
        ordering = ['ordem_cronograma']

    def __str__(self):
        return f"{self.equipe_a} vs {self.equipe_b} — {self.fase.nome}"


class SetResult(models.Model):
    """
    Resultado de um set individual de uma partida.
    Permite visualização detalhada do placar (ex: 21-15, 18-21, 15-10).
    """
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
```

---

## 8\. Django Admin (apps/core/admin.py)

```python
from django.contrib import admin
from .models import (
    Torneio, RegraPontuacao, Equipe, Jogador,
    Fase, Grupo, Partida, SetResult
)


class JogadorInline(admin.TabularInline):
    model = Jogador
    extra = 2


class SetResultInline(admin.TabularInline):
    model = SetResult
    extra = 1


@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'modalidade', 'local', 'data_inicio', 'status', 'owner')
    list_filter = ('status', 'modalidade')
    search_fields = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


@admin.register(RegraPontuacao)
class RegraPontuacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sets_para_vencer', 'pontos_por_set', 'tem_vantagem', 'limite_pontos_diretos')


@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'torneio')
    list_filter = ('torneio',)
    inlines = [JogadorInline]


@admin.register(Fase)
class FaseAdmin(admin.ModelAdmin):
    list_display = ('nome', 'torneio', 'tipo', 'ordem', 'regra', 'equipes_avancam')
    list_filter = ('torneio', 'tipo')


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'fase')
    filter_horizontal = ('equipes',)


@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'is_wo', 'ordem_cronograma')
    list_filter = ('status', 'fase')
    inlines = [SetResultInline]
```

---

## 9\. Admin do Usuário Customizado (apps/users/admin.py)

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Dados Adicionais', {'fields': ('telefone',)}),
    )
```

---

## 10\. URLs Base (config/urls.py)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
]
```

---

## 11\. Checklist de Conclusão da Fase 1

Antes de avançar para a Fase 2, confirmar que:

* \[ \] `docker-compose up` sobe sem erros

* \[ \] Banco PostgreSQL conecta corretamente

* \[ \] `python manage.py migrate` aplica todas as migrações sem erros

* \[ \] `python manage.py createsuperuser` cria o admin

* \[ \] Acesso ao `/admin` funciona

* \[ \] É possível criar um `Torneio` pelo admin

* \[ \] É possível criar uma `RegraPontuacao` pelo admin

* \[ \] É possível criar `Equipe` com `Jogadores` pelo admin

* \[ \] É possível criar `Fase` vinculada a uma `RegraPontuacao`

* \[ \] É possível criar `Grupo` e associar equipes

* \[ \] É possível criar `Partida` e lançar `SetResult` pelo admin

---

## Observações Importantes para o Agente

1. **AUTH_USER_MODEL deve ser definido ANTES da primeira migração.** Nunca alterar depois sem resetar o banco.

2. **Slug do Torneio** deve ser único e gerado automaticamente a partir do nome, com tratamento de colisão (sufixo numérico).

3. **Partida FINALIZADA** não pode ser editada — essa validação será implementada nas views (Fase 3), mas o model já está preparado com o campo `status`.

4. **W.O.** usa os campos `is_wo` e `vencedor_wo`. A lógica de calcular o placar automático (ex: 21x0) será implementada no `services.py` da Fase 3.

5. **Multitenancy:** O `TorneioAdmin` já filtra por `owner`. Nas views (Fase 2+), sempre filtrar com `torneio__owner=request.user`.