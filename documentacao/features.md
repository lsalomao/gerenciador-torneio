# Gerenciador de Torneio - Especificação de Features (MVP)

Sistema web para gerenciamento de torneios esportivos genéricos com foco inicial em Vôlei de Praia, Futevôlei e Beach Tennis.

## 1. Feature: Autenticação e Usuários (Auth)
- **Login / Logout:** Sistema restrito para Administradores (ADMs).
- **Isolamento por Proprietário:** Cada ADM gerencia apenas seus próprios torneios, equipes e partidas.
- **Multitenancy:** O Django filtará as consultas (queries) baseado no usuário logado.

## 2. Feature: Gerenciamento de Torneios
- **Configurações Básicas:** Nome, Modalidade, Local, Data, Horário de Início e Slug (para URL pública).
- **Parâmetros do Torneio:** Quantidade de jogadores por equipe (definida individualmente por torneio).
- **Gerenciamento de Regras por Fase:** Permite que diferentes fases (Grupos, Quartas, Final) tenham regras de pontuação distintas.
- **Ciclo de Vida (Status):**
    - `Criação`: Configuração inicial.
    - `Inscrições`: Cadastro e edição de equipes.
    - `Em andamento`: Lançamento de placares (edição de equipes continua permitida).
    - `Encerrado`: Torneio finalizado para visualização histórica.

## 3. Feature: Regras de Pontuação (Flexíveis)
- **Configuração de Set:** Quantidade de sets por partida (Ex: Set único ou melhor de 3).
- **Pontuação:** Pontos necessários para fechar o set.
- **Lógica de Desempate (Vantagem):**
    - Opção A: Abrir 2 pontos de vantagem.
    - Opção B: Limite fixo/Pontos Diretos (Ex: Set de 15, quem fizer 18 primeiro vence, mesmo sem abrir 2).
- **W.O (Walkover):** Atribuição de vitória automática com pontuação máxima da fase (Ex: 21x0 ou 15x0).

## 4. Feature: Equipes (Teams)
- **Cadastro Manual:** Realizado exclusivamente pelo ADM no MVP.
- **Escopo:** Equipes são únicas por torneio.
- **Jogadores:** Nome.

## 5. Feature: Fases e Grupos (Phases & Groups)
- **Gestão de Fases:** Criação de fases tipo `Grupo` ou `Eliminatória`.
- **Configuração de Grupos:**
    - Definição manual de quantos times avançam por grupo.
    - Sorteio: Aleatório ou Manual.
- **Resiliência:** Botão "Resetar Fase" que limpa jogos e classificação, permitindo novo sorteio (bloqueado se houver resultados finalizados lançados).

## 6. Feature: Partidas (Matches)
- **Gerenciador de Rodadas:** Geração automática "Todos contra Todos" dentro dos grupos.
- **Lançamento de Resultados:** Interface para lançamento set por set.
- **Integridade:** Bloqueio de edição após o resultado ser confirmado/finalizado pelo ADM.
- **Quadra Única:** Cronograma linear de jogos (um jogo por vez).

## 7. Feature: Classificação e Desempate
- **Critérios de Ranking (Padrão):**
    1. Vitórias
    2. Confronto Direto
    3. Pontos feitos
    4. Saldo de Pontos
- **Regra de Empate Triplo:** Confronto direto entre os três, seguido de Pontos Feitos, Pontos Tomados e Saldo.

## 8. Feature: Fase Eliminatória (Bracket)
- **Cruzamento Inteligente:** Melhor 1º colocado vs Pior 2º colocado qualificado, e assim sucessivamente.
- **Disputa de 3º Lugar:** Obrigatória para definição de pódio e descanso dos finalistas.
- **Consistência:** Regras de empate seguem o padrão da fase configurada.

## 9. Feature: Área Pública (Public Views)
- **URL Amigável:** `torneio.ledtech.app/torneio/{slug}`.
- **Acesso:** Totalmente aberto, sem necessidade de login.
- **Conteúdo:** 
    - Informações gerais.
    - Classificação dos grupos em tempo real.
    - Cronograma e resultados de jogos.
    - Chave eliminatória (Bracket).
- **Ao Vivo:** Atualização de placares via *polling* automático (refresh leve sem WebSocket).

## Infraestrutura e Deploy

**Stack fixa:**
- Python 3.11+ + Django 5.x (usando Django Templates)
- Banco de dados: PostgreSQL
- Deploy: Docker + Nginx (produção)
- Variáveis de ambiente via `.env` (django-environ ou python-dotenv)
- Coleta de static files + whitenoise ou volume no Nginx

**Regras importantes:**
- Sempre respeitar a divisão em features/módulos que combinamos.
- Usar boas práticas Django (models claros, forms quando necessário, Class-Based Views preferencialmente).
- Templates em `templates/` com herança de base.html.
- Configurações sensíveis devem vir de `.env`.