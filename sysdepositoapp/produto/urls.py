from django.urls import path
from . import views

app_name = 'produto'

urlpatterns = [
    # Produtos
    path('', views.lista_produtos, name='lista_produtos'),
    path('produtos/', views.lista_produtos, name='lista_produtos'),
    path('produtos/novo/', views.produto_novo, name='produto_novo'),
    path('produtos/<int:pk>/', views.produto_detalhe, name='produto_detalhe'),
    path('produtos/<int:pk>/editar/', views.produto_editar, name='produto_editar'),
    path('produtos/<int:pk>/excluir/', views.produto_excluir, name='produto_excluir'),
    
    # Categorias
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/nova/', views.categoria_nova, name='categoria_nova'),
    path('categorias/<int:pk>/editar/', views.categoria_editar, name='categoria_editar'),
    path('categorias/<int:pk>/excluir/', views.categoria_excluir, name='categoria_excluir'),

    path('api/buscar_produtos/', views.buscar_produtos, name='buscar_produtos_api'),
]