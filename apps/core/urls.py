from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),

    # Torneio
    path('torneios/', views.torneio_list, name='admin_torneio_list'),
    path('torneios/novo/', views.torneio_create, name='admin_torneio_create'),
    path('torneios/<int:pk>/', views.torneio_detail, name='admin_torneio_detail'),
    path('torneios/<int:pk>/editar/', views.torneio_edit, name='admin_torneio_edit'),
    path('torneios/<int:pk>/excluir/', views.torneio_delete, name='admin_torneio_delete'),
    path('torneios/<int:pk>/avancar-fase/', views.torneio_avancar_fase, name='admin_torneio_avancar_fase'),

    # Regra de Pontuação
    path('regras/', views.regra_list, name='admin_regra_list'),
    path('regras/nova/', views.regra_create, name='admin_regra_create'),
    path('regras/<int:pk>/editar/', views.regra_edit, name='admin_regra_edit'),
    path('regras/<int:pk>/excluir/', views.regra_delete, name='admin_regra_delete'),

    # Equipe
    path('torneios/<int:torneio_pk>/equipes/nova/', views.equipe_create, name='admin_equipe_create'),
    path('equipes/<int:pk>/editar/', views.equipe_edit, name='admin_equipe_edit'),
    path('equipes/<int:pk>/excluir/', views.equipe_delete, name='admin_equipe_delete'),

    # Fase
    path('torneios/<int:torneio_pk>/fases/nova/', views.fase_create, name='admin_fase_create'),
    path('fases/<int:pk>/', views.fase_detail, name='admin_fase_detail'),
    path('fases/<int:pk>/editar/', views.fase_edit, name='admin_fase_edit'),
    path('fases/<int:pk>/excluir/', views.fase_delete, name='admin_fase_delete'),
    path('fases/<int:pk>/sortear/', views.fase_sortear_equipes, name='admin_fase_sortear'),
    path('fases/<int:pk>/gerar-partidas/', views.fase_gerar_partidas, name='admin_fase_gerar_partidas'),
    path('fases/<int:pk>/resetar/', views.fase_resetar, name='admin_fase_resetar'),
    path('fases/<int:pk>/gerar-eliminatoria/', views.fase_gerar_eliminatoria, name='admin_fase_gerar_eliminatoria'),

    # Grupo
    path('fases/<int:fase_pk>/grupos/novo/', views.grupo_create, name='admin_grupo_create'),
    path('grupos/<int:pk>/editar/', views.grupo_edit, name='admin_grupo_edit'),
    path('grupos/<int:pk>/excluir/', views.grupo_delete, name='admin_grupo_delete'),
    path('grupos/<int:pk>/classificacao/', views.grupo_classificacao, name='admin_grupo_classificacao'),

    # Partida
    path('fases/<int:fase_pk>/partidas/nova/', views.partida_create, name='admin_partida_create'),
    path('partidas/<int:pk>/editar/', views.partida_edit, name='admin_partida_edit'),
    path('partidas/<int:pk>/excluir/', views.partida_delete, name='admin_partida_delete'),
    path('partidas/<int:pk>/iniciar/', views.partida_iniciar, name='admin_partida_iniciar'),
    path('partidas/<int:pk>/wo/', views.partida_aplicar_wo, name='admin_partida_aplicar_wo'),
]
