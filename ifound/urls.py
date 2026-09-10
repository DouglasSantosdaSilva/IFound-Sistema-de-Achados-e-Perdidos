from django.urls import path
from django.http import HttpResponse
from . import views

def temp_view(request):
    return HttpResponse("Página em construção")

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('', views.index, name='index'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('meus-itens/', temp_view, name='meus_itens'),
    path('item/<int:id>/', views.detalhar_item, name='detalhar_item'),
    path('cadastrar/', views.cadastrar_item, name='cadastrar_item'),
]