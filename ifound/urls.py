
from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

urlpatterns = [
    path(
        'senha/redefinir/',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset_form.html',
            email_template_name='password_reset_email.txt',
            subject_template_name='password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'senha/redefinir/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'senha/redefinir/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'senha/redefinir/concluido/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/indicadores/', views.admin_indicadores, name='admin_indicadores'),
    path('admin-dashboard/prazos/', views.admin_prazos, name='admin_prazos'),
    path('admin-dashboard/solicitacoes/', views.admin_solicitacoes, name='admin_solicitacoes'),
    path('admin-dashboard/solicitantes/<int:user_id>/', views.admin_consultar_perfil_solicitante, name='admin_consultar_perfil_solicitante'),
    path('admin-dashboard/solicitacoes/<int:id>/', views.admin_detalhar_solicitacao, name='admin_detalhar_solicitacao'),
    path('admin-dashboard/solicitacoes/<int:id>/atualizar/', views.admin_atualizar_solicitacao, name='admin_atualizar_solicitacao'),
    path('login/', views.login_view, name='login'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('logout/', views.logout_view, name='logout'),

    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/alterar-senha/', views.alterar_senha, name='alterar_senha'),

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
