from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Produto, Categoria
from .forms import ProdutoForm, CategoriaForm, ProdutoSearchForm

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse

from django.http import JsonResponse

@login_required
def lista_produtos(request):
    """Lista todos os produtos com opções de filtro"""
    produtos = Produto.objects.all()
    form = ProdutoSearchForm(request.GET or None)
    
    if form.is_valid():
        nome = form.cleaned_data.get('nome')
        categoria = form.cleaned_data.get('categoria')
        ativo = form.cleaned_data.get('ativo')
        
        if nome:
            produtos = produtos.filter(Q(nome__icontains=nome) | Q(sku__icontains=nome))
        if categoria:
            produtos = produtos.filter(categoria=categoria)
        if ativo:
            produtos = produtos.filter(ativo=True)

    # Paginação
    page = request.GET.get('page', 1)
    paginator = Paginator(produtos, 25)  # 25 itens por página
    
    try:
        produtos_paginados = paginator.page(page)
    except PageNotAnInteger:
        produtos_paginados = paginator.page(1)
    except EmptyPage:
        produtos_paginados = paginator.page(paginator.num_pages)
    
    context = {
        'produtos': produtos_paginados,
        'produtos': produtos,
        'form': form,
        'total_produtos': produtos.count(),
    }
    return render(request, 'produto/lista_produtos.html', context)

@login_required
def produto_detalhe(request, pk):
    """Detalhes de um produto específico"""
    produto = get_object_or_404(Produto, pk=pk)
    
    # Adicionar informações calculadas ao contexto se necessário
    context = {
        'produto': produto,
    }
    return render(request, 'produto/produto_detalhe.html', context)

@login_required
def produto_novo(request):
    """Criar novo produto"""
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            produto = form.save()
            messages.success(request, f'Produto "{produto.nome}" criado com sucesso!')
            return redirect('produto:lista_produtos')
    else:
        form = ProdutoForm()
    
    context = {'form': form, 'titulo': 'Novo Produto'}
    return render(request, 'produto/produto_form.html', context)

@login_required
def produto_editar(request, pk):
    """Editar produto existente"""
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            produto = form.save()
            messages.success(request, f'Produto "{produto.nome}" atualizado com sucesso!')
            return redirect('produto:produto_detalhe', pk=produto.pk)
    else:
        form = ProdutoForm(instance=produto)
    
    context = {'form': form, 'titulo': 'Editar Produto', 'produto': produto}
    return render(request, 'produto/produto_form.html', context)

@login_required
def produto_excluir(request, pk):
    """Excluir produto"""
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        nome = produto.nome
        produto.delete()
        messages.success(request, f'Produto "{nome}" excluído com sucesso!')
        return redirect('produto:lista_produtos')
    
    context = {'produto': produto}
    return render(request, 'produto/produto_confirmar_exclusao.html', context)

@login_required
def lista_categorias(request):
    """Lista todas as categorias"""
    categorias = Categoria.objects.all()
    context = {'categorias': categorias}
    return render(request, 'produto/lista_categorias.html', context)

@login_required
def categoria_nova(request):
    """Criar nova categoria"""
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoria "{categoria.nome}" criada com sucesso!')
            return redirect('produto:lista_categorias')
    else:
        form = CategoriaForm()
    
    context = {'form': form, 'titulo': 'Nova Categoria'}
    return render(request, 'produto/categoria_form.html', context)

@login_required
def categoria_editar(request, pk):
    """Editar categoria existente"""
    categoria = get_object_or_404(Categoria, pk=pk)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoria "{categoria.nome}" atualizada com sucesso!')
            return redirect('produto:lista_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    
    context = {
        'form': form, 
        'titulo': 'Editar Categoria'
    }
    return render(request, 'produto/categoria_form.html', context)

@login_required
def categoria_excluir(request, pk):
    """Excluir categoria"""
    categoria = get_object_or_404(Categoria, pk=pk)
    
    if categoria.produto_set.exists():
        messages.error(request, f'Não é possível excluir a categoria "{categoria.nome}" porque ela possui produtos vinculados.')
        return redirect('produto:lista_categorias')
    
    if request.method == 'POST':
        nome = categoria.nome
        categoria.delete()
        messages.success(request, f'Categoria "{nome}" excluída com sucesso!')
        return redirect('produto:lista_categorias')
    
    context = {'object': categoria}
    return render(request, 'produto/categoria_confirm_delete.html', context)


@login_required
def buscar_produtos(request):
    """API para busca de produtos em tempo real - CORRIGIDA"""
    query = request.GET.get('q', '').strip()
    
    print(f"Busca recebida: '{query}'")  # Debug
    
    if len(query) < 2:
        return JsonResponse({'resultados': [], 'total': 0, 'query': query})
    
    try:
        # Busca por nome, SKU ou descrição
        produtos = Produto.objects.filter(
            Q(nome__icontains=query) | 
            Q(sku__icontains=query) |
            Q(descricao__icontains=query)
        ).filter(ativo=True).order_by('nome')[:10]

        print(f"Produtos encontrados: {produtos.count()}")  # Debug
        
        resultados = []
        for produto in produtos:
            resultado = {
                'id': produto.id,
                'nome': produto.nome,
                'sku': produto.sku,
                'preco_venda': str(produto.preco_venda),
                'estoque_atual': produto.estoque_atual,
                'categoria': produto.categoria.nome if produto.categoria else '',
            }
            
            # Adicionar URL de detalhe
            try:
                resultado['url_detalhe'] = reverse('produto:produto_detalhe', args=[produto.id])
            except:
                resultado['url_detalhe'] = f'/produto/produtos/{produto.id}/'
                
            resultados.append(resultado)

        response_data = {
            'resultados': resultados,
            'total': len(resultados),
            'query': query
        }
        
        print(f"Response: {response_data}")  # Debug
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"Erro na busca: {str(e)}")  # Debug
        return JsonResponse({'resultados': [], 'total': 0, 'error': str(e)})