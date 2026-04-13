Roadmap de Desenvolvimento — Gerenciador de Torneios (MVP)
🔷 Fase 1 — Fundação do Projeto e Modelagem de Dados
Objetivo:
Estabelecer a base sólida do sistema (projeto, apps, banco e autenticação).

Entregas:
1. Setup do Projeto
Criar projeto Django
Configurar PostgreSQL
Configurar Docker + docker-compose
Configurar variáveis de ambiente (.env)
Configurar static files (whitenoise ou nginx)
2. Estrutura de Apps
users → autenticação e controle de acesso
core → toda lógica de torneio
3. Modelo de Usuário
Custom User (AbstractUser)
Preparado para expansão futura (telefone, etc.)
4. Modelagem do Core (ESSENCIAL)
Criar os models:

Torneio
RegraPontuacao
Fase
Grupo
Equipe
Jogador
Partida
SetResult
Regras importantes:
Torneio pertence ao usuário (multitenancy)
Fase possui regra própria (override da modalidade)
Equipes são isoladas por torneio
Partidas NÃO podem ser editadas após finalização
Suporte a W.O. no model
5. Django Admin
Registrar todos os models
Permitir:
Criar torneio
Criar equipes
Criar fases e regras
✅ Resultado esperado:
Sistema já permite cadastro completo via admin.

🔷 Fase 2 — Lógica de Grupos e Geração de Partidas
Objetivo:
Fazer o torneio “existir” — criação de grupos e jogos.

Entregas:
1. Criação de Grupos
Manual e automático (sorteio)
Associação de equipes aos grupos
2. Geração de Jogos (Round Robin)
Algoritmo "todos contra todos"
Cada equipe joga contra todas do grupo
Garantir:
Sem duplicidade
Sem jogo contra si mesmo
3. Ordenação de Jogos (Cronograma)
Campo ordem_cronograma
Sequência linear (quadra única)
4. Reset de Fase
Botão/ação que:
Apaga partidas
Limpa classificação
Permite novo sorteio
Regra crítica:
Só pode resetar se NÃO houver partidas finalizadas
✅ Resultado esperado:
Grupos e jogos são gerados automaticamente e podem ser resetados com segurança.

🔷 Fase 3 — Lançamento de Resultados e Regras de Jogo
Objetivo:
Permitir operação real do torneio.

Entregas:
1. Interface de Lançamento de Resultado
Formulário por partida
Entrada de sets (dinâmico)
2. Lógica de Validação
Validar com base na RegraPontuacao:

Número máximo de sets
Pontuação mínima para vencer
Regra de vantagem (2 pontos)
Regra de limite (ex: 18 direto)
3. Definição de Vencedor
Calcular automaticamente:
Sets ganhos
Time vencedor
4. W.O. (Walkover)
Flag na partida
Sistema atribui:
Pontuação máxima automática
Define vencedor
5. Bloqueio de Edição
Após status FINALIZADA:
NÃO pode editar
Garantir integridade dos dados
✅ Resultado esperado:
Admin consegue lançar resultados corretamente e com segurança.

🔷 Fase 4 — Classificação e Ranking
Objetivo:
Gerar ranking automático e confiável.

Entregas:
1. Motor de Classificação
Para cada grupo calcular:

Vitórias
Derrotas
Sets ganhos/perdidos
Pontos feitos/tomados
2. Critérios de Ranking (ORDENADOS)
Vitórias
Saldo de Sets
Saldo de Pontos
Confronto Direto
3. Empate Triplo
Aplicar regra:

Confronto entre empatados
Pontos feitos
Pontos tomados
Saldo
4. Atualização Automática
Sempre que uma partida finaliza:
Ranking recalcula
✅ Resultado esperado:
Classificação correta e atualizada automaticamente.

🔷 Fase 5 — Fase Eliminatória (Mata-Mata)
Objetivo:
Gerar chaveamento inteligente e consistente.

Entregas:
1. Seleção de Classificados
Baseado na configuração:
equipes_avancam
2. Ordenação Geral
Rankear todos classificados globalmente
3. Cruzamento Inteligente
Implementar regra:

Melhor 1º vs Pior 2º
Segundo melhor 1º vs Segundo pior 2º
E assim por diante
4. Geração de Partidas Eliminatórias
Quartas
Semi
Final
5. Disputa de 3º Lugar
Entre perdedores da semifinal
✅ Resultado esperado:
Chave eliminatória gerada automaticamente e correta.

🔷 Fase 6 — Área Pública
Objetivo:
Visualização do torneio pelo público.

Entregas:
1. URL Pública
/torneio/{slug}
2. Páginas:
Visão geral do torneio
Grupos e classificação
Jogos (cronograma)
Resultados
Chave eliminatória
3. “Ao Vivo” (Polling)
Atualização automática (ex: 10s)
Sem WebSocket (MVP)
✅ Resultado esperado:
Usuários acompanham torneio em tempo real.

🔷 Fase 7 — Interface (UI/UX)
Objetivo:
Interface limpa, moderna e funcional.

Diretrizes:
Tema:
Base: Branco / Cinza claro
Primária: Azul (confiança / sistema)
Destaque: Laranja ou Amarelo (ação / energia)
Uso das cores:
Azul → navegação / headers
Laranja → botões principais / CTAs
Verde → vitória
Vermelho → derrota / erro
Componentes:
Tabelas (classificação)
Cards (jogos)
Badge de status (AO VIVO, FINALIZADO)
✅ Resultado esperado:
Sistema agradável, legível e utilizável em celular.

🔷 Fase 8 — Deploy e Produção
Objetivo:
Colocar o sistema no ar.

Entregas:
Docker otimizado
Nginx configurado
HTTPS (SSL)
Domínio:
torneio.ledtech.app
✅ Resultado esperado:
Sistema acessível publicamente.