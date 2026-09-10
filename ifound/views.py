import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Perfil, Item, Solicitacao

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

                headers = {'Authorization': f'Bearer {access_token}'}
                dados_response = requests.get(SUAP_DADOS_URL, headers=headers)

                if dados_response.status_code == 200:
                    dados = dados_response.json()

                    user, _ = User.objects.get_or_create(username=matricula)
                    user.email = dados.get('email', '')
                    user.save()

                    sexo = dados.get('sexo', 'M')
                    tipo_vinculo = dados.get('vinculo', {}).get('vinculo', 'Aluno')
                    if tipo_vinculo.lower() == 'aluno' and sexo == 'F':
                        tipo_vinculo = 'Aluna'

                    url_foto = dados.get('url_foto_150x200', '')
                    foto_completa = f"https://suap.ifrn.edu.br{url_foto}" if url_foto else None

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
    
    itens = Item.objects.exclude(status='devolvido').order_by('-data_registro')

    if query:
        itens = itens.filter(nome__icontains=query)

    return render(request, 'index.html', {'itens': itens})


@login_required
def detalhar_item(request, id):
    item = get_object_or_404(Item, id=id)

    if request.method == 'POST':
        foto = request.FILES.get('foto_comprovante')

        if foto:
            Solicitacao.objects.create(
                item=item,
                solicitante=request.user,
                foto_comprovante=foto
            )
            messages.success(request, 'Sua solicitação e comprovante foram enviados com sucesso!')
            return redirect('index')
        else:
            messages.error(request, 'Você precisa anexar uma foto de comprovação.')

    return render(request, 'detalhar_item.html', {'item': item})

def catalogo(request):
    itens = Item.objects.all().order_by('-data_registro')
    return render(request, 'catalogo.html', {'itens': itens})

@login_required
def cadastrar_item(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        local = request.POST.get('local')
        data = request.POST.get('data')
        status = request.POST.get('status')
        imagem = request.FILES.get('imagem')

        Item.objects.create(
            nome=nome,
            descricao=descricao,
            local=local,
            data_registro=data,
            status=status,
            imagem=imagem,
            usuario=request.user
        )
        messages.success(request, 'Item cadastrado com sucesso!')
        return redirect('index')

    return render(request, 'cadastrar_item.html')