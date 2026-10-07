import json
import os

from PIL import Image, UnidentifiedImageError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.files.images import ImageFile
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse

from .models import Perfil, Item, Solicitacao


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
    if value == 'em-analise':
        return 'em-analise'
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

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or request.GET.get('ajax') == '1'
    )

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


# =========================================================
# LOGIN
# =========================================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('perfil')

    if request.method == 'POST':
        matricula = (request.POST.get('username') or '').strip()
        senha = request.POST.get('password') or ''

        if not matricula or not senha:
            messages.error(request, 'Informe sua matrícula e senha.')
            return render(request, 'login.html')

        user = authenticate(
            request,
            username=matricula,
            password=senha
        )

        if user is not None:
            login(request, user)
            return redirect('perfil')

        messages.error(request, 'Matrícula ou senha inválidas.')

    return render(request, 'login.html')


# =========================================================
# CADASTRO
# =========================================================

def cadastro_view(request):
    if request.method == 'GET':
        return render(request, 'login.html', {
            'active_tab': 'signup'
        })

    nome_completo = request.POST.get('nome_completo', '').strip()
    matricula = request.POST.get('matricula', '').strip()
    email = request.POST.get('email', '').strip()
    curso = request.POST.get('curso', '').strip()
    turma = request.POST.get('turma', '').strip()
    senha = request.POST.get('password', '')
    senha_confirm = request.POST.get('password_confirm', '')

    if not nome_completo or not matricula or not email or not curso or not turma:
        messages.error(request, 'Preencha todos os campos obrigatórios.')
        return render(request, 'login.html', {
            'active_tab': 'signup'
        })

    if not senha:
        messages.error(request, 'Informe uma senha.')
        return render(request, 'login.html', {
            'active_tab': 'signup'
        })

    if senha != senha_confirm:
        messages.error(request, 'As senhas não coincidem.')
        return render(request, 'login.html', {
            'active_tab': 'signup'
        })

    if User.objects.filter(username=matricula).exists():
        messages.error(request, 'Esta matrícula já está cadastrada.')
        return render(request, 'login.html', {
            'active_tab': 'signup'
        })

    if User.objects.filter(email=email).exists():
        messages.error(request, 'Este e-mail já está cadastrado.')
        return render(request, 'login.html', {
            'active_tab': 'signup'
        })

    user = User.objects.create_user(
        username=matricula,
        email=email,
        password=senha
    )

    Perfil.objects.create(
        user=user,
        nome_completo=nome_completo,
        vinculo='Aluno(a)',
        curso=curso,
        turma=turma
    )

    login(request, user)

    messages.success(request, 'Conta criada com sucesso!')

    return redirect('perfil')


# =========================================================
# PERFIL
# =========================================================

@login_required
def perfil_view(request):
    perfil, _ = Perfil.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        foto = request.FILES.get('foto')
        extensoes_permitidas = {'.jpg', '.jpeg', '.png', '.webp'}
        mensagem_erro = 'Não foi possível atualizar sua foto de perfil.'

        if not foto or os.path.splitext(foto.name)[1].lower() not in extensoes_permitidas or foto.size > 5 * 1024 * 1024:
            return JsonResponse({'success': False, 'message': mensagem_erro}, status=400)

        try:
            with Image.open(foto) as imagem:
                if imagem.format not in {'JPEG', 'PNG', 'WEBP'}:
                    return JsonResponse({'success': False, 'message': mensagem_erro}, status=400)
                imagem.verify()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            return JsonResponse({'success': False, 'message': mensagem_erro}, status=400)

        foto.seek(0)
        perfil.foto = foto
        perfil.save(update_fields=['foto'])

        return JsonResponse({
            'success': True,
            'message': 'Foto de perfil atualizada com sucesso!',
            'url': perfil.foto.url,
        })

    return render(
        request,
        'perfil.html',
        {'perfil': perfil}
    )


