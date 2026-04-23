from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .services.bracket_service import gerar_eliminatoria
from .services.torneio_setup_service import criar_fases_torneio
from .models import (
    Torneio, RegraPontuacao, Equipe, Jogador,
    Fase, Grupo, Partida, SetResult
)
from .forms import (
    TorneioForm, RegraPontuacaoForm, EquipeForm,
    JogadorFormSet, FaseForm, GrupoForm,
    PartidaForm, SetResultFormSet
)


def home(request):
    return render(request, 'home.html')


def _serialize_live_payload(torneio):
    highlight = get_current_highlight(torneio)

    if not highlight:
        return {'torneio': torneio.nome, 'highlight': None}

    sets = [
        {
            'numero_set': s.numero_set,
            'pontos_a': s.pontos_a,
            'pontos_b': s.pontos_b,
        }
        for s in highlight.sets.all()
    ]

    sets_ganhos_a = sum(1 for s in highlight.sets.all() if s.pontos_a > s.pontos_b)
    sets_ganhos_b = sum(1 for s in highlight.sets.all() if s.pontos_b > s.pontos_a)

    return {
        'torneio': torneio.nome,
        'highlight': {
            'id': highlight.id,
            'fase': highlight.fase.nome,
            'status': highlight.status,
            'ordem_cronograma': highlight.ordem_cronograma,
            'grupo': highlight.grupo.nome if highlight.grupo else None,
            'equipe_a': highlight.equipe_a.nome,
            'equipe_b': highlight.equipe_b.nome,
            'sets_ganhos_a': sets_ganhos_a,
            'sets_ganhos_b': sets_ganhos_b,
            'sets': sets,
            'vencedor': highlight.vencedor.nome if highlight.vencedor else None,
            'is_wo': highlight.is_wo,
        },
    }


def public_torneio_tv(request, slug):
    torneio = get_object_or_404(Torneio, slug=slug)
    initial_dashboard = get_dashboard_context(torneio)
    initial_live = _serialize_live_payload(torneio)

    return render(request, 'public/tv_dashboard.html', {
        'torneio': torneio,
        'polling_interval': torneio.polling_interval * 1000,
        'live_url': torneio.live_url,
        'initial_dashboard': initial_dashboard,
        'initial_live': initial_live,
        'dashboard_url': f'/api/v1/public/torneio/{torneio.slug}/dashboard/',
        'live_data_url': f'/api/v1/public/torneio/{torneio.slug}/live/',
    })


@require_GET
def public_dashboard_data(request, slug):
    torneio = get_object_or_404(Torneio, slug=slug)
    data = get_dashboard_context(torneio)
    return JsonResponse(data)


@require_GET
def public_live_data(request, slug):
    torneio = get_object_or_404(Torneio, slug=slug)
    data = _serialize_live_payload(torneio)
    return JsonResponse(data)


from .services import (
    sortear_equipes_automatico,
    gerar_round_robin_fase,
    pode_resetar_fase,
    resetar_fase,
    obter_estatisticas_fase,
)
from .services.match_service import iniciar_partida, adicionar_set
from .services.wo_service import aplicar_wo
from .services.validation_service import validar_set
from .services.ranking_service import rankear_grupo
from .services.advancement_service import processar_finalizacao_partida
from .services.public_data_service import get_dashboard_context, get_current_highlight


def _configurar_formularios(form, fase):
    """Configura querysets e widgets dos formulários de partida."""
    equipes = fase.torneio.equipes.all()
    form.fields['equipe_a'].queryset = equipes
    form.fields['equipe_b'].queryset = equipes
    form.fields['grupo'].queryset = fase.grupos.all()
    form.fields['vencedor'].queryset = equipes
    form.fields['vencedor_wo'].queryset = equipes

    if fase.tipo == 'ELIMINATORIA':
        form.fields['grupo'].widget = forms.HiddenInput()
        form.fields['grupo'].required = False

    form.fields['fase'].widget = forms.HiddenInput()


def _finalizar_partida(partida, regra):
    """Finaliza partida atribuindo vencedor e atualizando rankings.
    Retorna o nome do vencedor ou None se não houver vencedor."""
    set_atual = partida.sets.filter(numero_set=1).first()
    if not set_atual:
        return None

    valid = validar_set(set_atual.pontos_a, set_atual.pontos_b, regra)
    if not valid.get('success'):
        return None

    if valid.get('winner') == 'A':
        partida.vencedor = partida.equipe_a
    else:
        partida.vencedor = partida.equipe_b
    partida.status = 'FINALIZADA'
    partida.save()

    if partida.grupo:
        try:
            rankear_grupo(partida.grupo)
        except Exception:
            pass
    try:
        processar_finalizacao_partida(partida)
    except Exception:
        pass

    return partida.vencedor.nome if partida.vencedor else ''


