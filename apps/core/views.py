from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.bracket_service import gerar_eliminatoria
from .models import (
    Torneio, RegraPontuacao, Equipe, Jogador,
    Fase, Grupo, Partida, SetResult
)
from .forms import (
    TorneioForm, RegraPontuacaoForm, EquipeForm,
    JogadorFormSet, FaseForm, GrupoForm,
    PartidaForm, SetResultFormSet
)
from .services import (
    sortear_equipes_automatico,
    gerar_round_robin_fase,
    pode_resetar_fase,
    resetar_fase,
    obter_estatisticas_fase,
)
from .services.match_service import iniciar_partida, adicionar_set
from .services.wo_service import aplicar_wo


@login_required
def dashboard(request):
    torneios = Torneio.objects.filter(owner=request.user)
    regras = RegraPontuacao.objects.all()
    return render(request, 'admin_area/dashboard.html', {
        'torneios': torneios,
        'regras': regras,
    })


# --- TORNEIO ---

@login_required
def torneio_list(request):
    torneios = Torneio.objects.filter(owner=request.user)
    return render(request, 'admin_area/torneio_list.html', {'torneios': torneios})


@login_required
def torneio_create(request):
    if request.method == 'POST':
        form = TorneioForm(request.POST)
        if form.is_valid():
            torneio = form.save(commit=False)
            torneio.owner = request.user
            torneio.save()
            messages.success(request, f'Torneio "{torneio.nome}" criado com sucesso!')
            return redirect('admin_torneio_detail', pk=torneio.pk)
    else:
        form = TorneioForm()
    return render(request, 'admin_area/torneio_form.html', {'form': form, 'title': 'Novo Torneio'})


@login_required
def torneio_detail(request, pk):
    torneio = get_object_or_404(Torneio, pk=pk, owner=request.user)
    equipes = torneio.equipes.all()
    fases = torneio.fases.all()
    return render(request, 'admin_area/torneio_detail.html', {
        'torneio': torneio,
        'equipes': equipes,
        'fases': fases,
    })


