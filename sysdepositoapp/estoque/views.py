from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, F  # Adicione models aqui
from django.db import models  # Importação do models
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from produto.models import Produto, Categoria
from .models import MovimentacaoEstoque, AjusteEstoque
from .forms import MovimentacaoEstoqueForm, AjusteEstoqueForm, RelatorioEstoqueForm

# estoque/views.py
#from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.timezone import now, timedelta
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from .models import MovimentacaoEstoque, Produto
#from django.db.models import Count, Sum, Q

from django.db.models import Case, When, Value, IntegerField

@login_required
def dashboard_estoque(request):
    """Dashboard do estoque"""
    # Estatísticas
    total_produtos = Produto.objects.count()
    
    # Usando annotate para contar produtos com estoque baixo
    
    produtos_estoque_baixo = Produto.objects.filter(
        Q(estoque_atual__lte=models.F('estoque_minimo')) & 
        Q(estoque_atual__gt=0)
    ).count()
    
    produtos_esgotados = Produto.objects.filter(estoque_atual=0).count()
    produtos_estoque_normal = total_produtos - produtos_estoque_baixo - produtos_esgotados
    
    # Movimentações recentes
    movimentacoes_recentes = MovimentacaoEstoque.objects.select_related('produto').order_by('-data_movimentacao')[:10]
    
    # Produtos com estoque baixo
    produtos_alerta = Produto.objects.filter(
        Q(estoque_atual__lte=models.F('estoque_minimo')) | Q(estoque_atual=0)
    ).order_by('estoque_atual')[:5]

    context = {
        'total_produtos': total_produtos,
        'produtos_estoque_baixo': produtos_estoque_baixo,
        'produtos_esgotados': produtos_esgotados,
        'produtos_estoque_normal': produtos_estoque_normal,
        'movimentacoes_recentes': movimentacoes_recentes,
        'produtos_alerta': produtos_alerta,
    }
    return render(request, 'estoque/dashboard_estoque.html', context)

@login_required
def lista_estoque(request):
    produtos = Produto.objects.all().select_related('categoria')
    
    # Parâmetros de filtro
    categoria_selecionada = request.GET.get('categoria', '')
    status_selecionado = request.GET.get('status_estoque', '')
    query = request.GET.get('q', '')  # Parâmetro de pesquisa
    
    # Aplicar filtro de pesquisa
    if query:
        produtos = produtos.filter(
            Q(nome__icontains=query) |
            Q(sku__icontains=query) |
            Q(descricao__icontains=query)
        )
    
    # Aplicar filtro de categoria
    if categoria_selecionada:
        produtos = produtos.filter(categoria_id=categoria_selecionada)
    
    # Aplicar filtro de status
    if status_selecionado:
        if status_selecionado == 'esgotado':
            produtos = produtos.filter(estoque_atual=0)
        elif status_selecionado == 'baixo':
            produtos = produtos.filter(estoque_atual__gt=0, estoque_atual__lte=F('estoque_minimo'))
        elif status_selecionado == 'normal':
            produtos = produtos.filter(estoque_atual__gt=F('estoque_minimo'))
    
    categorias = Categoria.objects.all()
    
    context = {
        'produtos': produtos,
        'categorias': categorias,
        'categoria_selecionada': categoria_selecionada,
        'status_selecionado': status_selecionado,
        'query': query,  # Passa a query de volta para o template
    }
    
    return render(request, 'estoque/lista_estoque.html', context)

@login_required
def movimentacao_estoque(request):
    """Registrar movimentação de estoque"""
    if request.method == 'POST':
        form = MovimentacaoEstoqueForm(request.POST)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.usuario = request.user
            movimentacao.save()
            
            messages.success(request, f'Movimentação registrada com sucesso! Estoque atual: {movimentacao.produto.estoque_atual}')
            return redirect('estoque:lista_movimentacoes')
    else:
        form = MovimentacaoEstoqueForm()
    
    context = {'form': form, 'titulo': 'Nova Movimentação'}
    return render(request, 'estoque/movimentacao_form.html', context)

@login_required
def ajuste_estoque(request):
    """Ajuste direto de estoque"""
    if request.method == 'POST':
        form = AjusteEstoqueForm(request.POST)
        if form.is_valid():
            ajuste = form.save(commit=False)
            ajuste.usuario = request.user
            ajuste.estoque_anterior = ajuste.produto.estoque_atual
            
            # Criar movimentação correspondente
            diferenca = ajuste.estoque_novo - ajuste.estoque_anterior
            if diferenca != 0:
                tipo = 'E' if diferenca > 0 else 'S'
                MovimentacaoEstoque.objects.create(
                    produto=ajuste.produto,
                    tipo=tipo,
                    quantidade=abs(diferenca),
                    motivo='ajuste',
                    observacao=ajuste.motivo,
                    usuario=request.user
                )
            
            ajuste.save()
            messages.success(request, f'Estoque ajustado com sucesso! Novo estoque: {ajuste.produto.estoque_atual}')
            return redirect('estoque:lista_estoque')
    else:
        form = AjusteEstoqueForm()
    
    context = {'form': form, 'titulo': 'Ajuste de Estoque'}
    return render(request, 'estoque/ajuste_form.html', context)

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import MovimentacaoEstoque, Produto

