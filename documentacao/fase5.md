# Plano de Execução — Fase 5: Fase Eliminatória (Bracket) e Cruzamento Inteligente

## Objetivo da Fase 5

Implementar a geração da fase eliminatória (Mata-Mata) após a conclusão da fase de grupos, utilizando a lógica de cruzamento inteligente (Melhor 1º vs Pior 2º) e garantindo a disputa de 3º lugar.

---

## Pré-requisitos (Fases 1 a 4 concluídas)

* Ranking dos grupos consolidado e confiável

* Definição clara de quantas equipes avançam (`equipes_avancam`)

* Resultados e estatísticas da fase de grupos finalizados

---

## Escopo

### Inclui

* Seleção e rankeamento global dos classificados da fase de grupos

* Lógica de cruzamento inteligente (Seed)

* Geração automática das partidas de Quartas, Semi, Final e 3º Lugar

* Interface para visualização da chave (Bracket) na área administrativa

### Não inclui

* Exibição pública da chave (Fase 6)

* Lançamento de resultados (já implementado na Fase 3 para qualquer partida)

---

## Regras de Negócio

### 1) Seleção de Classificados

O sistema deve identificar as equipes que avançam de cada grupo baseado no campo `equipes_avancam` da `Fase` anterior (Grupos).

Regras:

* Se `equipes_avancam = 2`, pegar o 1º e o 2º lugar de cada grupo.

* Validar se todos os grupos da fase anterior estão com todas as partidas `FINALIZADAS` antes de permitir gerar a eliminatória.

### 2) Ranking Geral de Classificados (Seed)

Para realizar o cruzamento inteligente, o sistema deve criar um ranking global entre os classificados para definir quem é o "Melhor 1º", "Segundo Melhor 1º", etc.

Critérios globais (aplicados aos classificados de grupos diferentes):

1. **% de Vitórias** (Vitórias / Jogos) — necessário pois grupos podem ter tamanhos diferentes

2. **Média de Saldo de Sets** (Saldo de Sets / Jogos)

3. **Média de Saldo de Pontos** (Saldo de Pontos / Jogos)

4. Sorteio (caso persista empate absoluto)

### 3) Lógica de Cruzamento Inteligente

O cruzamento deve privilegiar as equipes com melhor campanha.

Padrão para 8 equipes (Quartas de Final):

* Jogo 1: Melhor 1º (P1) vs Pior 2º (P8)

* Jogo 2: 4º Melhor Qualificado (P4) vs 5º Melhor Qualificado (P5)

* Jogo 3: 2º Melhor Qualificado (P2) vs 7º Melhor Qualificado (P7)

* Jogo 4: 3º Melhor Qualificado (P3) vs 6º Melhor Qualificado (P6)

Regras:

* O cruzamento deve ser montado de forma que o Melhor 1º e o Segundo Melhor 1º só se enfrentem na Final.

* Caso o torneio tenha menos ou mais times, a lógica de "Melhor vs Pior" deve ser mantida proporcionalmente.

### 4) Gestão de Fases Eliminatórias

As fases eliminatórias seguem a ordem:

* Quartas de Final (se houver times suficientes)

* Semifinal

* Disputa de 3º Lugar (Perdedor Semi 1 vs Perdedor Semi 2)

* Final (Vencedor Semi 1 vs Vencedor Semi 2)

Regras:

* O sistema deve gerar a rodada seguinte automaticamente à medida que as partidas da rodada atual forem sendo finalizadas (ou permitir geração manual da rodada).

### 5) Disputa de 3º Lugar (Obrigatória)

* Deve ser gerada simultaneamente ou antes da Final.

* Serve para definição de pódio e permitir descanso aos finalistas.

---

## Estrutura Técnica Recomendada

### 1) Services (apps/core/services)

#### bracket_service

Responsável por:

* Buscar classificados da fase anterior.

* Calcular o ranking global (Seed).

* Montar os pares conforme a lógica Melhor vs Pior.

* Criar os objetos `Partida` na nova `Fase` (tipo ELIMINATORIA).

#### advancement_service

Responsável por:

* Monitorar partidas eliminatórias.

* Ao finalizar uma Semi, identificar perdedores para o 3º lugar e vencedores para a Final.

---

### 2) Views (Admin Area)

#### Tela de Bracket

Visualização em árvore ou colunas:

* Coluna 1: Quartas

* Coluna 2: Semifinais

* Coluna 3: Final / 3º Lugar

---

## Edge Cases

1. Número de grupos ímpar ou desigual\
  → A média (divisão por jogos) no ranking global de Seed resolve a diferença de tamanho de grupos.

2. Bye (Folga)\
  → Se o número de classificados não for potência de 2 (4, 8, 16), o sistema deve atribuir "Bye" aos melhores classificados (avançam direto). _Sugestão: No MVP focar em números pares 4 ou 8._

3. Reset da Eliminatória\
  → Seguir a mesma regra da fase de grupos: só permite resetar se não houver resultados finalizados na fase eliminatória.

---

## Critérios de Pronto (Definition of Done)

* \[ \] Ranking global de classificados (Seed) calculado corretamente.

* \[ \] Partidas de Quartas/Semi geradas com cruzamento inteligente.

* \[ \] Partida de 3º lugar gerada automaticamente.

* \[ \] Partida da Final gerada automaticamente com os vencedores das Semis.

* \[ \] Visualização da chave funcional no Admin.

---

## Testes Recomendados

* Ranking global (Seed) com grupos de tamanhos diferentes.

* Confirmação de que o Melhor 1º enfrenta o pior qualificado.

* Verificação da geração de 3º lugar após conclusão das Semis.