def _handle_placar(partida, regra, action):
    """Processa ações de placar (+/-). Retorna redirect."""
    set_atual = partida.sets.filter(numero_set=1).first()
    pontos_a = set_atual.pontos_a if set_atual else 0
    pontos_b = set_atual.pontos_b if set_atual else 0

    if action == 'increment_a':
        pontos_a += 1
    elif action == 'decrement_a' and pontos_a > 0:
        pontos_a -= 1
    elif action == 'increment_b':
        pontos_b += 1
    elif action == 'decrement_b' and pontos_b > 0:
        pontos_b -= 1

    if set_atual:
        SetResult.objects.filter(pk=set_atual.pk).update(pontos_a=pontos_a, pontos_b=pontos_b)
    else:
        SetResult.objects.bulk_create([
            SetResult(partida=partida, numero_set=1, pontos_a=pontos_a, pontos_b=pontos_b)
        ])

    valid = validar_set(pontos_a, pontos_b, regra)
    if valid.get('success'):
        if valid.get('winner') == 'A':
            partida.vencedor = partida.equipe_a
        elif valid.get('winner') == 'B':
            partida.vencedor = partida.equipe_b
        partida.status = 'FINALIZADA'
        partida.save()

        if partida.grupo:
            try:
                rankear_grupo(partida.grupo)
            except Exception:
                pass
        try:
            processar_finalizacao_partida(partida)
        except Exception:
            pass

        return f'?finalizada=1'
    else:
        if partida.status == 'AGENDADA':
            partida.status = 'AO_VIVO'
            partida.save(update_fields=['status'])

    return ''


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
            
            # Criar fases automaticamente
            resultado = criar_fases_torneio(torneio)
            
            if resultado['sucesso']:
                messages.success(request, f'Torneio "{torneio.nome}" criado com sucesso! {len(resultado["fases_criadas"])} fases foram criadas automaticamente.')
                
                if 'aviso' in resultado:
                    messages.warning(request, resultado['aviso'])
            else:
                messages.error(request, f"Erro ao criar fases: {resultado.get('erro', 'Erro desconhecido')}")
            
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
        form = EquipeForm(request.POST, torneio=torneio)
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
        form = EquipeForm(torneio=torneio)
        formset = JogadorFormSet()
    return render(request, 'admin_area/equipe_form.html', {
        'form': form, 'formset': formset, 'torneio': torneio, 'title': 'Nova Equipe'
    })


