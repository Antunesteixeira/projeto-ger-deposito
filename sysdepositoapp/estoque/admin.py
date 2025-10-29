from django.contrib import admin
from .models import MovimentacaoEstoque, AjusteEstoque

@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo', 'quantidade', 'motivo', 'usuario', 'data_movimentacao']
    list_filter = ['tipo', 'motivo', 'data_movimentacao']
    search_fields = ['produto__nome', 'observacao']
    readonly_fields = ['usuario', 'data_movimentacao']

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)

@admin.register(AjusteEstoque)
class AjusteEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'estoque_anterior', 'estoque_novo', 'diferenca', 'usuario', 'data_ajuste']
    list_filter = ['data_ajuste']
    search_fields = ['produto__nome', 'motivo']
    readonly_fields = ['usuario', 'data_ajuste', 'estoque_anterior']

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)