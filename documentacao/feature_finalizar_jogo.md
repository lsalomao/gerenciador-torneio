Views.py 
metodo: partida_edit

Minha solicitação:
Em vez de redirecionar automaticamente quando houver um vencedor (valid.get('success') == True), quero exibir um modal (pop-up) bonito na própria página de edição da partida.
O que o modal deve conter:

Título: "Partida Finalizada!"
Texto: "O jogo acabou com sucesso."
Informar claramente o vencedor: "Vencedor: Nome do Time"
Mensagem adicional: "A partida foi marcada como FINALIZADA e os rankings/processos foram atualizados."
Dois botões grandes:
"Ir para a página de edição da partida" → fecha o modal e permanece na tela atual
"Voltar para a lista de partidas" → redireciona para a changelist


Requisitos técnicos:

Implementar usando o método response_change da classe PartidaAdmin
Usar um modal Bootstrap (o Django Admin já inclui Bootstrap)
Não criar uma página nova (TemplateResponse separado). O modal deve aparecer na própria tela de edição após o save.
Sobrescrever o template change_form.html apenas o necessário para incluir o modal
Passar as informações do vencedor e da partida via contexto
O modal deve aparecer automaticamente apenas quando a partida for finalizada com sucesso
Manter o comportamento atual quando não houver vencedor (continuar como "AO_VIVO" e voltar normalmente para a edição)

Por favor, forneça:

O código completo da classe PartidaAdmin com response_change implementado
O código do template templates/admin/sua_app/partida/change_form.html (apenas a parte necessária com o modal)
Qualquer observação importante sobre como injetar o modal e como adaptar a chamada do validar_set

Faça o código limpo, organizado e pronto para usar.