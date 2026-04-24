Prompt Detalhado para Desenvolvimento da Página Pública do Torneio (MVP)
Contexto:
Criar uma página pública e institucional para cada torneio, acessível apenas via link direto pelo slug do torneio. A página funciona como um cartão de visita digital, sem login, sem listagem pública, e deve exibir informações básicas e institucionais do torneio.

Requisitos Funcionais:

URL e Rota:
Rota pública: /t/<slug>/
Usar slug do model Torneio para lookup.
Se slug não existir, retornar 404 padrão.
Não deve haver autenticação ou login para acessar.
Não deve haver listagem pública de torneios.
Model Torneio:
Usar campos já existentes para MVP.
Campos obrigatórios para a página:
premiacao (TextField, texto livre, pode ser longo)
regras_gerais (TextField, texto livre, pode ser longo)
Campos para informações básicas: data início, horário, local, quantidade de times, formato, times por grupo, regra de pontuação, status.
Campos de logo e foto_capa ficam para futuras versões (não implementar agora).
View:
Usar Class-Based View DetailView para o model Torneio.
Lookup pelo slug.
Passar no contexto:
torneio (objeto completo)
status_display (label legível do status)
Sem filtro por owner ou autenticação.
Template:
Criar template public/torneio_publico.html.
Não herdar do base.html administrativo.
Criar base_public.html limpo, sem menu, sidebar ou header administrativo.
Layout mobile-first, largura máxima 600px, centralizado.
Fundo cinza claro, cards brancos com borda sutil.
Fonte padrão do sistema.
No topo: fundo azul sólido removido, exibir apenas o nome do torneio, centralizado e destacado.
Badge de status com cores distintas conforme status (ex: verde para "Em andamento", vermelho para "Encerrado", laranja para "Inscrições abertas").
Cards a exibir (na ordem):
Informações: data (ex: "19 e 20 de abril de 2026"), horário, local.
Formato: quantidade de times, formato, times por grupo, regra de pontuação.
Premiação: exibir texto do campo premiacao. Se vazio, ocultar o card.
Regras gerais: exibir texto do campo regras_gerais. Se vazio, ocultar o card.
Premiação e regras gerais podem ser textos longos; permitir rolagem interna nesses cards se necessário.
Rodapé: texto "Gerado por ledtech.app" com link para https://ledtech.app abrindo em nova aba.
Segurança e Privacidade:
Não exibir dados sensíveis: owner, id numérico, emails, tokens.
Não exibir equipes, resultados ou classificações.
Página pública, sem autenticação.
Edge Cases:
Slug inexistente → 404 padrão.
Sem logo e foto_capa → não exibir, sem espaço reservado.
Premiação e regras gerais vazios → ocultar cards sem deixar espaço em branco.
Atualizações no torneio devem refletir imediatamente na página (sem cache agressivo).
Internacionalização:
Apenas PT-BR, sem necessidade de suporte multilíngue.
Testes:
Não implementar testes automatizados no MVP.
Futuras Integrações:
Código deve ser organizado para facilitar inclusão futura de logo e foto_capa, mas sem implementar agora.
Design e Estilo:

Usar cores do sistema: azul primário #0C447C, laranja CTA #e85d04.
Fundo da página cinza claro (#f5f5f5 ou similar).
Cards com fundo branco, borda sutil e espaçamento generoso.
Badge de status com cores distintas e texto legível.
Fonte padrão do sistema (sem alteração).
Layout responsivo, mobile-first, largura máxima 600px, centralizado.
Entrega Esperada:

Código Django para model (migração se necessário), view, urls, templates e CSS.
Templates organizados com base_public.html e torneio_publico.html.
Comentários claros no código para facilitar manutenção futura.
Sem funcionalidades extras além do escopo definido.