# Plano de Execução — Fase 4: Classificação e Desempate

## Objetivo da Fase 4

Implementar o motor de classificação automático dos grupos, calculando o ranking de cada equipe com base nos resultados das partidas finalizadas, aplicando os critérios de desempate definidos nas regras de negócio.

> Esta fase NÃO inclui a geração da chave eliminatória (Fase 5). Aqui garantimos que o ranking de cada grupo está correto e atualizado.

---

## Pré-requisitos (Fases 1, 2 e 3 concluídas)

* Partidas geradas com Round Robin

* Resultados lançados com sets válidos

* Vencedores definidos por partida

* W.O. funcionando corretamente

---

## Escopo

### Inclui

* Cálculo de estatísticas por equipe dentro do grupo

* Ordenação por critérios de desempate

* Tratamento de empate duplo e triplo

* Atualização automática ao finalizar partida

* Exibição da tabela de classificação na área administrativa

### Não inclui

* Geração da chave eliminatória (Fase 5)

* Exibição pública (Fase 6)

* Classificação em fases eliminatórias

---

## Regras de Negócio

### 1) Estatísticas por Equipe (por grupo)

Para cada equipe dentro de um grupo, calcular:

* `jogos` → total de partidas finalizadas

* `vitorias` → partidas vencidas

* `derrotas` → partidas perdidas

* `sets_ganhos` → total de sets vencidos

* `sets_perdidos` → total de sets perdidos

* `saldo_sets` → sets_ganhos - sets_perdidos

* `pontos_feitos` → total de pontos marcados em todos os sets

* `pontos_tomados` → total de pontos sofridos em todos os sets

* `saldo_pontos` → pontos_feitos - pontos_tomados

Regras:

* Considerar apenas partidas com `status = FINALIZADA`

* W.O. deve ser contabilizado normalmente (vencedor ganha, perdedor perde)

* Pontos do W.O. devem ser calculados com base na regra da fase (ex: 21x0)

---

### 2) Critérios de Ranking (ordem de aplicação)

Aplicar na seguinte ordem:

1. **Vitórias** (maior número)

2. **Saldo de Sets** (maior saldo)

3. **Saldo de Pontos** (maior saldo)

4. **Confronto Direto** (resultado entre os empatados)

Regras:

* Só avançar para o próximo critério se ainda houver empate

* Confronto direto: comparar apenas as partidas entre as equipes empatadas

---

### 3) Empate Duplo (2 equipes)

Se após vitórias ainda houver empate entre 2 equipes:

1. Saldo de Sets

2. Saldo de Pontos

3. Confronto Direto entre as duas

---

### 4) Empate Triplo (3 ou mais equipes)

Se após vitórias houver empate entre 3 ou mais equipes:

Aplicar subcritérios apenas entre as equipes empatadas:

1. Confronto direto entre elas (mini-tabela)

2. Pontos feitos (entre elas)

3. Pontos tomados (entre elas)

4. Saldo de pontos (entre elas)

Regras:

* Calcular mini-tabela apenas com as partidas entre as equipes empatadas

* Se ainda houver empate após todos os critérios: manter ordem atual (não é necessário critério extra no MVP)

---

### 5) Atualização Automática

O ranking deve ser recalculado sempre que:

* Uma partida for finalizada

* Um W.O. for aplicado

Implementação recomendada:

* Chamar o serviço de classificação ao final de qualquer operação que mude o status de uma partida para `FINALIZADA`

* Não armazenar ranking em banco (calcular sempre em tempo real no MVP)

> Justificativa: Com poucos times por grupo (torneios amadores), o cálculo em tempo real é rápido e evita inconsistências de cache.

---

## Estrutura Técnica Recomendada

### 1) Services (apps/core/services)

Criar serviço específico:

#### ranking_service

Responsável por:

* receber um `Grupo`

* calcular estatísticas de cada equipe

* aplicar critérios de desempate

* retornar lista ordenada de equipes com suas estatísticas

Regras:

* Serviço puro (sem dependência de request/response)

* Recebe objeto `Grupo` ou `grupo_id`

* Retorna lista de dicionários ou dataclasses com:

  * equipe

  * posição

  * jogos, vitórias, derrotas

  * sets_ganhos, sets_perdidos, saldo_sets

  * pontos_feitos, pontos_tomados, saldo_pontos

#### confronto_direto_service

Responsável por:

* receber lista de equipes empatadas e o grupo

* filtrar apenas as partidas entre essas equipes

* calcular mini-ranking entre elas

* retornar ordem de desempate

---

### 2) Views (Admin Area)

#### Tela de Classificação do Grupo

Exibir:

* Tabela com posição, equipe e estatísticas

* Indicação visual de quem avança (baseado em `fase.equipes_avancam`)

Atualização:

* Recalcular ao carregar a página (sem polling nesta tela)

---

### 3) Templates

Componentes necessários:

* Tabela de classificação com colunas:

  * Pos | Equipe | J | V | D | SG | SP | PF | PT | Pts (se aplicável)

* Badge visual:

  * Verde → classificado

  * Cinza → eliminado

  * Amarelo → em disputa

---

## Regras de Permissão

* Tela de classificação da área administrativa:

  * Apenas usuário logado e owner do torneio

* Cálculo de ranking:

  * Sempre validar que o grupo pertence ao torneio do usuário logado

---

## Edge Cases

1. Grupo sem partidas finalizadas\
  → exibir equipes sem estatísticas (zeradas), sem erro

2. Grupo com partidas parcialmente finalizadas\
  → calcular apenas com as finalizadas, ignorar agendadas/ao vivo

3. Empate triplo com mini-tabela incompleta (nem todas as partidas entre empatados foram finalizadas)\
  → aplicar critérios apenas com os dados disponíveis, sem travar o sistema

4. W.O. no cálculo de pontos\
  → usar pontuação máxima da regra da fase (ex: 21x0) para contabilizar pontos feitos/tomados

5. Grupo com apenas 2 equipes\
  → funcionar normalmente, sem tentar aplicar empate triplo

6. Reset de fase após classificação calculada\
  → ao resetar, o ranking simplesmente deixa de existir (calculado em tempo real, não há o que limpar)

---

## Critérios de Pronto (Definition of Done)

* \[ \] Estatísticas calculadas corretamente por equipe

* \[ \] Ranking ordenado por vitórias

* \[ \] Desempate por saldo de sets aplicado corretamente

* \[ \] Desempate por saldo de pontos aplicado corretamente

* \[ \] Confronto direto aplicado corretamente (duplo e triplo)

* \[ \] W.O. contabilizado corretamente nas estatísticas

* \[ \] Tabela exibida na área administrativa

* \[ \] Indicação visual de classificados por grupo

* \[ \] Ranking recalculado automaticamente ao finalizar partida

---

## Testes Recomendados

### Unit (ranking_service)

* Grupo com 4 equipes, sem empate → ordenação por vitórias

* Empate duplo → desempate por saldo de sets

* Empate duplo → desempate por confronto direto

* Empate triplo → mini-tabela correta

* W.O. contabilizado nos pontos

### Integration

* Finalizar partida → ranking atualiza

* Tela de classificação exibe dados corretos

---

## Saída Esperada para Fase 5

Ao final da Fase 4, o sistema deve:

* Ter ranking correto e confiável por grupo

* Saber quais equipes estão classificadas (baseado em `fase.equipes_avancam`)

* Estar pronto para:

  * Selecionar os classificados

  * Gerar o cruzamento inteligente da fase eliminatória