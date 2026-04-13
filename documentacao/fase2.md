# Plano de Execução — Fase 2: Grupos e Geração de Partidas (Round Robin)

## Objetivo da Fase 2

Tornar o torneio “operável” após o cadastro base (Fase 1), permitindo:

1. Montar grupos (manual e/ou sorteio aleatório)

2. Gerar automaticamente os jogos “todos contra todos” dentro de cada grupo (Round Robin)

3. Definir o cronograma linear (quadra única) via ordenação

4. Implementar “Resetar Fase” com regras de segurança (não permitir se houver partidas finalizadas)

> Importante: Nesta fase **não** implementamos lançamento de resultados (isso é Fase 3). Aqui a partida nasce “AGENDADA”.

---

## Pré-requisitos (Fase 1 concluída)

* Projeto sobe via Docker + PostgreSQL

* Models criados e migrados:

  * Torneio, RegraPontuacao, Fase, Grupo, Equipe, Jogador, Partida, SetResult

* Multitenancy base:

  * Torneio tem `owner`

  * Views/queries sempre filtram por `torneio__owner=request.user`

---

## Escopo e Entidades Envolvidas

### Entidades usadas diretamente

* `Torneio`

* `Fase` (somente tipo `GRUPO` nesta fase)

* `Grupo`

* `Equipe`

* `Partida`

### O que NÃO entra no escopo

* Cálculo de classificação e desempate

* Lançamento e validação de placares (sets)

* Eliminatória / bracket

* Área pública

---

## Regras de Negócio (para o agente implementar sem ambiguidade)

### 1) Grupos existem apenas em fases do tipo GRUPO

* Só permitir criação/edição de grupos se `fase.tipo == 'GRUPO'`

### 2) Equipes são sempre do torneio da fase

* Ao associar equipes a um grupo, validar:

  * `equipe.torneio_id == fase.torneio_id`

### 3) Sorteio / Distribuição de Equipes

O sistema deve suportar 2 modos:

* **Manual**: ADM escolhe quais equipes entram em cada grupo

* **Aleatório**: sistema distribui automaticamente

Regras mínimas para aleatório:

* Distribuição balanceada (diferença de no máximo 1 equipe entre grupos)

* Sem duplicidade: uma equipe não pode estar em dois grupos na mesma fase

* Reprodutibilidade não é obrigatória no MVP (não precisa seed)

### 4) Geração de Partidas (Round Robin)

Para cada grupo:

* Gerar partidas para todos os pares possíveis (combinações) de equipes

* Não gerar jogo duplicado (A vs B e B vs A não podem coexistir)

* Não gerar jogo com mesma equipe (A vs A)

Estado inicial da partida:

* `status = 'AGENDADA'`

* `is_wo = False`

* `vencedor = None`

* `vencedor_wo = None`

### 5) Quadra única e cronograma linear

* Todas as partidas geradas devem receber `ordem_cronograma` sequencial

* A ordem pode ser simples (por grupo, depois por combinação), mas deve ser:

  * determinística

  * editável pelo ADM depois (via Admin ou tela futura)

### 6) Regeneração segura (Resetar Fase)

Implementar ação “Resetar Fase” para fases de grupo.

O reset deve:

* Remover (excluir) todas as `Partida` ligadas à fase (e seus `SetResult` por cascata)

* Opcional: remover grupos e recriar (ou apenas limpar a associação de equipes e manter grupos — decidir abaixo)

**Regra de bloqueio:**

* Se existir qualquer `Partida` da fase com `status='FINALIZADA'`, o reset deve ser bloqueado.

Decisão recomendada para MVP:

* Reset remove partidas e mantém grupos (mais simples)

* Limpa associações de equipes se a intenção é refazer sorteio (isso deve ser explícito em UI)

---

## Decisões de UI/UX (Admin Area)

> A fase 2 precisa de telas mínimas fora do Django Admin, ou pode iniciar pelo Admin.

Sugestão de abordagem para acelerar:

1. **Começar pelo Django Admin** para testar e validar as regras

2. Depois criar telas na “área administrativa” (templates) para operações do dia-a-dia

