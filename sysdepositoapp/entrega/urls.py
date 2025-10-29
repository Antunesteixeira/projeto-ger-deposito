from django.urls import path
from . import views

app_name = 'entrega'

urlpatterns = [
    path('', views.dashboard_entregas, name='dashboard_entregas'),
    path('entregas/', views.lista_entregas, name='lista_entregas'),
    path('entregas/nova/', views.nova_entrega, name='nova_entrega'),
    path('entregas/<int:pk>/', views.detalhe_entrega, name='detalhe_entrega'),
    path('entregas/<int:pk>/editar/', views.editar_entrega, name='editar_entrega'),
    path('entregas/<int:pk>/finalizar/', views.finalizar_entrega, name='finalizar_entrega'),
    path('escolas/', views.lista_escolas, name='lista_escolas'),
    path('escolas/nova/', views.nova_escola, name='nova_escola'),
    path('entregas/entregas/<int:entrega_id>/pdf/', views.gerar_pdf_entrega, name='gerar_pdf_entrega'),
]