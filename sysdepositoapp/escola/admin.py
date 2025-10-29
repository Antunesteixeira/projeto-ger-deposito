from django.contrib import admin
from .models import Escola  # Certifique-se que este import está correto

@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo_escola', 'cidade', 'quantidade_alunos', 'ativo']
    list_filter = ['tipo_escola', 'cidade', 'ativo']
    search_fields = ['nome', 'codigo_inep', 'cidade']