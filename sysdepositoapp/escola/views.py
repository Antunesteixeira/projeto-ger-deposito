from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.core.paginator import Paginator
import csv
from .models import Escola, ContatoEscola, HistoricoEscola
from .forms import EscolaForm, ContatoEscolaForm, HistoricoEscolaForm, EscolaSearchForm
from entrega.models import Entrega

@login_required
def lista_escolas(request):
    """Lista todas as escolas com filtros"""
    escolas = Escola.objects.all().order_by('nome')
    form_search = EscolaSearchForm(request.GET or None)
    
    # Aplicar filtros
    if form_search.is_valid():
        nome = form_search.cleaned_data.get('nome')
        cidade = form_search.cleaned_data.get('cidade')
        tipo_escola = form_search.cleaned_data.get('tipo_escola')
        nivel_ensino = form_search.cleaned_data.get('nivel_ensino')
        ativo = form_search.cleaned_data.get('ativo')
        
        if nome:
            escolas = escolas.filter(nome__icontains=nome)
        if cidade:
            escolas = escolas.filter(cidade__icontains=cidade)
        if tipo_escola:
            escolas = escolas.filter(tipo_escola=tipo_escola)
        if nivel_ensino:
            escolas = escolas.filter(nivel_ensino=nivel_ensino)
        if ativo:
            escolas = escolas.filter(ativo=True)

    # Estatísticas
    total_escolas = escolas.count()
    escolas_ativas = escolas.filter(ativo=True).count()
    escolas_inativas = escolas.filter(ativo=False).count()

    # Paginação
    page = request.GET.get('page', 1)
    paginator = Paginator(escolas, 20)  # 20 escolas por página
    
    try:
        escolas_paginadas = paginator.page(page)
    except PageNotAnInteger:
        escolas_paginadas = paginator.page(1)
    except EmptyPage:
        escolas_paginadas = paginator.page(paginator.num_pages)

    context = {
        'escolas': escolas_paginadas,
        'form_search': form_search,
        'total_escolas': total_escolas,
        'escolas_ativas': escolas_ativas,
        'escolas_inativas': escolas_inativas,
        'filtros_aplicados': any([
            request.GET.get('nome'),
            request.GET.get('cidade'),
            request.GET.get('tipo_escola'),
            request.GET.get('nivel_ensino')
        ])
    }
    
    return render(request, 'escola/lista_escolas.html', context)

@login_required
def detalhe_escola(request, pk):
    """Detalhes de uma escola específica"""
    escola = get_object_or_404(
        Escola.objects.prefetch_related('contatos', 'historico'), 
        pk=pk
    )
    
    # Entregas relacionadas
    entregas = Entrega.objects.filter(escola=escola).order_by('-data_criacao')[:10]
    
    # Formulário para histórico
    if request.method == 'POST':
        form_historico = HistoricoEscolaForm(request.POST)
        if form_historico.is_valid():
            historico = form_historico.save(commit=False)
            historico.escola = escola
            historico.usuario = request.user
            historico.save()
            messages.success(request, 'Histórico adicionado com sucesso!')
            return redirect('escola:detalhe_escola', pk=escola.pk)
    else:
        form_historico = HistoricoEscolaForm()

    context = {
        'escola': escola,
        'entregas': entregas,
        'form_historico': form_historico,
    }
    return render(request, 'escola/detalhe_escola.html', context)

@login_required
def nova_escola(request):
    """Criar nova escola"""
    ContatoFormSet = inlineformset_factory(
        Escola, ContatoEscola, form=ContatoEscolaForm, extra=1, can_delete=True
    )
    
    if request.method == 'POST':
        form = EscolaForm(request.POST)
        formset = ContatoFormSet(request.POST)
        
        print(f"DEBUG: Form is_valid: {form.is_valid()}")
        print(f"DEBUG: Form errors: {form.errors}")
        print(f"DEBUG: Formset is_valid: {formset.is_valid()}")
        print(f"DEBUG: Formset errors: {formset.errors}")
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    escola = form.save(commit=False)
                    escola.save()  # Salva primeiro para ter o ID
                    
                    formset.instance = escola
                    formset.save()
                
                # Registrar no histórico
                HistoricoEscola.objects.create(
                    escola=escola,
                    tipo_evento='cadastro',
                    descricao='Escola cadastrada no sistema',
                    usuario=request.user
                )
                
                messages.success(request, f'Escola "{escola.nome}" criada com sucesso!')
                return redirect('escola:detalhe_escola', pk=escola.pk)
                
            except Exception as e:
                messages.error(request, f'Erro ao criar escola: {str(e)}')
                print(f"ERROR: {str(e)}")
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = EscolaForm()
        formset = ContatoFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Nova Escola'
    }
    return render(request, 'escola/escola_form.html', context)