@login_required
def lista_movimentacoes(request):
    """Lista todas as movimentações com filtros"""
    # Query inicial otimizada
    movimentacoes = MovimentacaoEstoque.objects.select_related('produto', 'usuario').order_by('-data_movimentacao')
    
    # Filtros
    produto_id = request.GET.get('produto')
    tipo = request.GET.get('tipo')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if produto_id:
        movimentacoes = movimentacoes.filter(produto_id=produto_id)
    if tipo:
        movimentacoes = movimentacoes.filter(tipo=tipo)
    if data_inicio:
        movimentacoes = movimentacoes.filter(data_movimentacao__date__gte=data_inicio)
    if data_fim:
        movimentacoes = movimentacoes.filter(data_movimentacao__date__lte=data_fim)

    # Produtos ativos para o filtro
    produtos = Produto.objects.filter(ativo=True)
    
    # Paginação
    page = request.GET.get('page', 1)
    paginator = Paginator(movimentacoes, 25)  # 25 itens por página
    
    try:
        movimentacoes_paginadas = paginator.page(page)
    except PageNotAnInteger:
        movimentacoes_paginadas = paginator.page(1)
    except EmptyPage:
        movimentacoes_paginadas = paginator.page(paginator.num_pages)
    
    # Calcular estatísticas na query original (não paginada)
    estatisticas = {
        'entradas': movimentacoes.filter(tipo='E').count(),
        'saidas': movimentacoes.filter(tipo='S').count(),
        'total': movimentacoes.count(),
        'ultima_semana': movimentacoes.filter(
            data_movimentacao__gte=timezone.now() - timedelta(days=7)
        ).count(),
    }
    
    context = {
        'movimentacoes': movimentacoes_paginadas,
        'produtos': produtos,
        'estatisticas': estatisticas,
        'filtros_aplicados': any([produto_id, tipo, data_inicio, data_fim]),
    }
    
    return render(request, 'estoque/lista_movimentacoes.html', context)

@login_required
def relatorios_estoque(request):
    """Relatórios de estoque"""
    form = RelatorioEstoqueForm(request.GET or None)
    relatorio_data = None
    
    if form.is_valid():
        tipo_relatorio = form.cleaned_data['tipo_relatorio']
        data_inicio = form.cleaned_data['data_inicio']
        data_fim = form.cleaned_data['data_fim']
        categoria = form.cleaned_data['categoria']
        
        if tipo_relatorio == 'geral':
            produtos = Produto.objects.all()
            if categoria:
                produtos = produtos.filter(categoria=categoria)
            relatorio_data = produtos
        
        elif tipo_relatorio == 'baixo_estoque':
            relatorio_data = Produto.objects.filter(
                estoque_atual__lte=models.F('estoque_minimo'), 
                estoque_atual__gt=0
            )
            if categoria:
                relatorio_data = relatorio_data.filter(categoria=categoria)
        
        elif tipo_relatorio == 'esgotado':
            relatorio_data = Produto.objects.filter(estoque_atual=0)
            if categoria:
                relatorio_data = relatorio_data.filter(categoria=categoria)
        
        elif tipo_relatorio == 'movimentacoes':
            movimentacoes = MovimentacaoEstoque.objects.all()
            if data_inicio:
                movimentacoes = movimentacoes.filter(data_movimentacao__date__gte=data_inicio)
            if data_fim:
                movimentacoes = movimentacoes.filter(data_movimentacao__date__lte=data_fim)
            if categoria:
                movimentacoes = movimentacoes.filter(produto__categoria=categoria)
            
            relatorio_data = movimentacoes

    context = {
        'form': form,
        'relatorio_data': relatorio_data,
    }
    return render(request, 'estoque/relatorios.html', context)