@login_required
def editar_perfil(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    form_data = {
        'nome_completo': perfil.nome_completo or '',
        'email': request.user.email or '',
        'curso': perfil.curso or '',
        'turma': perfil.turma or '',
    }
    form_errors = []

    if request.method == 'POST':
        form_data = {
            'nome_completo': (request.POST.get('nome_completo') or '').strip(),
            'email': (request.POST.get('email') or '').strip(),
            'curso': (request.POST.get('curso') or '').strip(),
            'turma': (request.POST.get('turma') or '').strip(),
        }

        if not form_data['nome_completo']:
            form_errors.append('Informe seu nome completo.')
        if not form_data['curso']:
            form_errors.append('Informe seu curso.')
        if not form_data['turma']:
            form_errors.append('Informe sua turma.')
        if not form_data['email']:
            form_errors.append('Informe seu e-mail.')
        else:
            try:
                validate_email(form_data['email'])
            except ValidationError:
                form_errors.append('Informe um e-mail válido.')
            else:
                email_em_uso = User.objects.filter(
                    email__iexact=form_data['email']
                ).exclude(pk=request.user.pk).exists()
                if email_em_uso:
                    form_errors.append('Este e-mail já está sendo utilizado por outra conta.')

        if not form_errors:
            with transaction.atomic():
                request.user.email = form_data['email']
                request.user.save(update_fields=['email'])
                perfil.nome_completo = form_data['nome_completo']
                perfil.curso = form_data['curso']
                perfil.turma = form_data['turma']
                perfil.save(update_fields=['nome_completo', 'curso', 'turma'])

            messages.success(request, 'Dados atualizados com sucesso!')
            return redirect('perfil')

    return render(request, 'editar_perfil.html', {
        'perfil': perfil,
        'form_data': form_data,
        'form_errors': form_errors,
    })


# =========================================================
# LOGOUT
# =========================================================

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# =========================================================
# DETALHES DO ITEM
# =========================================================

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

            messages.success(
                request,
                'Sua solicitação e comprovante foram enviados com sucesso!'
            )

            return redirect('index')

        else:
            messages.error(
                request,
                'Você precisa anexar uma foto de comprovação.'
            )

    return render(
        request,
        'detalhes_item.html',
        {'item': item}
    )


# =========================================================
# CATÁLOGO
# =========================================================

def catalogo(request):
    itens = Item.objects.all().order_by('-data_registro')

    return render(
        request,
        'catalogo.html',
        {'itens': itens}
    )


# =========================================================
# CADASTRAR / EDITAR ITEM
# =========================================================

@login_required
def cadastrar_item(request):
    edit_id = request.GET.get('edit')
    item = None

    if edit_id:
        item = get_object_or_404(
            Item,
            id=edit_id,
            usuario=request.user
        )

    if request.method == 'POST':
        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest'
            or request.POST.get('ajax') == '1'
        )

        item_id = request.POST.get('item_id')

        # ---------------------------------------------
        # EDIÇÃO
        # ---------------------------------------------

        if item_id:
            item = get_object_or_404(
                Item,
                id=item_id,
                usuario=request.user
            )

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
                errors.append(
                    'Selecione se você achou ou perdeu o item.'
                )

            if errors:
                if is_ajax:
                    return JsonResponse(
                        {
                            'success': False,
                            'message': errors[0]
                        },
                        status=400
                    )

                for message in errors:
                    messages.error(request, message)

                return render(
                    request,
                    'cadastrar_item.html',
                    {
                        'item': item,
                        'edit_mode': True
                    },
                    status=400
                )

            item.nome = nome
            item.descricao = descricao
            item.local = local
            item.data_registro = data
            item.status = status

            if imagem:
                item.imagem = imagem

            item.save()

            if is_ajax:
                return JsonResponse(
                    {
                        'success': True,
                        'message': 'Item atualizado com sucesso!',
                        'redirect_url': reverse('meus_itens')
                    }
                )

            messages.success(
                request,
                'Item atualizado com sucesso!'
            )

            return redirect('meus_itens')

        # ---------------------------------------------
        # NOVO ITEM
        # ---------------------------------------------

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
            errors.append(
                'Selecione se você achou ou perdeu o item.'
            )

        if errors:
            if is_ajax:
                return JsonResponse(
                    {
                        'success': False,
                        'message': errors[0]
                    },
                    status=400
                )

            for message in errors:
                messages.error(request, message)

            return render(
                request,
                'cadastrar_item.html',
                {
                    'item': None,
                    'edit_mode': False
                },
                status=400
            )

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
            return JsonResponse(
                {
                    'success': True,
                    'message': 'Item cadastrado com sucesso!',
                    'redirect_url': reverse('meus_itens')
                }
            )

        messages.success(
            request,
            'Item cadastrado com sucesso!'
        )

        return redirect('index')

    return render(
        request,
        'cadastrar_item.html',
        {
            'item': item,
            'edit_mode': bool(item)
        }
    )