@login_required
def editar_escola(request, pk):
    escola = get_object_or_404(Escola, pk=pk)
    
    if request.method == 'POST':
        form = EscolaForm(request.POST, instance=escola)
        if form.is_valid():
            form.save()
            messages.success(request, 'Escola atualizada com sucesso!')
            return redirect('escola:detalhe_escola', pk=escola.pk)
    else:
        form = EscolaForm(instance=escola)
    
    return render(request, 'escola/escola_form.html', {
        'form': form,
        'titulo': 'Editar Escola',
        'escola': escola
    })

@login_required
def dashboard_escolas(request):
    """Dashboard de escolas"""
    from django.db.models import Sum
    
    # Estatísticas gerais
    total_escolas = Escola.objects.count()
    escolas_ativas = Escola.objects.filter(ativo=True).count()
    total_alunos = Escola.objects.aggregate(total=Sum('quantidade_alunos'))['total'] or 0
    
    # Escolas por tipo
    escolas_municipais = Escola.objects.filter(tipo_escola='municipal').count()
    
    # Distribuição por tipo com percentual
    escolas_por_tipo = []
    tipos = Escola.objects.values('tipo_escola').annotate(total=Count('id'))
    for tipo in tipos:
        percentual = (tipo['total'] / total_escolas * 100) if total_escolas > 0 else 0
        escolas_por_tipo.append({
            'tipo_escola': tipo['tipo_escola'],
            'total': tipo['total'],
            'percentual': round(percentual, 1)
        })
    
    # Escolas com mais entregas
    escolas_mais_entregas = Escola.objects.annotate(
        num_entregas=Count('entregas')
    ).order_by('-num_entregas')[:5]
    
    # Últimas escolas cadastradas
    ultimas_escolas = Escola.objects.order_by('-data_criacao')[:5]

    context = {
        'total_escolas': total_escolas,
        'escolas_ativas': escolas_ativas,
        'total_alunos': total_alunos,
        'escolas_municipais': escolas_municipais,
        'escolas_por_tipo': escolas_por_tipo,
        'escolas_mais_entregas': escolas_mais_entregas,
        'ultimas_escolas': ultimas_escolas,
    }
    return render(request, 'escola/dashboard_escolas.html', context)

@login_required
def exportar_escolas_csv(request):
    """Exportar escolas para CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="escolas.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Nome', 'Código INEP', 'Tipo', 'Nível', 'Endereço', 'Bairro', 'Cidade', 
        'Estado', 'Telefone', 'Email', 'Diretor', 'Alunos', 'Ativa'
    ])
    
    escolas = Escola.objects.all().order_by('nome')
    for escola in escolas:
        writer.writerow([
            escola.nome,
            escola.codigo_inep or '',
            escola.get_tipo_escola_display(),
            escola.get_nivel_ensino_display(),
            escola.endereco,
            escola.bairro,
            escola.cidade,
            escola.estado,
            escola.telefone or '',
            escola.email or '',
            escola.diretor or '',
            escola.quantidade_alunos,
            'Sim' if escola.ativo else 'Não'
        ])
    
    return response

@login_required
def toggle_ativa_escola(request, pk):
    """Ativar/desativar escola"""
    escola = get_object_or_404(Escola, pk=pk)
    
    if request.method == 'POST':
        escola.ativo = not escola.ativo
        escola.save()
        
        acao = "ativada" if escola.ativo else "desativada"
        messages.success(request, f'Escola "{escola.nome}" {acao} com sucesso!')
    
    return redirect('escola:detalhe_escola', pk=escola.pk)