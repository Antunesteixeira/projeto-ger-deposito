from django.db import models
from django.urls import reverse

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    status_ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def produtos_ativos_count(self):
        return self.produto_set.filter(ativo=True).count()
    
    def produtos_count(self):
        return self.produto_set.count()

    def __str__(self):
        return self.nome

class Produto(models.Model):
    UNIDADE_CHOICES = [
        ('UN', 'Unidade'),
        ('PC', 'Peça'),
        ('KG', 'Quilograma'),
        ('MT', 'Metro'),
        ('LT', 'Litro'),
        ('CX', 'Caixa'),
        ('PCT', 'Pacote'),
    ]

    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    codigo_barras = models.CharField(max_length=100, unique=True, blank=True, null=True)
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unidade_medida = models.CharField(max_length=3, choices=UNIDADE_CHOICES, default='UN')
    estoque_minimo = models.IntegerField(default=0)
    estoque_atual = models.IntegerField(default=0)
    localizacao = models.CharField(max_length=100, blank=True, null=True, help_text='Localização no depósito')
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.sku})"

    def get_absolute_url(self):
        return reverse('produto_detalhe', kwargs={'pk': self.pk})

    @property
    def lucro(self):
        """Calcula o lucro por unidade"""
        return self.preco_venda - self.preco_custo

    @property
    def margem_lucro(self):
        """Calcula a margem de lucro em porcentagem"""
        if self.preco_custo > 0:
            return ((self.preco_venda - self.preco_custo) / self.preco_custo) * 100
        return 0

    @property
    def estoque_baixo(self):
        """Verifica se o estoque está abaixo do mínimo"""
        return self.estoque_atual <= self.estoque_minimo

    @property
    def status_estoque(self):
        """Retorna o status do estoque"""
        if self.estoque_atual == 0:
            return 'esgotado'
        elif self.estoque_baixo:
            return 'baixo'
        else:
            return 'normal'