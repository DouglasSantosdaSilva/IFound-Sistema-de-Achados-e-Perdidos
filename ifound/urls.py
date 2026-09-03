from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('', views.index, name='index'),
    path('objeto/<int:id>/', views.detalhar_objeto, name='detalhar_objeto'),
    path('objetos/', views.todos_objetos, name='todos_objetos'),
]