Documento de Feature: Evolução da Tela de Detalhes e Lógica de Status
1. Objetivo
Modernizar a interface de gerenciamento do torneio (View de Detalhes), implementando um indicador visual de progresso (Stepper), uma organização de grupos compacta (estilo Libertadores/GE) e automatizando a transição dos status do torneio.

2. Lógica de Status Automática (Backend)
O botão "Avançar Fase" deve ser removido. O campo status do modelo Torneio deve ser atualizado automaticamente pelo sistema seguindo estes gatilhos:

Criação: Status inicial ao cadastrar o torneio.
Inscrições: Ativado quando a primeira Equipe for cadastrada ou quando a data atual entrar no período de inscrições.
Em Andamento: Ativado automaticamente no momento em que o usuário acionar a função "Gerar Grupos" ou "Gerar Partidas" de qualquer fase.
Encerrado: Ativado quando o resultado da última partida da última fase (Final) for lançado.
3. Componentes de UI (Frontend - Django Templates + Tailwind)
A. Stepper de Progresso (Topo da Tela):

Substitui o antigo botão de ação.
Exibir 4 estados: Criação → Inscrições → Em Andamento → Encerrado.
Estilo: Círculos numerados conectados por uma linha horizontal.
Estados Visuais:
Etapas concluídas: Círculo verde com ícone de check (check_circle).
Etapa atual: Círculo azul com brilho ou borda destacada.
Etapas futuras: Círculo cinza com texto esmaecido.
B. Organização de Grupos (Estilo GE/Libertadores):

Layout: Grid com 2 grupos por linha (lado a lado) em telas desktop para otimização de espaço.
Tabela de Classificação: Deve seguir o padrão visual do ge.globo:
Cabeçalho compacto: P (Pontos), J (Jogos), V (Vitórias), D (Derrotas), SP (Sets Pró), SC (Sets Contra), SS (Saldo de Sets).
Linha de destaque: As equipes que estão dentro da zona de classificação (baseado no campo equipes_avancam da Fase) devem ter uma barra vertical verde à esquerda da linha.
Interatividade: Não incluir lista de partidas nesta seção (manter apenas a classificação pura).
C. Indicador de Fase Atual:

Na lista lateral ou inferior de "Fases", adicionar um Badge "▶ Atual" (fundo azul, texto branco) ao lado do nome da fase que possui partidas agendadas ou em disputa hoje.
4. Requisitos Técnicos
View do Django: A view torneio_detail deve calcular e injetar no contexto o objeto fase_atual e garantir que o objeto grupo tenha acesso à classificacao_atual (lista ordenada de dicionários com os stats de cada equipe).
Template Tag: Se necessário, criar uma template tag para realizar o split de strings no stepper ou lógicas de comparação de status.
Responsividade: Em dispositivos móveis (mobile), o grid de 2 colunas dos grupos deve empilhar para 1 coluna automaticamente.
5. Referência Visual
Basear o design na captura de tela: imageTabelaGE.jpeg (Tabela GE).
Cores: Azul institucional para ações e destaques, Verde para conclusões e classificação.