from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from .models import Entrega, ItemEntrega, HistoricoStatus
from .forms import EntregaForm, ItemEntregaForm, FiltroEntregaForm, ItemEntregaFormSet  # REMOVER EscolaForm
from produto.models import Produto
from escola.models import Escola

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.timezone import now
import os
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from .models import Entrega

def gerar_pdf_entrega(request, entrega_id):
    entrega = get_object_or_404(Entrega, id=entrega_id)
    
    context = {
        'entrega': entrega,
        'gerado_em': now(),
        'STATIC_ROOT': settings.STATIC_ROOT,
    }
    
    # Renderiza o template HTML
    html_string = render_to_string('entrega/entrega_pdf.html', context)
    
    # Configuração de fontes
    font_config = FontConfiguration()
    
    # Gera o PDF
    pdf_file = HTML(
        string=html_string,
        base_url=request.build_absolute_uri()
    ).write_pdf(font_config=font_config)
    
    # Cria a resposta
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"entrega_{entrega.numero_pedido}_{now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def lista_entregas(request):
    """Lista todas as entregas com filtros"""
    entregas = Entrega.objects.select_related('escola').prefetch_related('itens').all()
    form = FiltroEntregaForm(request.GET or None)
    
    if form.is_valid():
        status = form.cleaned_data.get('status')
        tipo_entrega = form.cleaned_data.get('tipo_entrega')
        escola = form.cleaned_data.get('escola')
        data_inicio = form.cleaned_data.get('data_inicio')
        data_fim = form.cleaned_data.get('data_fim')
        
        if status:
            entregas = entregas.filter(status=status)
        if tipo_entrega:
            entregas = entregas.filter(tipo_entrega=tipo_entrega)
        if escola:
            entregas = entregas.filter(escola=escola)
        if data_inicio:
            entregas = entregas.filter(data_entrega_prevista__gte=data_inicio)
        if data_fim:
            entregas = entregas.filter(data_entrega_prevista__lte=data_fim)

    # Estatísticas
    total_entregas = entregas.count()
    entregas_planejadas = entregas.filter(status='planejada').count()
    entregas_preparacao = entregas.filter(status='preparacao').count()
    entregas_transporte = entregas.filter(status='transporte').count()
    entregas_entregues = entregas.filter(status='entregue').count()
    entregas_atrasadas = entregas.filter(
        status__in=['planejada', 'preparacao', 'transporte'],
        data_entrega_prevista__lt=timezone.now().date()
    ).count()

    context = {
        'entregas': entregas,
        'form': form,
        'total_entregas': total_entregas,
        'entregas_planejadas': entregas_planejadas,
        'entregas_preparacao': entregas_preparacao,
        'entregas_transporte': entregas_transporte,
        'entregas_entregues': entregas_entregues,
        'entregas_atrasadas': entregas_atrasadas,
    }
    return render(request, 'entrega/lista_entregas.html', context)

@login_required
@transaction.atomic
def nova_entrega(request):
    """Criar nova entrega com itens"""
    # Definir o FormSet
    ItemEntregaFormSetInline = inlineformset_factory(
        Entrega, ItemEntrega, form=ItemEntregaForm, 
        formset=ItemEntregaFormSet, extra=1, can_delete=True
    )
    
    if request.method == 'POST':
        form = EntregaForm(request.POST)
        formset = ItemEntregaFormSetInline(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    entrega = form.save(commit=False)
                    entrega.usuario = request.user
                    entrega.save()
                    
                    # Salvar histórico inicial
                    HistoricoStatus.objects.create(
                        entrega=entrega,
                        status_anterior='',
                        status_novo=entrega.status,
                        usuario=request.user,
                        observacao='Entrega criada'
                    )
                    
                    # Salvar itens
                    formset.instance = entrega
                    saved_items = formset.save()

                    '''
                    # Diminuir estoque para cada item salvo (criar movimentação de saída)
                    try:
                        from estoque.models import MovimentacaoEstoque
                        for item in entrega.itens.all():
                            try:
                                MovimentacaoEstoque.objects.create(
                                    produto=item.produto,
                                    tipo='S',  # Saída
                                    quantidade=item.quantidade,
                                    motivo='entrega',
                                    observacao=f'Reserva para entrega {entrega.numero_pedido} - {entrega.escola.nome}',
                                    usuario=request.user
                                )
                            except Exception:
                                # não falhar todo o processo se movimentação não puder ser criada
                                pass
                    except Exception:
                        # se o app de estoque não existir ou falhar, prosseguir sem bloquear
                        pass
                    '''
                    messages.success(request, f'Entrega {entrega.numero_pedido} criada com sucesso!')
                    return redirect('entrega:detalhe_entrega', pk=entrega.pk)
                    
            except Exception as e:
                messages.error(request, f'Erro ao criar entrega: {str(e)}')
    else:
        form = EntregaForm()
        formset = ItemEntregaFormSetInline()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Nova Entrega'
    }
    return render(request, 'entrega/entrega_form.html', context)

