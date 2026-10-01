import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse
from .models import Perfil, Item, Solicitacao

SUAP_AUTH_URL = 'https://suap.ifrn.edu.br/api/v2/autenticacao/token/'
SUAP_DADOS_URL = 'https://suap.ifrn.edu.br/api/v2/minhas-informacoes/meus-dados/'


def _status_label(status_value):
    if status_value == 'perdi':
        return 'Perdido'
    if status_value == 'achei':
        return 'Encontrado'
    return 'Em análise'


def _serializar_item(item):
    return {
        'id': item.id,
        'titulo': item.nome,
        'data': item.data_registro.strftime('%d/%m/%Y') if item.data_registro else 'Não informado',
        'detalhes': item.descricao,
        'status': _status_label(item.status),
        'status_key': item.status,
        'imagem': item.imagem.url if item.imagem else None,
        'url_detalhe': f'/item/{item.id}/',
    }


def _status_filter_value(value):
    if value == 'perdido':
        return 'perdi'
    if value == 'encontrado':
        return 'achei'
    return None


def index(request):
    query = (request.GET.get('q') or '').strip()
    page_number = request.GET.get('page', 1)

    try:
        page_number = int(page_number)
    except (TypeError, ValueError):
        page_number = 1

    itens = Item.objects.exclude(status='devolvido').order_by('-data_registro')

    if query:
        itens = itens.filter(nome__icontains=query)

    paginator = Paginator(itens, 6)
    page_obj = paginator.get_page(page_number)

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'

    if is_ajax:
        payload = {
            'items': [_serializar_item(item) for item in page_obj.object_list],
            'page': page_obj.number,
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'has_next_page': page_obj.has_next(),
            'total_items': paginator.count,
            'query': query,
        }
        return JsonResponse(payload)

    return render(request, 'index.html', {
        'itens': page_obj.object_list,
        'page_obj': page_obj,
        'query': query,
    })


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

    return render(request, 'detalhes_item.html', {'item': item})


def catalogo(request):
    itens = Item.objects.all().order_by('-data_registro')
    return render(request, 'catalogo.html', {'itens': itens})


@login_required
def cadastrar_item(request):
    edit_id = request.GET.get('edit')
    item = None

    if edit_id:
        item = get_object_or_404(Item, id=edit_id, usuario=request.user)

    if request.method == 'POST':
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1'
        item_id = request.POST.get('item_id')

        if item_id:
            item = get_object_or_404(Item, id=item_id, usuario=request.user)
            nome = (request.POST.get('nome') or '').strip()
            descricao = (request.POST.get('descricao') or '').strip()
            local = (request.POST.get('local') or '').strip()
            data = request.POST.get('data')
            status = request.POST.get('status')
            imagem = request.FILES.get('imagem')

            errors = []
            if not nome:
                errors.append('Informe o tipo do objeto.')
            if not descricao:
                errors.append('Descreva o objeto.')
            if not local:
                errors.append('Informe o local do ocorrido.')
            if not data:
                errors.append('Selecione a data do registro.')
            if not status:
                errors.append('Selecione se você achou ou perdeu o item.')

            if errors:
                if is_ajax:
                    return JsonResponse({'success': False, 'message': errors[0]}, status=400)
                for message in errors:
                    messages.error(request, message)
                return render(request, 'cadastrar_item.html', {'item': item, 'edit_mode': True}, status=400)

            item.nome = nome
            item.descricao = descricao
            item.local = local
            item.data_registro = data
            item.status = status
            if imagem:
                item.imagem = imagem
            item.save()

            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Item atualizado com sucesso!', 'redirect_url': reverse('meus_itens')})

            messages.success(request, 'Item atualizado com sucesso!')
            return redirect('meus_itens')

        nome = (request.POST.get('nome') or '').strip()
        descricao = (request.POST.get('descricao') or '').strip()
        local = (request.POST.get('local') or '').strip()
        data = request.POST.get('data')
        status = request.POST.get('status')
        imagem = request.FILES.get('imagem')

        errors = []
        if not nome:
            errors.append('Informe o tipo do objeto.')
        if not descricao:
            errors.append('Descreva o objeto.')
        if not local:
            errors.append('Informe o local do ocorrido.')
        if not data:
            errors.append('Selecione a data do registro.')
        if not status:
            errors.append('Selecione se você achou ou perdeu o item.')

        if errors:
            if is_ajax:
                return JsonResponse({'success': False, 'message': errors[0]}, status=400)
            for message in errors:
                messages.error(request, message)
            return render(request, 'cadastrar_item.html', {'item': None, 'edit_mode': False}, status=400)

        item = Item.objects.create(
            nome=nome,
            descricao=descricao,
            local=local,
            data_registro=data,
            status=status,
            imagem=imagem,
            usuario=request.user
        )

        if is_ajax:
            return JsonResponse({'success': True, 'message': 'Item cadastrado com sucesso!', 'redirect_url': reverse('meus_itens')})

        messages.success(request, 'Item cadastrado com sucesso!')
        return redirect('index')

    return render(request, 'cadastrar_item.html', {'item': item, 'edit_mode': bool(item)})


@login_required
def meus_itens(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    queryset = Item.objects.filter(usuario=request.user).order_by('-criado_em')

    query = (request.GET.get('q') or '').strip()
    status_filter = (request.GET.get('status') or 'todos').strip().lower()
    date_filter = (request.GET.get('data') or '').strip()

    if query:
        queryset = queryset.filter(nome__icontains=query)

    if status_filter and status_filter != 'todos':
        normalized_status = _status_filter_value(status_filter)
        if normalized_status:
            queryset = queryset.filter(status=normalized_status)

    if date_filter:
        queryset = queryset.filter(data_registro=date_filter)

    total_items = queryset.count()
    total_perdidos = queryset.filter(status='perdi').count()
    total_encontrados = queryset.filter(status='achei').count()
    total_em_analise = 0

    if request.method == 'POST' and is_ajax:
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Dados inválidos.'}, status=400)

        action = data.get('action')
        item_id = data.get('item_id')

        if action == 'delete_item':
            item = get_object_or_404(Item, id=item_id, usuario=request.user)
            item.delete()
            return JsonResponse({'success': True, 'message': 'Item excluído com sucesso.'})

        return JsonResponse({'success': False, 'message': 'Ação inválida.'}, status=400)

    page_number = request.GET.get('page', 1)

    try:
        page_number = int(page_number)
    except (TypeError, ValueError):
        page_number = 1

    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(page_number)

    items_payload = [
        {
            'id': item.id,
            'titulo': item.nome,
            'data': item.data_registro.strftime('%d/%m/%Y') if item.data_registro else '—',
            'detalhes': item.descricao,
            'status': _status_label(item.status),
            'status_key': item.status,
        }
        for item in page_obj.object_list
    ]

    summary = {
        'totalItems': total_items,
        'perdidos': total_perdidos,
        'encontrados': total_encontrados,
        'emAnalise': total_em_analise,
    }

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': 'Itens carregados com sucesso.',
            'data': items_payload,
            'summary': summary,
            'pagination': {
                'page': page_obj.number,
                'totalPages': paginator.num_pages,
                'totalItems': total_items,
            },
        })

    return render(request, 'meus_itens.html', {'items': items_payload})