Mesmo que as telas venham depois, os **serviços** (camada de domínio) devem existir agora para evitar lógica no view.

---

## Estrutura técnica recomendada (sem código)

### 1) Criar um módulo de serviços no app `core`

Criar arquivo `apps/core/services/` com responsabilidades claras:

* `grouping_service`:

  * sortear equipes

  * validar distribuição

* `schedule_service`:

  * gerar round robin

  * atribuir ordem_cronograma

  * impedir duplicidade

* `phase_reset_service`:

  * validar se pode resetar

  * apagar partidas e limpar estrutura conforme regra

**Regras:**

* Serviço não deve depender de request/response

* Serviço deve receber ids/objects e retornar resultado estruturado (ex: números de jogos criados)

### 2) Views (Admin Area)

Criar views protegidas por login, sempre filtrando por owner.

Sugestão de telas:

1. **Tela da Fase (detalhe)**

* exibe: nome da fase, tipo, regra, grupos

* botões:

  * “Sortear equipes” (aleatório)

  * “Gerar partidas”

  * “Resetar fase”

1. **Tela de edição de grupos (manual)**

* selecionar equipes e alocar em grupos

### 3) Rotas (URLs)

Padrão sugerido (pode ajustar depois):

* `/admin-area/torneios/<id>/fases/<id>/` (detalhe)

* `/admin-area/fases/<id>/sortear/`

* `/admin-area/fases/<id>/gerar-partidas/`

* `/admin-area/fases/<id>/resetar/`

### 4) Templates

Tema claro:

* Primária: Azul

* Destaque/CTA: Laranja (contraste e legibilidade)

Componentes mínimos:

* card da fase

* tabela de grupos com equipes

* lista de partidas (com ordem)

* botões com estados (disabled quando bloqueado)

---

## Regras de Permissão e Multitenancy (obrigatórias)

Para qualquer operação (sortear, gerar partidas, resetar):

* Garantir que o usuário logado é o `owner` do torneio da fase

* Nunca aceitar ids “soltos” sem conferir a cadeia:

  * `fase.torneio.owner == request.user`

---

## Edge Cases e Validações (lista objetiva)

1. Fase do tipo ELIMINATORIA:

* não permitir grupos / sorteio / round robin

1. Grupo com < 2 equipes:

* não gerar partidas (retornar mensagem: “grupo precisa de pelo menos 2 equipes”)

1. Equipe em mais de um grupo:

* impedir (erro claro)

1. Partidas já geradas:

* impedir geração dupla, ou oferecer opção “resetar e gerar novamente”

* recomendação MVP: bloquear e pedir reset

1. Reset com partidas finalizadas:

* bloquear, informar quais partidas impedem o reset

1. Ordem do cronograma:

* garantir sequência sem buracos (1..N) ao gerar

---

## Critérios de Pronto (Definition of Done)

A Fase 2 está concluída quando:

* \[ \] ADM consegue montar grupos (manual ou aleatório)

* \[ \] Sistema gera partidas round robin corretamente para cada grupo

* \[ \] Partidas são criadas com `status=AGENDADA` e `ordem_cronograma` sequencial

* \[ \] Sistema impede gerar partidas duplicadas

* \[ \] Botão/ação “Resetar fase” funciona e apaga partidas

* \[ \] Reset é bloqueado se existir qualquer partida `FINALIZADA`

* \[ \] Todas as operações respeitam multitenancy (`owner`)

---

## Testes recomendados (mínimo viável)

### Unit Tests (serviços)

* Sorteio distribui equipes balanceado

* Round robin gera número correto de jogos:

  * Para N equipes no grupo, jogos = N\*(N-1)/2

* Não cria duplicidade

* Reset bloqueia com partidas finalizadas

### Integration Tests (views)

* Usuário não-owner não acessa endpoints

* Ações executam e persistem no banco

---

## Saída esperada para avançar para a Fase 3

Ao final da Fase 2, o sistema deve ter:

* Fase de grupos configurada

* Grupos preenchidos

* Partidas geradas e ordenadas

E estar pronto para:

* Lançamento de resultados set a set

* Validação por regra da fase

* Bloqueio de edição após finalização