@login_required
def torneio_avancar_fase(request, pk):
    """Gera automaticamente a próxima fase eliminatória quando os grupos terminam."""
    torneio = get_object_or_404(Torneio, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        # Buscar fase de grupos
        fase_grupo = Fase.objects.filter(torneio=torneio, tipo='GRUPO').first()
        
        if not fase_grupo:
            messages.error(request, 'Nenhuma fase de GRUPO encontrada no torneio.')
            return redirect('admin_torneio_detail', pk=torneio.pk)
        
        # Verificar se todos os grupos estão finalizados
        for grupo in fase_grupo.grupos.all():
            if grupo.partidas.exclude(status='FINALIZADA').exists():
                messages.error(request, f'Ainda há partidas não finalizadas no grupo {grupo.nome}. Finalize todas as partidas antes de avançar.')
                return redirect('admin_torneio_detail', pk=torneio.pk)
        
        # Buscar próxima fase eliminatória
        proxima_fase_elim = Fase.objects.filter(
            torneio=torneio,
            ordem__gt=fase_grupo.ordem,
            tipo='ELIMINATORIA'
        ).order_by('ordem').first()
        
        if not proxima_fase_elim:
            messages.error(request, 'Nenhuma fase ELIMINATÓRIA configurada. Crie uma antes de avançar.')
            return redirect('admin_torneio_detail', pk=torneio.pk)
        
        if proxima_fase_elim.partidas.exists():
            messages.warning(request, 'A fase eliminatória já foi gerada. Redirecionando...')
            return redirect('admin_fase_detail', pk=proxima_fase_elim.pk)
        
        # Gerar eliminatória
        resultado = gerar_eliminatoria(fase_grupo.id, fase_existente=proxima_fase_elim)
        
        if resultado['success']:
            messages.success(request, f'✓ {resultado["message"]} Redirecionando para a nova fase...')
            return redirect('admin_fase_detail', pk=proxima_fase_elim.pk)
        else:
            messages.error(request, f'Erro ao gerar fase eliminatória: {resultado["message"]}')
            return redirect('admin_torneio_detail', pk=torneio.pk)
    
    messages.warning(request, 'Esta ação requer confirmação.')
    return redirect('admin_torneio_detail', pk=torneio.pk)


@login_required
def torneio_edit(request, pk):
    torneio = get_object_or_404(Torneio, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = TorneioForm(request.POST, instance=torneio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Torneio atualizado com sucesso!')
            return redirect('admin_torneio_detail', pk=torneio.pk)
    else:
        form = TorneioForm(instance=torneio)
    return render(request, 'admin_area/torneio_form.html', {'form': form, 'title': f'Editar: {torneio.nome}'})


@login_required
def torneio_delete(request, pk):
    torneio = get_object_or_404(Torneio, pk=pk, owner=request.user)
    if request.method == 'POST':
        nome = torneio.nome
        torneio.delete()
        messages.success(request, f'Torneio "{nome}" excluído.')
        return redirect('admin_torneio_list')
    return render(request, 'admin_area/confirm_delete.html', {'object': torneio, 'type': 'Torneio'})


# --- REGRA DE PONTUACAO ---

@login_required
def regra_list(request):
    regras = RegraPontuacao.objects.all()
    return render(request, 'admin_area/regra_list.html', {'regras': regras})


@login_required
def regra_create(request):
    if request.method == 'POST':
        form = RegraPontuacaoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Regra de pontuação criada!')
            return redirect('admin_regra_list')
    else:
        form = RegraPontuacaoForm()
    return render(request, 'admin_area/generic_form.html', {'form': form, 'title': 'Nova Regra de Pontuação'})


@login_required
def regra_edit(request, pk):
    regra = get_object_or_404(RegraPontuacao, pk=pk)
    if request.method == 'POST':
        form = RegraPontuacaoForm(request.POST, instance=regra)
        if form.is_valid():
            form.save()
            messages.success(request, 'Regra atualizada!')
            return redirect('admin_regra_list')
    else:
        form = RegraPontuacaoForm(instance=regra)
    return render(request, 'admin_area/generic_form.html', {'form': form, 'title': f'Editar: {regra.nome}'})


@login_required
def regra_delete(request, pk):
    regra = get_object_or_404(RegraPontuacao, pk=pk)
    if request.method == 'POST':
        regra.delete()
        messages.success(request, 'Regra excluída.')
        return redirect('admin_regra_list')
    return render(request, 'admin_area/confirm_delete.html', {'object': regra, 'type': 'Regra de Pontuação'})


# --- EQUIPE ---

@login_required
def equipe_create(request, torneio_pk):
    torneio = get_object_or_404(Torneio, pk=torneio_pk, owner=request.user)
    if request.method == 'POST':
        form = EquipeForm(request.POST)
        formset = JogadorFormSet(request.POST)
        if form.is_valid():
            equipe = form.save(commit=False)
            equipe.torneio = torneio
            equipe.save()
            formset = JogadorFormSet(request.POST, instance=equipe)
            if formset.is_valid():
                formset.save()
            messages.success(request, f'Equipe "{equipe.nome}" criada!')
            return redirect('admin_torneio_detail', pk=torneio.pk)
    else:
        form = EquipeForm()
        formset = JogadorFormSet()
    return render(request, 'admin_area/equipe_form.html', {
        'form': form, 'formset': formset, 'torneio': torneio, 'title': 'Nova Equipe'
    })


@login_required
def equipe_edit(request, pk):
    equipe = get_object_or_404(Equipe, pk=pk, torneio__owner=request.user)
    if request.method == 'POST':
        form = EquipeForm(request.POST, instance=equipe)
        formset = JogadorFormSet(request.POST, instance=equipe)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Equipe atualizada!')
            return redirect('admin_torneio_detail', pk=equipe.torneio.pk)
    else:
        form = EquipeForm(instance=equipe)
        formset = JogadorFormSet(instance=equipe)
    return render(request, 'admin_area/equipe_form.html', {
        'form': form, 'formset': formset, 'torneio': equipe.torneio, 'title': f'Editar: {equipe.nome}'
    })


@login_required
def equipe_delete(request, pk):
    equipe = get_object_or_404(Equipe, pk=pk, torneio__owner=request.user)
    torneio_pk = equipe.torneio.pk
    if request.method == 'POST':
        equipe.delete()
        messages.success(request, 'Equipe excluída.')
        return redirect('admin_torneio_detail', pk=torneio_pk)
    return render(request, 'admin_area/confirm_delete.html', {'object': equipe, 'type': 'Equipe'})


# --- FASE ---

@login_required
def fase_create(request, torneio_pk):
    torneio = get_object_or_404(Torneio, pk=torneio_pk, owner=request.user)
    if request.method == 'POST':
        form = FaseForm(request.POST)
        if form.is_valid():
            fase = form.save(commit=False)
            fase.torneio = torneio
            fase.save()
            messages.success(request, f'Fase "{fase.nome}" criada!')
            return redirect('admin_torneio_detail', pk=torneio.pk)
    else:
        form = FaseForm()
    return render(request, 'admin_area/generic_form.html', {
        'form': form, 'title': f'Nova Fase — {torneio.nome}', 'torneio': torneio
    })


@login_required
def fase_edit(request, pk):
    fase = get_object_or_404(Fase, pk=pk, torneio__owner=request.user)
    if request.method == 'POST':
        form = FaseForm(request.POST, instance=fase)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fase atualizada!')
            return redirect('admin_torneio_detail', pk=fase.torneio.pk)
    else:
        form = FaseForm(instance=fase)
    return render(request, 'admin_area/generic_form.html', {
        'form': form, 'title': f'Editar: {fase.nome}', 'torneio': fase.torneio
    })


@login_required
def fase_detail(request, pk):
    fase = get_object_or_404(Fase, pk=pk, torneio__owner=request.user)
    grupos = fase.grupos.prefetch_related('equipes').all()
    partidas = fase.partidas.select_related('equipe_a', 'equipe_b', 'grupo').all()
    
    stats = obter_estatisticas_fase(fase.id)
    
    return render(request, 'admin_area/fase_detail.html', {
        'fase': fase,
        'grupos': grupos,
        'partidas': partidas,
        'stats': stats,
    })


@login_required
def fase_gerar_eliminatoria(request, pk):
    fase = get_object_or_404(Fase, pk=pk, torneio__owner=request.user)
    if request.method == 'POST':
        resultado = gerar_eliminatoria(fase.id)
        if resultado['success']:
            messages.success(request, resultado['message'])
            return redirect('admin_fase_detail', pk=resultado['fase_eliminatoria_id'])
        messages.error(request, resultado['message'])
        return redirect('admin_fase_detail', pk=fase.pk)

    return render(request, 'admin_area/fase_generate_bracket.html', {'fase': fase})


@login_required
def grupo_classificacao(request, pk):
    from .services.ranking_service import rankear_grupo

    grupo = get_object_or_404(Grupo, pk=pk, fase__torneio__owner=request.user)

    ranking = rankear_grupo(grupo)

    return render(request, 'admin_area/group_ranking.html', {
        'grupo': grupo,
        'ranking': ranking,
    })


@login_required
def fase_delete(request, pk):
    fase = get_object_or_404(Fase, pk=pk, torneio__owner=request.user)
    torneio_pk = fase.torneio.pk
    if request.method == 'POST':
        fase.delete()
        messages.success(request, 'Fase excluída.')
        return redirect('admin_torneio_detail', pk=torneio_pk)
    return render(request, 'admin_area/confirm_delete.html', {'object': fase, 'type': 'Fase'})


@login_required
def fase_sortear_equipes(request, pk):
    fase = get_object_or_404(Fase, pk=pk, torneio__owner=request.user)
    
    if request.method == 'POST':
        resultado = sortear_equipes_automatico(fase.id)
        
        if resultado['success']:
            messages.success(request, resultado['message'])
        else:
            messages.error(request, resultado['message'])
        
        return redirect('admin_fase_detail', pk=fase.pk)
    
    grupos = fase.grupos.prefetch_related('equipes').all()
    equipes_disponiveis = fase.torneio.equipes.exclude(grupos__fase=fase)
    
    return render(request, 'admin_area/fase_sortear_confirm.html', {
        'fase': fase,
        'grupos': grupos,
        'equipes_disponiveis': equipes_disponiveis,
    })


@login_required
def fase_gerar_partidas(request, pk):
    fase = get_object_or_404(Fase, pk=pk, torneio__owner=request.user)
    
    if request.method == 'POST':
        resultado = gerar_round_robin_fase(fase.id)
        
        if resultado['success']:
            messages.success(request, resultado['message'])
        else:
            messages.error(request, resultado['message'])
            if resultado.get('erros'):
                for erro in resultado['erros']:
                    messages.warning(request, erro)
        
        return redirect('admin_fase_detail', pk=fase.pk)
    
    grupos = fase.grupos.prefetch_related('equipes').all()
    grupos_info = []
    
    for grupo in grupos:
        num_equipes = grupo.equipes.count()
        num_partidas = (num_equipes * (num_equipes - 1)) // 2 if num_equipes >= 2 else 0
        grupos_info.append({
            'grupo': grupo,
            'num_equipes': num_equipes,
            'num_partidas': num_partidas,
        })
    
    total_partidas = sum(info['num_partidas'] for info in grupos_info)
    
    return render(request, 'admin_area/fase_gerar_confirm.html', {
        'fase': fase,
        'grupos_info': grupos_info,
        'total_partidas': total_partidas,
    })


@login_required
def fase_resetar(request, pk):
    fase = get_object_or_404(Fase, pk=pk, torneio__owner=request.user)
    
    if request.method == 'POST':
        limpar_grupos = request.POST.get('limpar_grupos') == 'on'
        
        resultado = resetar_fase(fase.id, limpar_grupos=limpar_grupos)
        
        if resultado['success']:
            messages.success(request, resultado['message'])
        else:
            messages.error(request, resultado['message'])
        
        return redirect('admin_fase_detail', pk=fase.pk)
    
    pode, mensagem = pode_resetar_fase(fase.id)
    stats = obter_estatisticas_fase(fase.id)
    
    return render(request, 'admin_area/fase_resetar_confirm.html', {
        'fase': fase,
        'pode_resetar': pode,
        'mensagem': mensagem,
        'stats': stats,
    })


# --- GRUPO ---

@login_required
def grupo_create(request, fase_pk):
    fase = get_object_or_404(Fase, pk=fase_pk, torneio__owner=request.user)
    if request.method == 'POST':
        form = GrupoForm(request.POST)
        form.fields['equipes'].queryset = fase.torneio.equipes.all()
        if form.is_valid():
            grupo = form.save(commit=False)
            grupo.fase = fase
            grupo.save()
            form.save_m2m()
            messages.success(request, f'Grupo "{grupo.nome}" criado!')
            return redirect('admin_fase_detail', pk=fase.pk)
    else:
        form = GrupoForm()
        form.fields['equipes'].queryset = fase.torneio.equipes.all()
    return render(request, 'admin_area/generic_form.html', {
        'form': form, 'title': f'Novo Grupo — {fase.nome}'
    })


@login_required
def grupo_edit(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk, fase__torneio__owner=request.user)
    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo)
        form.fields['equipes'].queryset = grupo.fase.torneio.equipes.all()
        if form.is_valid():
            form.save()
            messages.success(request, 'Grupo atualizado!')
            return redirect('admin_fase_detail', pk=grupo.fase.pk)
    else:
        form = GrupoForm(instance=grupo)
        form.fields['equipes'].queryset = grupo.fase.torneio.equipes.all()
    return render(request, 'admin_area/generic_form.html', {
        'form': form, 'title': f'Editar: {grupo.nome}'
    })


@login_required
def grupo_delete(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk, fase__torneio__owner=request.user)
    fase_pk = grupo.fase.pk
    if request.method == 'POST':
        grupo.delete()
        messages.success(request, 'Grupo excluído.')
        return redirect('admin_fase_detail', pk=fase_pk)
    return render(request, 'admin_area/confirm_delete.html', {'object': grupo, 'type': 'Grupo'})


# --- PARTIDA ---

@login_required
def partida_create(request, fase_pk):
    fase = get_object_or_404(Fase, pk=fase_pk, torneio__owner=request.user)
    equipes_torneio = fase.torneio.equipes.all()
    if request.method == 'POST':
        form = PartidaForm(request.POST)
        form.fields['equipe_a'].queryset = equipes_torneio
        form.fields['equipe_b'].queryset = equipes_torneio
        form.fields['grupo'].queryset = fase.grupos.all()
        form.fields['vencedor'].queryset = equipes_torneio
        form.fields['vencedor_wo'].queryset = equipes_torneio
        if form.is_valid():
            partida = form.save(commit=False)
            partida.fase = fase
            partida.save()
            messages.success(request, 'Partida criada!')
            return redirect('admin_fase_detail', pk=fase.pk)
    else:
        form = PartidaForm(initial={'fase': fase})
        form.fields['equipe_a'].queryset = equipes_torneio
        form.fields['equipe_b'].queryset = equipes_torneio
        form.fields['grupo'].queryset = fase.grupos.all()
        form.fields['vencedor'].queryset = equipes_torneio
        form.fields['vencedor_wo'].queryset = equipes_torneio
    
    # Ocultar grupo para fases eliminatórias
    if fase.tipo == 'ELIMINATORIA':
        form.fields['grupo'].widget = forms.HiddenInput()
        form.fields['grupo'].required = False
    
    form.fields['fase'].widget = forms.HiddenInput()
    return render(request, 'admin_area/generic_form.html', {
        'form': form, 'title': f'Nova Partida — {fase.nome}', 'fase': fase
    })


@login_required
def partida_edit(request, pk):
    partida = get_object_or_404(Partida, pk=pk, fase__torneio__owner=request.user)
    if partida.status == 'FINALIZADA':
        messages.error(request, 'Partida finalizada não pode ser editada.')
        return redirect('admin_fase_detail', pk=partida.fase.pk)
    equipes_torneio = partida.fase.torneio.equipes.all()
    if request.method == 'POST':
        form = PartidaForm(request.POST, instance=partida)
        formset = SetResultFormSet(request.POST, instance=partida)
        form.fields['equipe_a'].queryset = equipes_torneio
        form.fields['equipe_b'].queryset = equipes_torneio
        form.fields['grupo'].queryset = partida.fase.grupos.all()
        form.fields['vencedor'].queryset = equipes_torneio
        form.fields['vencedor_wo'].queryset = equipes_torneio
        if form.is_valid() and formset.is_valid():
            # Salva campos da partida
            form.save()

            # Processar sets um-a-um usando match_service para garantir validações e regras
            for set_form in formset:
                cd = set_form.cleaned_data
                if not cd:
                    continue
                # Remoção de set
                if cd.get('DELETE') and set_form.instance.pk:
                    # permitir remoção apenas se partida não finalizada
                    if partida.status == 'FINALIZADA':
                        messages.error(request, 'Não é possível remover sets de partida finalizada.')
                        return redirect('admin_partida_edit', pk=partida.pk)
                    set_form.instance.delete()
                    continue

                numero = cd.get('numero_set')
                pontos_a = cd.get('pontos_a')
                pontos_b = cd.get('pontos_b')

                # Se já existe, atualizar via model (permitido apenas se não finalizada)
                if set_form.instance.pk:
                    if partida.status == 'FINALIZADA':
                        messages.error(request, 'Não é possível editar sets de partida finalizada.')
                        return redirect('admin_partida_edit', pk=partida.pk)
                    set_obj = set_form.save(commit=False)
                    set_obj.save()
                else:
                    # Adicionar novo set usando serviço (irá validar e finalizar partida quando aplicável)
                    resultado = adicionar_set(partida, numero, pontos_a, pontos_b)
                    if not resultado['success']:
                        messages.error(request, resultado['message'])
                        return redirect('admin_partida_edit', pk=partida.pk)

            messages.success(request, 'Partida atualizada!')
            return redirect('admin_fase_detail', pk=partida.fase.pk)
    else:
        form = PartidaForm(instance=partida)
        formset = SetResultFormSet(instance=partida)
        form.fields['equipe_a'].queryset = equipes_torneio
        form.fields['equipe_b'].queryset = equipes_torneio
        form.fields['grupo'].queryset = partida.fase.grupos.all()
        form.fields['vencedor'].queryset = equipes_torneio
        form.fields['vencedor_wo'].queryset = equipes_torneio
    
    # Ocultar grupo para fases eliminatórias
    if partida.fase.tipo == 'ELIMINATORIA':
        form.fields['grupo'].widget = forms.HiddenInput()
        form.fields['grupo'].required = False
    
    form.fields['fase'].widget = forms.HiddenInput()
    return render(request, 'admin_area/partida_form.html', {
        'form': form, 'formset': formset, 'partida': partida,
        'title': f'Editar: {partida}', 'fase': partida.fase
    })


@login_required
def partida_iniciar(request, pk):
    partida = get_object_or_404(Partida, pk=pk, fase__torneio__owner=request.user)
    if request.method == 'POST':
        resultado = iniciar_partida(partida)
        if resultado['success']:
            messages.success(request, resultado['message'])
        else:
            messages.error(request, resultado['message'])
        return redirect('admin_partida_edit', pk=partida.pk)

    return render(request, 'admin_area/partida_start_confirm.html', {'partida': partida})


@login_required
def partida_aplicar_wo(request, pk):
    partida = get_object_or_404(Partida, pk=pk, fase__torneio__owner=request.user)
    if request.method == 'POST':
        vencedor_id = request.POST.get('vencedor')
        if not vencedor_id:
            messages.error(request, 'Selecione a equipe vencedora para aplicar W.O.')
            return redirect('admin_partida_edit', pk=partida.pk)
        vencedor = get_object_or_404(Equipe, pk=vencedor_id, torneio=partida.fase.torneio)
        resultado = aplicar_wo(partida, vencedor)
        if resultado['success']:
            messages.success(request, resultado['message'])
        else:
            messages.error(request, resultado['message'])
        return redirect('admin_partida_edit', pk=partida.pk)

    return render(request, 'admin_area/partida_apply_wo_confirm.html', {'partida': partida})


@login_required
def partida_delete(request, pk):
    partida = get_object_or_404(Partida, pk=pk, fase__torneio__owner=request.user)
    fase_pk = partida.fase.pk
    if request.method == 'POST':
        partida.delete()
        messages.success(request, 'Partida excluída.')
        return redirect('admin_fase_detail', pk=fase_pk)
    return render(request, 'admin_area/confirm_delete.html', {'object': partida, 'type': 'Partida'})
