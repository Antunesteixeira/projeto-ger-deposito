from django import forms
from .models import Entrega, ItemEntrega
from produto.models import Produto
from escola.models import Escola  # Importar do novo app

# REMOVER completamente a classe EscolaForm
# class EscolaForm(forms.ModelForm):
#     class Meta:
#         model = Escola
#         fields = ['nome', 'endereco', 'telefone', 'email', 'responsavel', 'ativo']
#         widgets = {
#             'endereco': forms.Textarea(attrs={'rows': 3}),
#         }

class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = [
            'escola', 'tipo_entrega', 'data_entrega_prevista',
            'responsavel_entrega', 'motorista', 'veiculo', 'observacoes'
        ]
        widgets = {
            'data_entrega_prevista': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['escola'].queryset = Escola.objects.filter(ativo=True)

class ItemEntregaForm(forms.ModelForm):
    class Meta:
        model = ItemEntrega
        fields = ['produto', 'quantidade', 'observacao']
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].queryset = Produto.objects.filter(ativo=True)

class ItemEntregaFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                produto = form.cleaned_data.get('produto')
                quantidade = form.cleaned_data.get('quantidade')
                
                if produto and quantidade:
                    if quantidade <= 0:
                        raise forms.ValidationError(f"A quantidade para {produto.nome} deve ser maior que zero.")
                    
                    # Verificar estoque disponível
                    if not self.instance.pk or (self.instance and self.instance.status == 'planejada'):
                        if produto.estoque_atual < quantidade:
                            raise forms.ValidationError(
                                f"Estoque insuficiente para {produto.nome}. "
                                f"Disponível: {produto.estoque_atual}, Solicitado: {quantidade}"
                            )

class FiltroEntregaForm(forms.Form):
    STATUS_CHOICES = [('', 'Todos os status')] + Entrega.STATUS_CHOICES
    TIPO_CHOICES = [('', 'Todos os tipos')] + Entrega.TIPO_ENTREGA_CHOICES
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    tipo_entrega = forms.ChoiceField(choices=TIPO_CHOICES, required=False)
    escola = forms.ModelChoiceField(queryset=Escola.objects.filter(ativo=True), required=False, empty_label='Todas as escolas')
    data_inicio = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    data_fim = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))