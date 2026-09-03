import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Perfil

SUAP_AUTH_URL = 'https://suap.ifrn.edu.br/api/v2/autenticacao/token/'
SUAP_DADOS_URL = 'https://suap.ifrn.edu.br/api/v2/minhas-informacoes/meus-dados/'

def login_view(request):
    if request.user.is_authenticated:
        return redirect('perfil')

    if request.method == 'POST':
        matricula = request.POST.get('username')
        senha = request.POST.get('password')

        try:
            auth_response = requests.post(SUAP_AUTH_URL, data={'username': matricula, 'password': senha})

            if auth_response.status_code == 200:
                access_token = auth_response.json().get('access')

                # Requisita os dados completos do aluno no SUAP
                headers = {'Authorization': f'Bearer {access_token}'}
                dados_response = requests.get(SUAP_DADOS_URL, headers=headers)

                if dados_response.status_code == 200:
                    dados = dados_response.json()

                    # Garante que o User nativo existe
                    user, _ = User.objects.get_or_create(username=matricula)
                    user.email = dados.get('email', '')
                    user.save()

                    # Trata o vínculo (ex: Aluno / Aluna)
                    sexo = dados.get('sexo', 'M')
                    tipo_vinculo = dados.get('vinculo', {}).get('vinculo', 'Aluno')
                    if tipo_vinculo.lower() == 'aluno' and sexo == 'F':
                        tipo_vinculo = 'Aluna'

                    # Trata a foto
                    url_foto = dados.get('url_foto_150x200', '')
                    foto_completa = f"https://suap.ifrn.edu.br{url_foto}" if url_foto else None

                    # Cria ou atualiza o perfil do aluno no banco de dados local
                    perfil, _ = Perfil.objects.get_or_create(user=user)
                    perfil.nome_completo = dados.get('nome_usual') or dados.get('vinculo', {}).get('nome', '')
                    perfil.vinculo = tipo_vinculo
                    perfil.curso = dados.get('vinculo', {}).get('curso', 'Téc. em Informática para Internet')
                    perfil.turma = dados.get('vinculo', {}).get('turma', '')
                    perfil.foto_url = foto_completa
                    perfil.save()

                    login(request, user)
                    return redirect('perfil')

            else:
                messages.error(request, 'Matrícula ou senha do SUAP inválidas.')

        except requests.exceptions.RequestException:
            messages.error(request, 'Erro ao conectar com o SUAP. Tente novamente.')

    return render(request, 'login.html')

@login_required
def perfil_view(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    return render(request, 'perfil.html', {'perfil': perfil})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def index(request):
    query = request.GET.get('q')
    
    itens = [
        {'id': 1, 'nome': 'Mochila Preta', 'imagem': None},
        {'id': 2, 'nome': 'Garrafa Térmica', 'imagem': None},
        {'id': 3, 'nome': 'Chaveiro com Chaves', 'imagem': None},
    ]

    if query:
        itens = [item for item in itens if query.lower() in item['nome'].lower()]

    return render(request, 'index.html', {'itens': itens})


def detalhar_objeto(request, id):
    item = {'id': id, 'nome': f'Objeto #{id}', 'descricao': 'Descrição detalhada do item...', 'imagem': None}
    return render(request, 'detalhar_objeto.html', {'item': item})


def todos_objetos(request):
    itens = [
        {'id': 1, 'nome': 'Mochila Preta', 'imagem': None},
        {'id': 2, 'nome': 'Garrafa Térmica', 'imagem': None},
        {'id': 3, 'nome': 'Chaveiro com Chaves', 'imagem': None},
        {'id': 4, 'nome': 'Casaco de Frio', 'imagem': None},
    ]
    return render(request, 'todos_objetos.html', {'itens': itens})