@login_required
def detalhe_entrega(request, pk):
    """Detalhes de uma entrega específica"""
    entrega = get_object_or_404(Entrega.objects.prefetch_related('itens__produto'), pk=pk)
    itens = entrega.itens.all()
    
    context = {
        'entrega': entrega,
        'itens': itens,
    }
    return render(request, 'entrega/detalhe_entrega.html', context)

@login_required
@transaction.atomic
def editar_entrega(request, pk):
    """Editar entrega existente"""
    entrega = get_object_or_404(Entrega, pk=pk)
    
    # Definir o FormSet
    ItemEntregaFormSetInline = inlineformset_factory(
        Entrega, ItemEntrega, form=ItemEntregaForm, 
        formset=ItemEntregaFormSet, extra=1, can_delete=True
    )
    
    if request.method == 'POST':
        form = EntregaForm(request.POST, instance=entrega)
        formset = ItemEntregaFormSetInline(request.POST, instance=entrega)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Verificar se o status foi alterado
                    status_anterior = entrega.status
                    entrega = form.save()
                    
                    if status_anterior != entrega.status:
                        HistoricoStatus.objects.create(
                            entrega=entrega,
                            status_anterior=status_anterior,
                            status_novo=entrega.status,
                            usuario=request.user,
                            observacao='Status alterado'
                        )
                    
                    # Capturar quantidades antigas antes de salvar alterações do formset
                    old_quantities = {it.produto_id: it.quantidade for it in entrega.itens.all()}

                    formset.save()

                    # Depois de salvar, comparar quantidades e criar movimentações para ajustar estoque
                    try:
                        from estoque.models import MovimentacaoEstoque
                        new_quantities = {it.produto_id: it.quantidade for it in entrega.itens.all()}

                        product_ids = set(list(old_quantities.keys()) + list(new_quantities.keys()))
                        for pid in product_ids:
                            old_q = old_quantities.get(pid, 0)
                            new_q = new_quantities.get(pid, 0)
                            if new_q > old_q:
                                # houve aumento -> criar saída adicional
                                try:
                                    MovimentacaoEstoque.objects.create(
                                        produto_id=pid,
                                        tipo='S',
                                        quantidade=(new_q - old_q),
                                        motivo='entrega',
                                        observacao=f'Ajuste entrega {entrega.numero_pedido} (aumento de {new_q-old_q})',
                                        usuario=request.user
                                    )
                                except Exception:
                                    pass
                            elif new_q < old_q:
                                # houve diminuição -> devolver ao estoque (entrada)
                                try:
                                    MovimentacaoEstoque.objects.create(
                                        produto_id=pid,
                                        tipo='E',
                                        quantidade=(old_q - new_q),
                                        motivo='entrega',
                                        observacao=f'Ajuste entrega {entrega.numero_pedido} (redução de {old_q-new_q})',
                                        usuario=request.user
                                    )
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    
                    messages.success(request, f'Entrega {entrega.numero_pedido} atualizada com sucesso!')
                    return redirect('entrega:detalhe_entrega', pk=entrega.pk)
                    
            except Exception as e:
                messages.error(request, f'Erro ao atualizar entrega: {str(e)}')
    else:
        form = EntregaForm(instance=entrega)
        formset = ItemEntregaFormSetInline(instance=entrega)
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Editar Entrega',
        'entrega': entrega,
    }
    return render(request, 'entrega/entrega_form.html', context)

# ... resto das views permanecem iguais

