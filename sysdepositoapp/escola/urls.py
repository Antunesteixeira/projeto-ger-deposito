from django.urls import path
from . import views

app_name = 'escola'

urlpatterns = [
    path('', views.dashboard_escolas, name='dashboard_escolas'),  # Dashboard como página inicial
    path('lista/', views.lista_escolas, name='lista_escolas'),
    path('nova/', views.nova_escola, name='nova_escola'),
    path('<int:pk>/', views.detalhe_escola, name='detalhe_escola'),
    path('<int:pk>/editar/', views.editar_escola, name='editar_escola'),
    path('<int:pk>/toggle-ativa/', views.toggle_ativa_escola, name='toggle_ativa_escola'),
    path('exportar-csv/', views.exportar_escolas_csv, name='exportar_escolas_csv'),
]