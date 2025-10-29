from django.contrib import admin
from .models import Categoria, Produto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'data_criacao']
    search_fields = ['nome']
    list_filter = ['data_criacao']

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 
        'sku', 
        'categoria', 
        'preco_custo', 
        'preco_venda', 
        'estoque_atual',
        'estoque_minimo',
        'status_estoque',
        'ativo'
    ]
    list_filter = ['categoria', 'ativo', 'unidade_medida', 'data_criacao']
    search_fields = ['nome', 'sku', 'codigo_barras']
    readonly_fields = ['data_criacao', 'data_atualizacao']
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['nome', 'descricao', 'categoria', 'ativo']
        }),
        ('Códigos', {
            'fields': ['sku', 'codigo_barras']
        }),
        ('Preços', {
            'fields': ['preco_custo', 'preco_venda']
        }),
        ('Estoque', {
            'fields': ['unidade_medida', 'estoque_minimo', 'estoque_atual', 'localizacao']
        }),
        ('Datas', {
            'fields': ['data_criacao', 'data_atualizacao'],
            'classes': ['collapse']
        }),
    ]

    def status_estoque(self, obj):
        status = obj.status_estoque
        if status == 'esgotado':
            return '🔴 Esgotado'
        elif status == 'baixo':
            return '🟡 Baixo'
        else:
            return '🟢 Normal'
    status_estoque.short_description = 'Status Estoque'