# =========================================================
# MEUS ITENS
# =========================================================

@login_required
def meus_itens(request):
    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or request.GET.get('ajax') == '1'
    )

    queryset = Item.objects.filter(
        usuario=request.user
    ).order_by('-criado_em')

    query = (request.GET.get('q') or '').strip()
    status_filter = (
        request.GET.get('status') or 'todos'
    ).strip().lower()
    date_filter = (
        request.GET.get('data') or ''
    ).strip()

    if query:
        queryset = queryset.filter(
            nome__icontains=query
        )

    if status_filter and status_filter != 'todos':
        normalized_status = _status_filter_value(status_filter)

        if normalized_status == 'em-analise':
            queryset = queryset.exclude(status__in=['achei', 'perdi'])
        elif normalized_status:
            queryset = queryset.filter(status=normalized_status)

    if date_filter:
        queryset = queryset.filter(
            data_registro=date_filter
        )

    total_items = queryset.count()
    total_perdidos = queryset.filter(status='perdi').count()
    total_encontrados = queryset.filter(status='achei').count()
    total_em_analise = queryset.exclude(status__in=['achei', 'perdi']).count()

    if request.method == 'POST' and is_ajax:
        try:
            data = (
                json.loads(
                    request.body.decode('utf-8')
                )
                if request.body
                else {}
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Dados inválidos.'
                },
                status=400
            )

        action = data.get('action')
        item_id = data.get('item_id')

        if action == 'delete_item':
            item = get_object_or_404(
                Item,
                id=item_id,
                usuario=request.user
            )

            item.delete()

            return JsonResponse(
                {
                    'success': True,
                    'message': 'Item excluído com sucesso.'
                }
            )

        return JsonResponse(
            {
                'success': False,
                'message': 'Ação inválida.'
            },
            status=400
        )

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
            'data': (
                item.data_registro.strftime('%d/%m/%Y')
                if item.data_registro
                else '—'
            ),
            'detalhes': item.descricao,
            'status': _status_label(item.status),
            'status_key': item.status,
        }
        for item in page_obj.object_list
    ]

    stats = {
        'total': total_items,
        'perdidos': total_perdidos,
        'encontrados': total_encontrados,
        'em_analise': total_em_analise,
    }

    summary = {
        'totalItems': total_items,
        'perdidos': total_perdidos,
        'encontrados': total_encontrados,
        'emAnalise': total_em_analise,
    }

    if is_ajax:
        return JsonResponse(
            {
                'success': True,
                'message': 'Itens carregados com sucesso.',
                'items': items_payload,
                'data': items_payload,
                'stats': stats,
                'summary': summary,
                'pagination': {
                    'page': page_obj.number,
                    'totalPages': paginator.num_pages,
                    'totalItems': total_items,
                },
            }
        )

    return render(
        request,
        'meus_itens.html',
        {
            'items': items_payload
        }
    )