from django.contrib import admin
from django.contrib import messages
from .models import (
    Torneio, RegraPontuacao, Equipe, Jogador,
    Fase, Grupo, Partida, SetResult
)
from .services import (
    sortear_equipes_automatico,
    gerar_round_robin_fase,
    resetar_fase,
)


class JogadorInline(admin.TabularInline):
    model = Jogador
    extra = 2


class SetResultInline(admin.TabularInline):
    model = SetResult
    extra = 1


@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'modalidade', 'local', 'data_inicio', 'status', 'owner')
    list_filter = ('status', 'modalidade')
    search_fields = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


@admin.register(RegraPontuacao)
class RegraPontuacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sets_para_vencer', 'pontos_por_set', 'tem_vantagem', 'limite_pontos_diretos')


@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'torneio')
    list_filter = ('torneio',)
    inlines = [JogadorInline]


class GrupoInline(admin.TabularInline):
    model = Grupo
    extra = 0
    show_change_link = True


class PartidaInline(admin.TabularInline):
    model = Partida
    extra = 0
    readonly_fields = ('equipe_a', 'equipe_b', 'grupo', 'status', 'ordem_cronograma')
    can_delete = False
    max_num = 0


@admin.register(Fase)
class FaseAdmin(admin.ModelAdmin):
    list_display = ('nome', 'torneio', 'tipo', 'ordem', 'regra', 'equipes_avancam')
    list_filter = ('torneio', 'tipo')
    inlines = [GrupoInline, PartidaInline]
    actions = ['sortear_equipes_action', 'gerar_partidas_action', 'resetar_fase_action']
    
    @admin.action(description='Sortear equipes automaticamente')
    def sortear_equipes_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Selecione apenas uma fase por vez.', messages.WARNING)
            return
        
        fase = queryset.first()
        
        if fase.tipo != 'GRUPO':
            self.message_user(request, 'Sorteio só é permitido em fases do tipo GRUPO.', messages.ERROR)
            return
        
        resultado = sortear_equipes_automatico(fase.id)
        
        if resultado['success']:
            self.message_user(request, resultado['message'], messages.SUCCESS)
        else:
            self.message_user(request, resultado['message'], messages.ERROR)
    
    @admin.action(description='Gerar partidas round-robin')
    def gerar_partidas_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Selecione apenas uma fase por vez.', messages.WARNING)
            return
        
        fase = queryset.first()
        
        if fase.tipo != 'GRUPO':
            self.message_user(request, 'Geração de partidas só é permitida em fases do tipo GRUPO.', messages.ERROR)
            return
        
        resultado = gerar_round_robin_fase(fase.id)
        
        if resultado['success']:
            self.message_user(request, resultado['message'], messages.SUCCESS)
        else:
            self.message_user(request, resultado['message'], messages.ERROR)
            if resultado.get('erros'):
                for erro in resultado['erros']:
                    self.message_user(request, erro, messages.WARNING)
    
    @admin.action(description='Resetar fase (remover partidas)')
    def resetar_fase_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Selecione apenas uma fase por vez.', messages.WARNING)
            return
        
        fase = queryset.first()
        
        resultado = resetar_fase(fase.id, limpar_grupos=False)
        
        if resultado['success']:
            self.message_user(request, resultado['message'], messages.SUCCESS)
        else:
            self.message_user(request, resultado['message'], messages.ERROR)


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'fase')
    filter_horizontal = ('equipes',)


@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'is_wo', 'ordem_cronograma')
    list_filter = ('status', 'fase')
    inlines = [SetResultInline]
