# Gerenciador de Torneio — Instruções para Fase 3/4

Este README descreve como preparar o ambiente local, aplicar migrações e executar os testes para as implementações da Fase 3 e Fase 4 (lançamento de resultados, W.O., validação e ranking de grupos).

**Resumo das ações adicionadas**
- Serviços: `validation_service`, `match_service`, `wo_service`, `ranking_service`, `confronto_direto_service`.
- Views/templates: edição de partida com sets, confirmação de iniciar partida, aplicar W.O., tela de classificação do grupo.
- Validações de modelo: `SetResult.clean/save/delete` e `Partida.save` para garantir integridade após finalização.
- Testes unitários: `test_match_services.py`, `test_ranking_service.py`.

**Observação importante sobre migrações**
As alterações realizadas são majoritariamente implementações de serviços, views, templates e validações no nível do modelo (métodos `save()`/`clean()`) — não foram adicionados novos campos de modelo. Portanto, normalmente não é necessário criar novas migrações. Caso o seu repositório local detecte alterações de esquema, execute os passos abaixo para gerar as migrações.

**Requisitos locais**
- Python 3.10+ (o projeto foi testado com Python 3.11/3.14).
- Dependências listadas em `requirements.txt`.

Passos rápidos (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configurar banco de dados local (opções):

- Recomendo usar SQLite em desenvolvimento local para simplificar execução de testes e migrações. No arquivo `config/settings.py`, ajuste `DATABASES` para:

```python
# Exemplo (modo local, dev):
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

- Alternativamente, se você usa Docker/Compose com Postgres, certifique-se de que o host `db` esteja resolvível (container PostgreSQL em execução). O erro comum ao rodar testes localmente é "could not translate host name 'db' to address" — isso significa que seu ambiente não tem o container `db` acessível.

Gerar migrações e aplicar (se necessário):

```powershell
python manage.py makemigrations
python manage.py migrate
```

Criar superuser (para acessar área administrativa):

```powershell
python manage.py createsuperuser
```

Executar testes (todos):

```powershell
python manage.py test
```

Executar apenas os testes do core (mais rápido):

```powershell
python manage.py test apps.core -v 2
```

Executar servidor local:

```powershell
python manage.py runserver
```

Verificações úteis
- Se os testes falharem com erro do tipo `OperationalError: could not translate host name "db"`, verifique `DATABASES` em `config/settings.py` e ajuste para SQLite para execução local.
- Se `makemigrations` detectar alterações inesperadas de esquema, revise `apps/core/models.py` para confirmar se as mudanças de campo foram intencionais.

O que eu posso gerar a seguir (opções):
- Gerar migrações exemplares (manuais) se preferir um commit de migrações preparado.
- Instruções de deploy/Docker Compose para garantir que o host `db` esteja disponível durante testes.
- Documentação da API/Views adicionadas da Fase 3/4.

Informe qual opção prefere e eu continuo.

Executando com Docker Compose
-----------------------------

Use os comandos abaixo para rodar a aplicação em containers, aplicar migrações e executar testes dentro do serviço `web`.

1. Build e subir containers (background):

```powershell
docker compose up -d --build
```

2. Aplicar migrações dentro do container `web`:

```powershell
docker compose exec web python manage.py migrate
```

3. Criar superuser (interativo):

```powershell
docker compose exec web python manage.py createsuperuser
```

4. Rodar coletor de arquivos estáticos (se necessário):

```powershell
docker compose exec web python manage.py collectstatic --noinput
```

5. Executar testes dentro do container (mais rápido para CI/local):

```powershell
docker compose exec web python manage.py test apps.core -v 2
```

Resolução de problemas comuns
- Erro "could not translate host name 'db'": significa que o serviço de banco de dados não está acessível no hostname `db`. Certifique-se de que o serviço do banco (ex.: `db` no `docker-compose.yml`) esteja up:

```powershell
docker compose up -d db
```

- Alguns containers esperam o banco ficar pronto. Se `migrate` falhar por causa de timeout, aguarde o DB e reexecute o migrate, ou use um pequeno script de espera dentro do container `web` antes de rodar `manage.py`.
```