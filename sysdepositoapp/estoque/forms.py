from django import forms
from .models import MovimentacaoEstoque, AjusteEstoque
from produto.models import Produto

class MovimentacaoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ['produto', 'tipo', 'quantidade', 'motivo', 'observacao', 'data_ocorrencia']
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 3}),
            'data_ocorrencia': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].queryset = Produto.objects.filter(ativo=True)

class AjusteEstoqueForm(forms.ModelForm):
    class Meta:
        model = AjusteEstoque
        fields = ['produto', 'estoque_novo', 'motivo']
        widgets = {
            'motivo': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].queryset = Produto.objects.filter(ativo=True)

class RelatorioEstoqueForm(forms.Form):
    TIPO_RELATORIO_CHOICES = [
        ('geral', 'Relatório Geral'),
        ('baixo_estoque', 'Produtos com Estoque Baixo'),
        ('esgotado', 'Produtos Esgotados'),
        ('movimentacoes', 'Movimentações por Período'),
    ]
    
    tipo_relatorio = forms.ChoiceField(choices=TIPO_RELATORIO_CHOICES, initial='geral')
    data_inicio = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    data_fim = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    categoria = forms.ModelChoiceField(
        queryset=Produto.objects.none(),
        required=False,
        empty_label='Todas as categorias'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from produto.models import Categoria
        self.fields['categoria'].queryset = Categoria.objects.all()