from django.urls import path
from . import views

app_name = 'estoque'

urlpatterns = [
    path('', views.dashboard_estoque, name='dashboard_estoque'),
    path('lista/', views.lista_estoque, name='lista_estoque'),
    path('movimentacao/nova/', views.movimentacao_estoque, name='movimentacao_estoque'),
    path('ajuste/', views.ajuste_estoque, name='ajuste_estoque'),
    path('movimentacoes/', views.lista_movimentacoes, name='lista_movimentacoes'),
    path('relatorios/', views.relatorios_estoque, name='relatorios_estoque'),
    path('exportar-csv/', views.exportar_estoque_csv, name='exportar_estoque_csv'),
    path('movimentacao/<int:movimentacao_id>/pdf/', views.gerar_pdf_movimentacao, name='gerar_pdf_movimentacao'),
    # ... suas URLs existentes
    path('movimentacoes/exportar-pdf/', views.exportar_movimentacoes_pdf, name='exportar_movimentacoes_pdf'),
    path('movimentacao/<int:movimentacao_id>/pdf/', views.gerar_pdf_movimentacao, name='gerar_pdf_movimentacao'),
    #path('relatorios/estoque-pdf/', views.gerar_relatorio_estoque_pdf, name='gerar_relatorio_estoque_pdf'),
    #path('relatorios/estoque-csv/', views.gerar_relatorio_estoque_csv, name='gerar_relatorio_estoque_csv'),
]