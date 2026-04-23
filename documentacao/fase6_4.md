# Plano de Execução — Fase 6.4: Transmissão e Polimento Visual (Modo Final)

## Objetivo da Fase 6.4
Dar o acabamento profissional ao Dashboard Público. Nesta fase, implementamos a integração com a live (transmissão), adicionamos animações sutis para mudanças de dados e fazemos o ajuste fino da interface para garantir que a experiência na TV seja impecável.

---

## 1. Integração da Live (Transmissão via Instagram/Outros)

### Componente de Vídeo
- O Dashboard deve reservar um espaço no rodapé ou lateral (conforme layout ajustado) para o `live_url`.
- Implementar suporte para `iframe`.
- **Lógica de exibição:**
    - Se `torneio.live_url` estiver vazio: O layout deve se reajustar para ocupar o espaço com as tabelas/confrontos (seeding maior).
    - Se preenchido: Renderizar o contêiner de vídeo com uma borda sutil e título "ASSISTA AO VIVO".

---

## 2. Animações e Transições (UX de TV)

Para que a atualização de dados não seja brusca (teletransporte de números), utilizaremos CSS Transitions:

- **Mudança de Placar:** Pequeno efeito de "fade-in/out" ou "slide" quando o ponto mudar.
- **Badge Pulsante:** Melhorar a animação CSS `@keyframes pulse` do indicador 🔴 AO VIVO para que seja suave e não distraia o público excessivamente.
- **Destaque de Grupo:** Transição suave da borda laranja quando o jogo mudar de um grupo para outro.
- **Troca de Fase:** Se o torneio mudar de Grupos para Eliminatória, aplicar um efeito de fade na tela inteira para a transição de layout.

---

## 3. Polimento de UI (Ajustes de Design)

- **Legibilidade de Tabela:** Adicionar "zebra striping" (linhas alternadas) sutil nas tabelas de classificação para facilitar a leitura à distância.
- **Badges de Posição:** Refinar os indicadores de Classificado/Eliminado (cores verde/cinza) com ícones simples ou bordas arredondadas.
- **Empty States:** Garantir que, se um grupo estiver sem jogos, o card não fique feio (exibir uma mensagem elegante).
- **Relógio do Sistema:** Adicionar um relógio (HH:mm) digital discreto no topo da tela para ajudar na organização do evento.

---

## 4. Modo Fullscreen e UX Especializada

- **Auto-Fullscreen:** Instruir o ADM a usar F11, mas adicionar um pequeno botão flutuante "Entrar em Tela Cheia" (que desaparece após ativado) para facilitar a vida do operador.
- **Ocultar Cursor:** Adicionar lógica CSS para ocultar o cursor do mouse se ele ficar parado por mais de 5 segundos sobre o dashboard.

---

## 5. Critérios de Pronto (Definition of Done)
- [ ] Iframe da live renderizando corretamente quando a URL é fornecida.
- [ ] Layout se adapta elegantemente à ausência de live.
- [ ] Pontuação e classificação mudam com animações de transição suaves.
- [ ] Relógio digital funcional no dashboard.
- [ ] Cursor do mouse ocultado automaticamente após inatividade.
- [ ] Teste final de "Estresse Visual": Verificar se dados longos (nomes de equipes grandes) não quebram o layout.

---

## Encerramento da Fase 6 e do Planejamento
Com a conclusão da Fase 6.4, o sistema está pronto para produção na sua face pública. O próximo passo geral seria o **Deploy em Produção (Docker + Nginx no domínio torneio.ledtech.app)**.