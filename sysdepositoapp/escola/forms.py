from django import forms
from .models import Escola, ContatoEscola, HistoricoEscola

class EscolaForm(forms.ModelForm):
    class Meta:
        model = Escola
        fields = [
            'nome', 'codigo_inep', 'tipo_escola', 'nivel_ensino',
            'endereco', 'bairro', 'cidade', 'estado', 'cep',
            'telefone', 'email', 'diretor', 'responsavel_contato',
            'telefone_responsavel', 'quantidade_alunos', 'observacoes', 'ativo'
        ]
        widgets = {
            'endereco': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
            'cep': forms.TextInput(attrs={'placeholder': '00000-000'}),
        }
        labels = {
            'codigo_inep': 'Código INEP',
            'tipo_escola': 'Tipo de Escola',
            'nivel_ensino': 'Nível de Ensino',
        }

    def clean_codigo_inep(self):
        codigo_inep = self.cleaned_data.get('codigo_inep')
        if codigo_inep:
            # Validar formato do código INEP (apenas números, 8 dígitos)
            if not codigo_inep.isdigit():
                raise forms.ValidationError("O código INEP deve conter apenas números.")
            if len(codigo_inep) != 8:
                raise forms.ValidationError("O código INEP deve ter 8 dígitos.")
        return codigo_inep

    def clean_quantidade_alunos(self):
        quantidade = self.cleaned_data.get('quantidade_alunos')
        if quantidade < 0:
            raise forms.ValidationError("A quantidade de alunos não pode ser negativa.")
        return quantidade

class ContatoEscolaForm(forms.ModelForm):
    class Meta:
        model = ContatoEscola
        fields = ['tipo', 'valor', 'observacao', 'principal']
        widgets = {
            'observacao': forms.TextInput(attrs={'placeholder': 'Ex: Telefone da secretaria'}),
        }

class HistoricoEscolaForm(forms.ModelForm):
    class Meta:
        model = HistoricoEscola
        fields = ['tipo_evento', 'descricao', 'observacoes']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }

class EscolaSearchForm(forms.Form):
    nome = forms.CharField(required=False, label='Nome da Escola')
    cidade = forms.CharField(required=False, label='Cidade')
    tipo_escola = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + Escola.TIPO_ESCOLA_CHOICES,
        required=False,
        label='Tipo de Escola'
    )
    nivel_ensino = forms.ChoiceField(
        choices=[('', 'Todos os níveis')] + Escola.NIVEL_ESCOLA_CHOICES,
        required=False,
        label='Nível de Ensino'
    )
    ativo = forms.BooleanField(required=False, initial=True, label='Somente ativas')