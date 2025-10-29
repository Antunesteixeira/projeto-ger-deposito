from django.contrib import admin
from .models import Entrega, ItemEntrega, HistoricoStatus

class ItemEntregaInline(admin.TabularInline):
    model = ItemEntrega
    extra = 1

class HistoricoStatusInline(admin.TabularInline):
    model = HistoricoStatus
    extra = 0
    readonly_fields = ['usuario', 'data_mudanca']
    can_delete = False

@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ['numero_pedido', 'escola', 'status', 'tipo_entrega', 'data_entrega_prevista', 'data_criacao']
    list_filter = ['status', 'tipo_entrega', 'data_entrega_prevista', 'data_criacao']
    search_fields = ['numero_pedido', 'escola__nome', 'responsavel_entrega']
    readonly_fields = ['data_criacao', 'data_atualizacao']
    inlines = [ItemEntregaInline, HistoricoStatusInline]
    
    # Campos a serem exibidos no formulário
    fieldsets = [
        ('Informações Básicas', {
            'fields': [
                'escola', 'numero_pedido', 'status', 'tipo_entrega'
            ]
        }),
        ('Datas', {
            'fields': [
                'data_entrega_prevista', 'data_entrega_real'
            ]
        }),
        ('Responsáveis', {
            'fields': [
                'responsavel_entrega', 'motorista', 'veiculo'
            ]
        }),
        ('Observações', {
            'fields': ['observacoes'],
            'classes': ['collapse']
        }),
        ('Informações do Sistema', {
            'fields': ['data_criacao', 'data_atualizacao'],
            'classes': ['collapse']
        }),
    ]

    def save_model(self, request, obj, form, change):
        # Definir o usuário automaticamente
        if not obj.usuario_id:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Remover o campo usuario do formulário, pois será definido automaticamente
        if 'usuario' in form.base_fields:
            del form.base_fields['usuario']
        return form

@admin.register(ItemEntrega)
class ItemEntregaAdmin(admin.ModelAdmin):
    list_display = ['entrega', 'produto', 'quantidade', 'quantidade_entregue']
    list_filter = ['entrega__status']
    search_fields = ['entrega__numero_pedido', 'produto__nome']

@admin.register(HistoricoStatus)
class HistoricoStatusAdmin(admin.ModelAdmin):
    list_display = ['entrega', 'status_anterior', 'status_novo', 'usuario', 'data_mudanca']
    list_filter = ['data_mudanca']
    search_fields = ['entrega__numero_pedido']
    readonly_fields = ['usuario', 'data_mudanca']

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)