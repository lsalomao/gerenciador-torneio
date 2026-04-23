# Plano de Execução — Fase 6.3: Integração de Dados e Polling (Lógica Viva)

## Objetivo da Fase 6.3

Transformar o layout estático da Fase 6.2 em uma interface dinâmica que se atualiza sozinha. Nesta fase, conectamos o Dashboard aos endpoints JSON da Fase 6.1 e implementamos o sistema de batimento cardíaco (Polling) que mantém os dados frescos.

---

## Pré-requisitos (Fases 6.1 e 6.2 concluídas)

* Layout base (HTML/CSS) com mocks pronto.

* Endpoints JSON `/api/v1/public/...` retornando dados reais do banco.

---

## 1\. Estratégia de Atualização (HTMX vs JS Puro)

Para o MVP, utilizaremos **JavaScript Puro (fetch API)** ou **HTMX** para manter a lógica simples e eficiente.

### Fluxo de Polling

1. O template carrega com o valor de `polling_interval` do banco.

2. Um timer JavaScript dispara a cada N segundos.

3. Duas chamadas assíncronas são feitas:

  * `fetch('/api/v1/public/torneio/<slug>/dashboard/')`

  * `fetch('/api/v1/public/torneio/<slug>/live/')`

4. O backend processa e devolve o JSON.

5. O frontend atualiza **apenas os fragmentos** necessários do DOM (nomes, placares, posições na tabela).

---

## 2\. Lógica Dinâmica da Coluna Esquerda

### Detecção de Fase

* Se o JSON indicar mudança de fase (ex: mudou de GRUPO para ELIMINATORIA):

  * O frontend deve trocar o container exibido (limpar tabela e mostrar confrontos).

### Destaque de Grupo (Fase de Grupos)

* Ao iterar pelos grupos, verificar qual equipe está no objeto `live_match`.

* Aplicar a classe CSS de destaque (borda laranja/sombra) no grupo correspondente.

### Ordenação da Tabela

* A tabela deve refletir a ordem exata enviada pelo `ranking_service` (já calculada no backend).

* Se uma equipe subir ou descer de posição após um jogo, ela deve ser renderizada na nova ordem.

---

## 3\. Lógica Dinâmica da Coluna Direita (Placar/Destaque)

### Prioridade de Exibição

O JavaScript deve seguir esta regra ao receber os dados:

1. **Se `live_match` (status AO_VIVO) existir:**

  * Esconder o container "Próximo Jogo".

  * Mostrar o container "Placar Real".

  * Atualizar Sets Ganhos (A vs B) e Pontos do Set Atual (A vs B).

  * Ativar animação pulsante no badge "AO VIVO".

2. **Se `live_match` NÃO existir:**

  * Esconder o container "Placar Real".

  * Mostrar o container "Próximo Jogo" (fallback para o agendado).

---

## 4\. Implementação do Polling (Padrão de Código)

```javascript
// Exemplo da lógica a ser implementada no template
const slug = "{{ torneio.slug }}";
const interval = {{ torneio.polling_interval }} * 1000;

function updateDashboard() {
    fetch(`/api/v1/public/torneio/${slug}/dashboard/`)
        .then(response => response.json())
        .then(data => {
            // Atualiza Títulos, Fase e Coluna Esquerda
            renderSidebar(data); 
        });

    fetch(`/api/v1/public/torneio/${slug}/live/`)
        .then(response => response.json())
        .then(data => {
            // Atualiza Placar ou Próximo Jogo
            renderLivePanel(data);
        });
}

setInterval(updateDashboard, interval);
```

---

## 5\. Fallbacks e Tratamento de Erros

* **Erro de conexão:** Se o fetch falhar (internet caiu no local), manter os últimos dados na tela (não mostrar erro feio pro público).

* **Dados vazios:** Se o torneio não tiver jogos, mostrar "Aguardando definição de tabela".

---

## 6\. Critérios de Pronto (Definition of Done)

* \[ \] O dashboard carrega os dados reais do banco no primeiro load.

* \[ \] O timer de atualização (setInterval) respeita o tempo definido no banco de dados.

* \[ \] O placar ao vivo atualiza os pontos sem necessidade de F5.

* \[ \] A tabela de classificação reflete mudanças de posição assim que um jogo é finalizado no Admin.

* \[ \] A troca entre "Ao Vivo" e "Próximo Jogo" acontece automaticamente quando o status da partida muda no backend.

* \[ \] O destaque do grupo (borda laranja) segue a equipe que está jogando no momento.

---

## Próximo Passo

Com os dados fluindo automaticamente, seguiremos para a **Fase 6.4: Transmissão e Polimento Final**, onde integraremos o bônus da live (Instagram) e faremos os ajustes finos de transição visual (animações leves).