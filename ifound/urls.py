
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('logout/', views.logout_view, name='logout'),

    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    path('', views.index, name='index'),
    path('catalogo/', views.catalogo, name='catalogo'),

    path('meus-itens/', views.meus_itens, name='meus_itens'),
    path('minhas-solicitacoes/', views.minhas_solicitacoes, name='minhas_solicitacoes'),
    path('solicitacao/<int:id>/', views.detalhar_solicitacao, name='detalhar_solicitacao'),
    path('item/<int:item_id>/verificar-solicitacao/', views.verificar_solicitacao_item, name='verificar_solicitacao_item'),
    path('item/<int:item_id>/solicitar/', views.confirmar_solicitacao, name='confirmar_solicitacao'),

    path('item/<int:id>/', views.detalhar_item, name='detalhar_item'),

    path('cadastrar/', views.cadastrar_item, name='cadastrar_item'),
]