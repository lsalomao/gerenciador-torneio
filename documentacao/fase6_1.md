# Plano de Execução — Fase 6.1: Fundação da Área Pública (Models e APIs)

## Objetivo da Fase 6.1

Preparar a infraestrutura de dados e os endpoints de API necessários para alimentar o Dashboard Público (TV). Esta fase foca na lógica de backend e disponibilidade de dados, sem implementar a interface visual ainda.

---

## 1\. Alterações nos Models (App: core)

### Model: Torneio

Adicionar campos para controle do Dashboard e Transmissão:

* `slug` (SlugField, unique=True): URL gerada com código aleatório (Guid) (ex: `torneio.ledtech.app/torneio/3F2504E04F8941D39A0C0305E82C3301`)

* `polling_interval` (IntegerField, default=10): Intervalo em segundos para atualização da TV.

* `live_url` (URLField, blank=True, null=True): Link para o iframe da live (Instagram/Youtube).

### Model: Fase

Adicionar controle de visibilidade:

* `is_ativa` (BooleanField, default=False): Define qual fase deve ser exibida no Dashboard.

* _Regra:_ Apenas uma fase deve estar ativa por torneio (validar no `save` ou via service).

---

## 2\. Endpoints de API (Públicos)

Criar Views que retornam JSON estruturado. **Importante:** Estes endpoints não exigem login.

### Endpoint A: Dashboard Data

URL: `/api/v1/public/torneio/<slug>/dashboard/`\
Retorna:

* Dados do Torneio (nome, live_url, polling_interval).

* Fase Ativa (ID, Nome, Tipo: GRUPO/ELIMINATORIA).

* Se for GRUPO:

  * Lista de grupos com classificação completa (reusando o `ranking_service` da Fase 4).

* Se for ELIMINATORIA:

  * Lista de confrontos da fase ativa.

### Endpoint B: Live/Highlight Data

URL: `/api/v1/public/torneio/<slug>/live/`\
Retorna os dados da coluna da direita:

* **Prioridade 1:** Partida com `status=AO_VIVO` (placar set a set, nomes, sets ganhos).

* **Prioridade 2 (Fallback):** Se não houver partida ao vivo, retornar a próxima partida com `status=AGENDADA` (baseado na `ordem_cronograma`).

---

## 3\. Lógica de Negócio (Services)

#### public_data_service (Novo)

* `get_active_phase(torneio)`: Busca a fase marcada como `is_ativa`. Se não houver, pega a primeira fase disponível.

* `get_current_highlight(torneio)`: Implementa a lógica de buscar o jogo Ao Vivo ou o Próximo.

* `get_dashboard_context(torneio)`: Consolida os dados para o endpoint JSON.

---

## 4\. Segurança e Multitenancy

* Embora os endpoints sejam **GET públicos**, eles devem ser "read-only".

* Impedir qualquer operação de escrita (POST/PATCH/DELETE) nestas URLs.

* Garantir que o filtro por `slug` seja exato.

---

## 5\. Critérios de Pronto (Definition of Done)

* \[ \] Campos `slug`, `polling_interval` e `live_url` adicionados ao Torneio.

* \[ \] Campo `is_ativa` adicionado à Fase com lógica de "apenas uma ativa".

* \[ \] Endpoint `/dashboard/` retornando JSON correto com classificação ou confrontos.

* \[ \] Endpoint `/live/` retornando corretamente o jogo ao vivo ou o próximo agendado.

* \[ \] Slug configurável no Django Admin.

---

## Próximo Passo

Após concluir esta base de dados, seguiremos para a **Fase 6.2: Layout Base (Template TV)**, onde criaremos a estrutura HTML/CSS de duas colunas.