@login_required
def equipe_edit(request, pk):
    equipe = get_object_or_404(Equipe, pk=pk, torneio__owner=request.user)
    if request.method == 'POST':
        form = EquipeForm(request.POST, instance=equipe, torneio=equipe.torneio)
        formset = JogadorFormSet(request.POST, instance=equipe)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Equipe atualizada!')
            return redirect('admin_torneio_detail', pk=equipe.torneio.pk)
    else:
        form = EquipeForm(instance=equipe, torneio=equipe.torneio)
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
    partidas = fase.partidas.select_related('equipe_a', 'equipe_b', 'grupo', 'vencedor', 'vencedor_wo').prefetch_related('sets').order_by('grupo__nome', 'ordem_cronograma', 'id')

    for partida in partidas:
        sets_lancados = list(partida.sets.all())
        set_unico = sets_lancados[0] if sets_lancados else None
        partida.placar_resumo = f"{set_unico.pontos_a} x {set_unico.pontos_b}" if set_unico else ('W.O.' if partida.is_wo else '—')
        partida.vencedor_nome = partida.vencedor.nome if partida.vencedor else None

    partidas_por_grupo = []
    if fase.tipo == 'GRUPO':
        partidas_por_grupo_id = {}
        for partida in partidas:
            partidas_por_grupo_id.setdefault(partida.grupo_id, []).append(partida)

        for grupo in grupos:
            partidas_do_grupo = partidas_por_grupo_id.get(grupo.id, [])
            rodadas_map = {}
            for partida in partidas_do_grupo:
                numero_rodada = partida.rodada or 1
                rodadas_map.setdefault(numero_rodada, []).append(partida)

            rodadas = []
            for numero in sorted(rodadas_map.keys()):
                rodadas.append({
                    'numero': numero,
                    'partidas': rodadas_map[numero],
                })

            partidas_por_grupo.append({
                'grupo': grupo,
                'rodadas': rodadas,
            })

    stats = obter_estatisticas_fase(fase.id)

    return render(request, 'admin_area/fase_detail.html', {
        'fase': fase,
        'grupos': grupos,
        'partidas': partidas,
        'partidas_por_grupo': partidas_por_grupo,
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

            resultado_partidas = gerar_round_robin_fase(fase.id)
            if resultado_partidas['success']:
                messages.success(request, resultado_partidas['message'])
            else:
                messages.warning(request, f"Equipes sorteadas com sucesso, mas houve falha ao gerar partidas: {resultado_partidas['message']}")
                for erro in resultado_partidas.get('erros', []):
                    messages.warning(request, erro)
        else:
            messages.error(request, resultado['message'])

        return redirect('admin_fase_detail', pk=fase.pk)
    
    equipes_disponiveis = fase.torneio.equipes.exclude(grupos__fase=fase)

    return render(request, 'admin_area/fase_sortear_confirm.html', {
        'fase': fase,
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
    is_finalizada = partida.status == 'FINALIZADA'
    show_modal = request.GET.get('finalizada') == '1'

    if is_finalizada and not show_modal:
        messages.error(request, 'Partida finalizada não pode ser editada.')
        return redirect('admin_fase_detail', pk=partida.fase.pk)

    regra = partida.fase.regra

    if request.method == 'POST':
        action = request.POST.get('action')

        if action in ['increment_a', 'decrement_a', 'increment_b', 'decrement_b']:
            if not regra:
                messages.error(request, 'Defina uma regra de pontuação na fase antes de lançar placar.')
                return redirect('admin_partida_edit', pk=partida.pk)

            suffix = _handle_placar(partida, regra, action)
            redirect_path = f'{request.path}{suffix}' if suffix else request.path
            return redirect(redirect_path)

        if action == 'finalizar':
            if not regra:
                messages.error(request, 'Defina uma regra de pontuação na fase antes de finalizar o jogo.')
                return redirect('admin_partida_edit', pk=partida.pk)

            vencedor = _finalizar_partida(partida, regra)
            if vencedor is None:
                messages.error(request, 'Não foi possível finalizar o jogo. Verifique o placar.')
                return redirect('admin_partida_edit', pk=partida.pk)

            return redirect(f'{request.path}?finalizada=1')

        if action == 'voltar_ponto':
            set_atual = partida.sets.filter(numero_set=1).first()
            if not set_atual:
                messages.error(request, 'Não há placar para reverter.')
                return redirect('admin_partida_edit', pk=partida.pk)

            if partida.vencedor == partida.equipe_a and set_atual.pontos_a > 0:
                set_atual.pontos_a -= 1
            elif partida.vencedor == partida.equipe_b and set_atual.pontos_b > 0:
                set_atual.pontos_b -= 1

            set_atual.save(update_fields=['pontos_a', 'pontos_b'])
            partida.vencedor = None
            partida.save(update_fields=['vencedor'])

            messages.info(request, 'Último ponto removido. Confirme o término quando desejar.')
            return redirect('admin_partida_edit', pk=partida.pk)

        if action == 'save':
            messages.success(request, 'Placar salvo!')
            return redirect('admin_partida_edit', pk=partida.pk)

        # Formulário padrão (form/formset)
        form = PartidaForm(request.POST, instance=partida)
        _configurar_formularios(form, partida.fase)

        if partida.status == 'FINALIZADA':
            form.is_valid()
            messages.info(request, 'Partida finalizada. Use "Voltar último ponto" para reverter.')
            return redirect('admin_fase_detail', pk=partida.fase.pk)

        formset = SetResultFormSet(request.POST, instance=partida)
        if form.is_valid() and formset.is_valid():
            form.save()

            for set_form in formset:
                cd = set_form.cleaned_data
                if not cd:
                    continue
                if cd.get('DELETE') and set_form.instance.pk:
                    set_form.instance.delete()
                    continue

                if set_form.instance.pk:
                    set_form.save()
                else:
                    resultado = adicionar_set(
                        partida,
                        cd.get('numero_set'),
                        cd.get('pontos_a'),
                        cd.get('pontos_b'),
                    )
                    if not resultado['success']:
                        messages.error(request, resultado['message'])
                        return redirect('admin_partida_edit', pk=partida.pk)

            messages.success(request, 'Partida atualizada!')
            return redirect('admin_fase_detail', pk=partida.fase.pk)
    else:
        form = PartidaForm(instance=partida)
        formset = SetResultFormSet(instance=partida)
        _configurar_formularios(form, partida.fase)

    set_atual = partida.sets.filter(numero_set=1).first()
    pontos_a = set_atual.pontos_a if set_atual else 0
    pontos_b = set_atual.pontos_b if set_atual else 0

    partida_finalizada = None
    if show_modal:
        partida_finalizada = {
            'vencedor_nome': partida.vencedor.nome if partida.vencedor else '',
            'partida_nome': f'{partida.equipe_a.nome} vs {partida.equipe_b.nome}',
        }

    return render(request, 'admin_area/partida_form.html', {
        'form': form,
        'formset': formset,
        'partida': partida,
        'title': f'Editar: {partida}',
        'fase': partida.fase,
        'set_atual': set_atual,
        'pontos_a': pontos_a,
        'pontos_b': pontos_b,
        'partida_finalizada': partida_finalizada,
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