@login_required
@transaction.atomic
def finalizar_entrega(request, pk):
    """Finalizar entrega e atualizar estoque"""
    entrega = get_object_or_404(Entrega, pk=pk)
    
    # Verificações de segurança
    if entrega.status == 'ENTREGUE' or entrega.status == 'entregue':
        messages.warning(request, f'Entrega {entrega.numero_pedido} já foi finalizada anteriormente.')
        return redirect('entrega:detalhe_entrega', pk=entrega.pk)
    
    if not entrega.itens.exists():
        messages.error(request, f'Entrega {entrega.numero_pedido} não possui itens para entregar.')
        return redirect('entrega:detalhe_entrega', pk=entrega.pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                from estoque.models import MovimentacaoEstoque
                
                # VERIFICAÇÃO DE ESTOQUE
                problemas_estoque = []
                for item in entrega.itens.all():
                    produto = item.produto
                    if produto.estoque_atual < item.quantidade:
                        problemas_estoque.append(
                            f"{produto.nome} (estoque: {produto.estoque_atual}, necessário: {item.quantidade})"
                        )
                
                if problemas_estoque:
                    messages.error(request, 
                        f'❌ Estoque insuficiente para finalizar a entrega:<br>' + 
                        '<br>'.join(problemas_estoque)
                    )
                    return redirect('entrega:detalhe_entrega', pk=entrega.pk)
                
                # PROCESSAR ITENS E ATUALIZAR ESTOQUE
                itens_processados = []
                for item in entrega.itens.all():
                    produto = item.produto
                    estoque_anterior = produto.estoque_atual
                    
                    # 1. Criar movimentação de estoque
                    MovimentacaoEstoque.objects.create(
                        produto=produto,
                        tipo='SAIDA',  # Ajuste conforme seu modelo
                        quantidade=item.quantidade,
                        motivo='ENTREGA',  # Ajuste conforme seu modelo
                        observacao=f'Entrega {entrega.numero_pedido} - {entrega.escola.nome}',
                        usuario=request.user
                    )
                    
                    # 2. ATUALIZAR ESTOQUE DO PRODUTO
                    produto.estoque_atual = estoque_anterior - item.quantidade
                    produto.save(update_fields=['estoque_atual'])  # Salva apenas o campo necessário
                    
                    itens_processados.append({
                        'produto': produto.nome,
                        'quantidade': item.quantidade,
                        'estoque_anterior': estoque_anterior,
                        'novo_estoque': produto.estoque_atual
                    })
                
                # ✅ CORREÇÃO: ATUALIZAR STATUS E DATA DA ENTREGA
                status_anterior = entrega.status
                
                # Use os valores exatos do seu modelo
                entrega.status = 'entregue'  # Ou 'entregue' - verifique seu modelo
                entrega.data_entrega_real = timezone.now().date()  # ✅ DATA CORRETA
                
                # ✅ SALVAR A ENTREGA COM TODOS OS CAMPOS ATUALIZADOS
                entrega.save()  # Isso salva status E data_entrega_real
                
                # Registrar histórico
                HistoricoStatus.objects.create(
                    entrega=entrega,
                    status_anterior=status_anterior,
                    status_novo=entrega.status,
                    usuario=request.user,
                    observacao=f'Entrega finalizada em {timezone.now().strftime("%d/%m/%Y %H:%M")}'
                )
                
                # Mensagem de sucesso detalhada
                itens_info = '<br>'.join([
                    f"• {item['produto']}: {item['quantidade']} un. (Estoque: {item['estoque_anterior']} → {item['novo_estoque']})"
                    for item in itens_processados
                ])
                
                messages.success(request, 
                    f'✅ Entrega {entrega.numero_pedido} finalizada com sucesso!<br>'
                    f'<strong>Data de entrega:</strong> {timezone.now().strftime("%d/%m/%Y")}<br><br>'
                    f'<strong>Itens processados:</strong><br>{itens_info}'
                )
                return redirect('entrega:detalhe_entrega', pk=entrega.pk)
                
        except Exception as e:
            messages.error(request, f'❌ Erro ao finalizar entrega: {str(e)}')
            # Log para debug
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Erro ao finalizar entrega {entrega.pk}: {str(e)}', exc_info=True)
    
    # Se não for POST, redirecionar para detalhes
    return redirect('entrega:detalhe_entrega', pk=entrega.pk)

@login_required
def lista_escolas(request):
    """Lista todas as escolas"""
    escolas = Escola.objects.all()
    context = {'escolas': escolas}
    return render(request, 'entrega/lista_escolas.html', context)

@login_required
def nova_escola(request):
    """Criar nova escola"""
    if request.method == 'POST':
        form = EscolaForm(request.POST)
        if form.is_valid():
            escola = form.save()
            messages.success(request, f'Escola "{escola.nome}" criada com sucesso!')
            return redirect('entrega:lista_escolas')
    else:
        form = EscolaForm()
    
    context = {'form': form, 'titulo': 'Nova Escola'}
    return render(request, 'entrega/escola_form.html', context)

@login_required
def dashboard_entregas(request):
    """Dashboard de entregas"""
    # Estatísticas
    total_entregas = Entrega.objects.count()
    entregas_hoje = Entrega.objects.filter(data_entrega_prevista=timezone.now().date()).count()
    entregas_semana = Entrega.objects.filter(
        data_entrega_prevista__range=[
            timezone.now().date(),
            timezone.now().date() + timedelta(days=7)
        ]
    ).count()
    
    # Entregas por status
    entregas_por_status = Entrega.objects.values('status').annotate(
        total=Count('id')
    ).order_by('status')
    
    # Próximas entregas
    proximas_entregas = Entrega.objects.filter(
        status__in=['planejada', 'preparacao'],
        data_entrega_prevista__gte=timezone.now().date()
    ).order_by('data_entrega_prevista')[:10]
    
    # Entregas atrasadas
    entregas_atrasadas = Entrega.objects.filter(
        status__in=['planejada', 'preparacao', 'transporte'],
        data_entrega_prevista__lt=timezone.now().date()
    ).order_by('data_entrega_prevista')[:5]

    context = {
        'total_entregas': total_entregas,
        'entregas_hoje': entregas_hoje,
        'entregas_semana': entregas_semana,
        'entregas_por_status': entregas_por_status,
        'proximas_entregas': proximas_entregas,
        'entregas_atrasadas': entregas_atrasadas,
    }
    return render(request, 'entrega/dashboard_entregas.html', context)