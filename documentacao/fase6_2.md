# Plano de Execução — Fase 6.2: Layout Base (Template TV)

## Objetivo da Fase 6.2

Criar a estrutura visual do Dashboard Público (Modo TV), com layout de duas colunas, identidade visual definida e dados mockados. Nesta fase **não há integração com dados reais** — o objetivo é validar o layout antes de conectar os endpoints.

---

## Pré-requisitos (Fase 6.1 concluída)

- Campos `slug`, `polling_interval`, `live_url` e `is_ativa` criados e migrados
- Endpoints JSON funcionando e retornando dados corretos

---

## 1. URL e View

### URL
```
/torneio/<slug>/
```
Exemplo real:
```
torneio.ledtech.app/torneio/3F2504E04F8941D39A0C0305E82C3301
```

### View
- View pública (sem login)
- Busca o torneio pelo `slug`
- Retorna 404 se não encontrado
- Passa para o template:
  - `torneio` (objeto)
  - `polling_interval` (em milissegundos: valor do banco × 1000)
  - `live_url` (pode ser None)

---

## 2. Identidade Visual

### Paleta de Cores
- **Fundo geral:** Azul escuro (`#0D1B2A` ou similar)
- **Coluna esquerda (tabela):** Fundo levemente mais claro (`#1A2B3C`)
- **Coluna direita (ao vivo):** Fundo escuro com destaque laranja
- **Destaque AO VIVO:** Laranja (`#FF6B00`)
- **Texto principal:** Branco (`#FFFFFF`)
- **Texto secundário:** Cinza claro (`#A0AEC0`)
- **Classificado (badge):** Verde (`#38A169`)
- **Eliminado (badge):** Cinza (`#718096`)
- **Em disputa (badge):** Amarelo (`#D69E2E`)

### Tipografia
- Fonte principal: `Inter` ou `Roboto` (Google Fonts)
- Tamanhos pensados para leitura à distância (TV projetada):
  - Título da fase: `2rem`
  - Nome das equipes: `1.5rem`
  - Placar ao vivo: `4rem` (destaque máximo)
  - Colunas da tabela: `1rem`
  - Labels/legendas: `0.85rem`

---

## 3. Estrutura do Layout

### Regras gerais
- **Sem header de navegação** (sem menu, sem logo de sistema, sem botões)
- **Sem scroll** — tudo deve caber na tela (projetado para 1920×1080)
- **Full screen por padrão** — usar `height: 100vh`
- Responsividade não é prioridade no MVP (foco em TV/projetor)

### Estrutura HTML (macro)

```
┌─────────────────────────────────────────────────────────────┐
│                    NOME DO TORNEIO                          │
│                    NOME DA FASE ATIVA                       │
├──────────────────────────────┬──────────────────────────────┤
│                              │                              │
│   COLUNA ESQUERDA            │   COLUNA DIREITA             │
│   (60% da largura)           │   (40% da largura)           │
│                              │                              │
│   [Fase Grupos]              │   [Jogo AO VIVO]             │
│   Tabelas de classificação   │   ou                         │
│   empilhadas por grupo       │   [Próximo Jogo]             │
│                              │                              │
│   [Fase Eliminatória]        │                              │
│   Lista de confrontos        │                              │
│                              │                              │
├──────────────────────────────┴──────────────────────────────┤
│   [BÔNUS] Área da Live (iframe) — exibir só se live_url     │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Componentes Visuais (com dados mockados)

### 4.1 Header do Dashboard
- Nome do torneio (centralizado, destaque)
- Nome da fase ativa (subtítulo)
- Indicador pulsante "🔴 AO VIVO" (visível apenas quando houver jogo ao vivo)

---

### 4.2 Coluna Esquerda — Fase de Grupos

Exibir grupos empilhados verticalmente.

**Card de Grupo:**
- Título: "GRUPO A", "GRUPO B", etc.
- Destaque visual (borda laranja) no grupo que contém o jogo ao vivo
- Tabela de classificação com colunas:

| Pos | Equipe | J | V | D | SG | SP |
|-----|--------|---|---|---|----|----|

Legenda das colunas:
- J = Jogos
- V = Vitórias
- D = Derrotas
- SG = Saldo de Sets
- SP = Saldo de Pontos

Badge de posição:
- 🟢 Verde → classificado (baseado em `equipes_avancam`)
- 🟡 Amarelo → em disputa
- ⚫ Cinza → eliminado

---

### 4.3 Coluna Esquerda — Fase Eliminatória

Lista vertical de confrontos da fase ativa.

**Card de Confronto:**
```
┌─────────────────────────────────────┐
│  Quartas 1                          │
│  Equipe A    2  ×  1    Equipe B    │
│  [FINALIZADO]                       │
└─────────────────────────────────────┘
```

Estados visuais:
- `AGENDADA` → placar oculto, exibir horário
- `AO_VIVO` → placar em destaque laranja + badge pulsante
- `FINALIZADA` → placar normal + badge cinza "Finalizado"

---

### 4.4 Coluna Direita — Jogo AO VIVO

```
┌─────────────────────────────────────┐
│         🔴 AO VIVO                  │
│                                     │
│   EQUIPE A        EQUIPE B          │
│                                     │
│      2        ×       1             │
│   (sets ganhos)   (sets ganhos)     │
│                                     │
│   Set atual:  18  ×  15             │
│                                     │
└─────────────────────────────────────┘
```

Detalhes:
- Nome das equipes: fonte grande e bold
- Sets ganhos: destaque visual (ex: bolinhas preenchidas ●●○)
- Pontuação do set atual: maior fonte da tela (`4rem`)
- Badge "AO VIVO" com animação de pulso (CSS)

---

### 4.5 Coluna Direita — Próximo Jogo (Fallback)

Exibido quando não há jogo `AO_VIVO`:

```
┌─────────────────────────────────────┐
│         PRÓXIMO JOGO                │
│                                     │
│   EQUIPE A    VS    EQUIPE B        │
│                                     │
│   Jogo 3 • Grupo B                  │
│                                     │
└─────────────────────────────────────┘
```

---

### 4.6 Rodapé — Live (Bônus)

Exibir apenas se `torneio.live_url` estiver preenchido:
- Iframe ou link da transmissão
- Altura fixa (ex: `200px`)
- Não deve comprometer o layout principal

---

## 5. Dados Mockados para Desenvolvimento

O agente deve criar um **context mockado** no template ou na view para desenvolver e validar o layout sem depender dos endpoints reais.

Exemplo de estrutura mockada:
- 2 grupos com 4 equipes cada
- 1 jogo ao vivo no Grupo A
- Classificação com posições variadas (classificado, em disputa, eliminado)

---

## 6. Critérios de Pronto (Definition of Done)

- [ ] URL `/torneio/<slug>/` acessível sem login
- [ ] Layout de duas colunas implementado (60/40)
- [ ] Header com nome do torneio e fase ativa
- [ ] Tabela de classificação com badges de posição (dados mockados)
- [ ] Card de jogo ao vivo com placar grande (dados mockados)
- [ ] Card de próximo jogo (fallback, dados mockados)
- [ ] Card de confronto eliminatório (dados mockados)
- [ ] Sem header/menu de sistema
- [ ] Tela ocupa 100vh sem scroll
- [ ] Badge "AO VIVO" com animação de pulso

---

## Próximo Passo

Após validar o layout com dados mockados, seguiremos para a **Fase 6.3: Integração Dados + Polling**, onde substituiremos os mocks pelos endpoints JSON reais e implementaremos a atualização automática.