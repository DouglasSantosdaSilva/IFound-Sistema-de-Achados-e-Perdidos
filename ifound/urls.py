
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('logout/', views.logout_view, name='logout'),

    path('perfil/', views.perfil_view, name='perfil'),

    path('', views.index, name='index'),
    path('catalogo/', views.catalogo, name='catalogo'),

    path('meus-itens/', views.meus_itens, name='meus_itens'),

    path('item/<int:id>/', views.detalhar_item, name='detalhar_item'),

    path('cadastrar/', views.cadastrar_item, name='cadastrar_item'),
]