@login_required
def exportar_estoque_csv(request):
    """Exportar estoque para CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="estoque.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Produto', 'SKU', 'Categoria', 'Estoque Atual', 'Estoque Mínimo', 'Status', 'Preço Custo', 'Preço Venda'])
    
    produtos = Produto.objects.all().order_by('nome')
    for produto in produtos:
        writer.writerow([
            produto.nome,
            produto.sku,
            produto.categoria.nome if produto.categoria else '',
            produto.estoque_atual,
            produto.estoque_minimo,
            produto.status_estoque,
            produto.preco_custo,
            produto.preco_venda,
        ])
    
    return response

# estoque/views.py
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.timezone import now
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from .models import MovimentacaoEstoque

def gerar_pdf_movimentacao(request, movimentacao_id):
    """Gera PDF de uma movimentação específica"""
    movimentacao = get_object_or_404(MovimentacaoEstoque, id=movimentacao_id)
    
    context = {
        'movimentacao': movimentacao,
        'gerado_em': now(),
    }
    
    # Renderiza o template HTML
    html_string = render_to_string('estoque/movimentacao_pdf.html', context)
    
    # Configuração de fontes
    font_config = FontConfiguration()
    
    # Gera o PDF
    pdf_file = HTML(
        string=html_string,
        base_url=request.build_absolute_uri()
    ).write_pdf(font_config=font_config)
    
    # Cria a resposta
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"movimentacao_{movimentacao.id}_{now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response


# estoque/views.py
def gerar_relatorio_movimentacoes(request):
    """Gera PDF com múltiplas movimentações (filtradas)"""
    # Obter parâmetros de filtro
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo')
    produto_id = request.GET.get('produto')
    
    # Filtrar movimentações
    movimentacoes = MovimentacaoEstoque.objects.all().select_related('produto')
    
    if data_inicio:
        movimentacoes = movimentacoes.filter(data_ocorrencia__gte=data_inicio)
    if data_fim:
        movimentacoes = movimentacoes.filter(data_ocorrencia__lte=data_fim)
    if tipo:
        movimentacoes = movimentacoes.filter(tipo=tipo)
    if produto_id:
        movimentacoes = movimentacoes.filter(produto_id=produto_id)
    
    movimentacoes = movimentacoes.order_by('-data_ocorrencia')
    
    context = {
        'movimentacoes': movimentacoes,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'tipo': tipo,
        'gerado_em': now(),
        'total_entradas': movimentacoes.filter(tipo='E').count(),
        'total_saidas': movimentacoes.filter(tipo='S').count(),
    }
    
    html_string = render_to_string('estoque/relatorio_movimentacoes_pdf.html', context)
    
    pdf_file = HTML(string=html_string).write_pdf()
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"relatorio_movimentacoes_{now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response

@login_required
def exportar_movimentacoes_pdf(request):
    """Exporta movimentações em PDF com filtros e estatísticas"""
    from django.db.models import Sum, Count, F, DecimalField
    from django.utils import timezone
    from datetime import datetime
    
    # Query base com related
    movimentacoes = MovimentacaoEstoque.objects.select_related('produto', 'usuario')

    # Inicializar variáveis
    produto = None
    data_inicio = None
    data_fim = None
    
    # Aplicar filtros da query string
    produto_id = request.GET.get('produto')
    tipo = request.GET.get('tipo')
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')

    # Filtro de produto
    if produto_id:
        try:
            produto = Produto.objects.get(id=produto_id)
            movimentacoes = movimentacoes.filter(produto=produto)
        except (Produto.DoesNotExist, ValueError):
            messages.warning(request, 'Produto não encontrado')

    # Filtro de tipo
    if tipo:
        movimentacoes = movimentacoes.filter(tipo=tipo)

    # Filtro de data início
    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            movimentacoes = movimentacoes.filter(data_movimentacao__date__gte=data_inicio)
        except ValueError:
            messages.warning(request, 'Data inicial inválida')

    # Filtro de data fim
    if data_fim_str:
        try:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
            movimentacoes = movimentacoes.filter(data_movimentacao__date__lte=data_fim)
        except ValueError:
            messages.warning(request, 'Data final inválida')

    # Ordenação
    movimentacoes = movimentacoes.order_by('-data_movimentacao')

    # Calcular estatísticas separadamente para evitar agregações aninhadas
    movimentacoes_entrada = movimentacoes.filter(tipo='E')
    movimentacoes_saida = movimentacoes.filter(tipo='S')

    # Estatísticas de entrada
    stats_entrada = {
        'total': movimentacoes_entrada.count(),
        'quantidade': movimentacoes_entrada.aggregate(
            total=models.Sum('quantidade')
        )['total'] or 0,
        'valor': movimentacoes_entrada.aggregate(
            total=models.Sum(
                models.F('quantidade') * models.F('produto__preco_custo'),
                output_field=models.DecimalField(max_digits=10, decimal_places=2)
            )
        )['total'] or 0
    }

    # Estatísticas de saída
    stats_saida = {
        'total': movimentacoes_saida.count(),
        'quantidade': movimentacoes_saida.aggregate(
            total=models.Sum('quantidade')
        )['total'] or 0,
        'valor': movimentacoes_saida.aggregate(
            total=models.Sum(
                models.F('quantidade') * models.F('produto__preco_venda'),
                output_field=models.DecimalField(max_digits=10, decimal_places=2)
            )
        )['total'] or 0
    }

    # Preparar contexto
    context = {
        'movimentacoes': movimentacoes,
        'filtros': {
            'produto': produto.nome if produto else 'Todos',
            'tipo': dict(MovimentacaoEstoque.TIPO_CHOICES).get(tipo, 'Todos'),
            'data_inicio': data_inicio.strftime('%d/%m/%Y') if data_inicio else 'Início',
            'data_fim': data_fim.strftime('%d/%m/%Y') if data_fim else 'Hoje',
        },
        'stats': {
            'entradas': stats_entrada,
            'saidas': stats_saida
        },
        'gerado_em': timezone.now(),
        'usuario': request.user,
    }
    
    # Renderizar o template
    html_string = render_to_string('estoque/relatorio_movimentacoes_pdf.html', context)
    
    # Configurar fontes
    font_config = FontConfiguration()
    
    # Gerar PDF
    html = HTML(
        string=html_string,
        base_url=request.build_absolute_uri(),
    )
    
    # Criar o PDF em memória
    result = html.write_pdf(
        font_config=font_config,
        presentational_hints=True
    )
    
    # Retornar como resposta HTTP
    response = HttpResponse(result, content_type='application/pdf')
    filename = f"movimentacoes_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response
    """Gera PDF com múltiplas movimentações baseado nos filtros"""
    
    # Aplicar os mesmos filtros da lista
    movimentacoes = MovimentacaoEstoque.objects.all().select_related('produto', 'usuario')
    
    # Filtros da query string
    produto_id = request.GET.get('produto')
    tipo = request.GET.get('tipo')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Aplicar filtros
    if produto_id:
        movimentacoes = movimentacoes.filter(produto_id=produto_id)
        produto = Produto.objects.get(id=produto_id)  # Para mostrar nome no relatório
    else:
        produto = None
    
    if tipo:
        movimentacoes = movimentacoes.filter(tipo=tipo)
    
    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            movimentacoes = movimentacoes.filter(data_movimentacao__date__gte=data_inicio)
        except (ValueError, TypeError):
            messages.warning(request, 'Formato de data inicial inválido')
    
    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            movimentacoes = movimentacoes.filter(data_movimentacao__date__lte=data_fim)
        except (ValueError, TypeError):
            messages.warning(request, 'Formato de data final inválido')
    
    # Ordenar por data mais recente
    movimentacoes = movimentacoes.order_by('-data_movimentacao')
    
    # Calcular estatísticas para o relatório
    stats_entrada = movimentacoes.filter(tipo='E').aggregate(
        total=Count('id'),
        quantidade=Sum('quantidade'),
        valor=Sum(F('quantidade') * F('produto__preco_custo'), output_field=models.DecimalField())
    )
    
    stats_saida = movimentacoes.filter(tipo='S').aggregate(
        total=Count('id'),
        quantidade=Sum('quantidade'),
        valor=Sum(F('quantidade') * F('produto__preco_venda'), output_field=models.DecimalField())
    )
    quantidade_total_saidas = movimentacoes.filter(tipo='S').aggregate(Sum('quantidade'))['quantidade__sum'] or 0
    
    # Produto mais movimentado
    produto_mais_movimentado = movimentacoes.values('produto__nome').annotate(
        total=Count('id')
    ).order_by('-total').first()
    
    context = {
        'movimentacoes': movimentacoes,
        'filtros_aplicados': {
            'produto': Produto.objects.filter(id=produto_id).first() if produto_id else None,
            'tipo': tipo,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        },
        'estatisticas': {
            'total_registros': movimentacoes.count(),
            'total_entradas': total_entradas,
            'total_saidas': total_saidas,
            'quantidade_entradas': quantidade_total_entradas,
            'quantidade_saidas': quantidade_total_saidas,
            'saldo_quantidade': quantidade_total_entradas - quantidade_total_saidas,
            'produto_mais_movimentado': produto_mais_movimentado,
        },
        'gerado_em': now(),
        'usuario': request.user,
    }
    
    # Renderizar template HTML
    html_string = render_to_string('estoque/relatorio_movimentacoes_pdf.html', context)
    
    # Configuração de fontes
    font_config = FontConfiguration()
    
    # Gerar PDF
    pdf_file = HTML(
        string=html_string,
        base_url=request.build_absolute_uri()
    ).write_pdf(font_config=font_config)
    
    # Criar resposta
    response = HttpResponse(pdf_file, content_type='application/pdf')
    
    # Nome do arquivo
    filename = f"relatorio_movimentacoes_{now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response

def exportar_movimentacoes_csv(request):
    # Lógica para gerar CSV
    pass