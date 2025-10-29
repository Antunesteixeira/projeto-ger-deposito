from django import forms
from .models import Produto, Categoria

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'nome', 'descricao', 'categoria', 'codigo_barras', 'sku',
            'preco_custo', 'preco_venda', 'unidade_medida',
            'estoque_minimo', 'estoque_atual', 'localizacao', 'ativo'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'preco_custo': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'form-control',
                'readonly': 'readonly',
                'style': 'background-color: #f8f9fa; cursor: not-allowed;'
            }),
            'preco_venda': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'form-control',
                'readonly': 'readonly',
                'style': 'background-color: #f8f9fa; cursor: not-allowed;'
            }),
            'sku': forms.TextInput(attrs={'placeholder': 'SKU único do produto. Ex: NOME-CATEGORIA-MARCA-1234'}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }
        


class ProdutoSearchForm(forms.Form):
    nome = forms.CharField(
        required=False,
        label='Nome ou SKU',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nome ou SKU...'
        })
    )
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        label='Categoria',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ativo = forms.BooleanField(
        required=False,
        label='Somente ativos',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )