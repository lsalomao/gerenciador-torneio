# Plano de Execução — Fase 3: Lançamento de Resultados, Validação e W.O.

## Objetivo da Fase 3

Permitir a operação real do torneio com lançamento de resultados por set, validação conforme regra da fase, definição automática do vencedor, suporte a W.O. e bloqueio de edição após finalização.

> Esta fase NÃO inclui classificação (Fase 4). Aqui garantimos a integridade do resultado de cada partida.

---

## Pré-requisitos (Fases 1 e 2 concluídas)

* Models criados e migrados

* Fases de grupo configuradas

* Grupos preenchidos

* Partidas geradas com `status=AGENDADA` e `ordem_cronograma`

* Multitenancy implementado (owner do torneio)

---

## Escopo

### Inclui

* Interface de lançamento de resultados (sets)

* Validação das regras de pontuação (por fase)

* Cálculo de sets ganhos e definição de vencedor

* Suporte a W.O. (vitória automática)

* Transições de status da partida

* Bloqueio de edição após finalização

### Não inclui

* Classificação/ranking (Fase 4)

* Eliminatória (Fase 5)

* Área pública (Fase 6)

---

## Regras de Negócio

### 1) Estados da Partida

Estados possíveis:

* `AGENDADA`

* `AO_VIVO`

* `FINALIZADA`

Transições válidas:

* AGENDADA → AO_VIVO

* AO_VIVO → FINALIZADA

Regras:

* Não permitir pular direto de AGENDADA → FINALIZADA sem resultado válido

* Após FINALIZADA: **nenhuma edição é permitida**

---

### 2) Lançamento de Sets

Para cada partida, permitir cadastrar múltiplos `SetResult`.

Regras:

* `numero_set` deve ser sequencial (1, 2, 3...)

* Não permitir sets duplicados

* Quantidade máxima de sets baseada em:

  * `sets_para_vencer * 2 - 1`

Exemplo:

* Melhor de 3 → máximo 3 sets

* Set único → máximo 1 set

---

### 3) Validação de Pontuação por Set

Baseado em `RegraPontuacao` da fase:

Campos relevantes:

* `pontos_por_set`

* `tem_vantagem`

* `limite_pontos_diretos`

#### Regras:

Para um set ser válido:

1. Um dos times deve atingir pelo menos `pontos_por_set`

2. Se `tem_vantagem = True`:

* Diferença mínima de 2 pontos

* Ex: 21x19 válido, 21x20 inválido

1. Se `limite_pontos_diretos` estiver definido:

* Ao atingir esse valor, vence direto

* Ex: limite 18 → 18x17 é válido mesmo sem diferença de 2

1. Não permitir empate (ex: 20x20 salvo como final)

---

### 4) Cálculo de Sets Ganhos

Para cada set:

* Comparar `pontos_a` vs `pontos_b`

* Incrementar sets do vencedor

Após cada inserção/edição de set:

* Recalcular:

  * sets ganhos por equipe

---

### 5) Definição de Vencedor da Partida

Baseado em `sets_para_vencer`:

* Quando uma equipe atingir esse número de sets:

  * Definir `vencedor`

  * Atualizar status → `FINALIZADA`

Regras:

* Não permitir sets extras após já existir vencedor

* Não permitir finalizar manualmente sem vencedor válido

---

### 6) W.O. (Walkover)

Permitir marcar partida como W.O.

Campos:

* `is_wo = True`

* `vencedor_wo` definido

Regras:

* Ao marcar W.O.:

  * Ignorar sets

  * Definir vencedor automaticamente

  * Gerar placar lógico (não precisa salvar sets fisicamente no MVP)

Pontuação sugerida:

* Usar `pontos_por_set` da regra

* Ex: 21x0 ou 15x0

Status:

* W.O. → `FINALIZADA`

---

### 7) Bloqueio de Edição

Após `status = FINALIZADA`:

Bloquear:

* edição de sets

* alteração de vencedor

* alteração de W.O.

Implementação:

* validação no backend (não confiar só no frontend)

---

## Estrutura Técnica Recomendada

### 1) Services (apps/core/services)

Criar serviços específicos:

#### match_service

Responsável por:

* validar sets

* calcular sets ganhos

* definir vencedor

* mudar status

#### wo_service

Responsável por:

* aplicar W.O.

* definir vencedor

* atribuir lógica de placar

#### validation_service

Responsável por:

* validar regras de pontuação

* garantir integridade dos sets

Regras gerais:

* serviços não dependem de request

* recebem entidades ou IDs

* retornam resultado estruturado (success/error + mensagem)

---

### 2) Views (Admin Area)

Criar telas protegidas por login:

#### Tela de Partida (detalhe)

Exibir:

* equipes

* status

* sets lançados

Ações:

* iniciar partida (AGENDADA → AO_VIVO)

* lançar sets

* finalizar automaticamente

* marcar W.O.

---

### 3) Formulários

Criar form dinâmico para sets:

Campos:

* número do set

* pontos equipe A

* pontos equipe B

Validações no backend obrigatórias

---

## Regras de Permissão

Para qualquer operação:

* validar:

  * `partida.fase.torneio.owner == request.user`

Bloquear acesso caso contrário

---

## Edge Cases

1. Inserir set após partida finalizada\
  → bloquear

2. Inserir set inválido (ex: 21x20 com vantagem)\
  → erro claro

3. Inserir sets além do necessário\
  → bloquear

4. Marcar W.O. com sets já lançados\
  → limpar sets ou bloquear (recomendado: bloquear)

5. Remover sets e quebrar consistência\
  → impedir remoção se comprometer resultado

---

## Critérios de Pronto (Definition of Done)

* \[ \] ADM consegue iniciar partida

* \[ \] ADM consegue lançar sets válidos

* \[ \] Sistema valida regras de pontuação corretamente

* \[ \] Sistema define vencedor automaticamente

* \[ \] Sistema finaliza partida ao atingir sets necessários

* \[ \] W.O. funciona corretamente

* \[ \] Não é possível editar partida finalizada

* \[ \] Todas as operações respeitam multitenancy

---

## Testes Recomendados

### Unit

* validação de set com vantagem

* validação com limite direto

* cálculo de sets

* definição de vencedor

* W.O.

### Integration

* fluxo completo: AGENDADA → AO_VIVO → FINALIZADA

* bloqueio após finalização

---

## Saída Esperada para Fase 4

Ao final da Fase 3, o sistema deve:

* Ter partidas com resultados completos

* Ter vencedores definidos

* Estar pronto para cálculo de classificação automática