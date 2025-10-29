from django.db import models
from django.contrib.auth.models import User
from produto.models import Produto

class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = [
        ('E', 'Entrada'),
        ('S', 'Saída'),
    ]
    
    MOTIVO_CHOICES = [
        ('compra', 'Compra'),
        ('venda', 'Venda'),
        ('ajuste', 'Ajuste de Estoque'),
        ('devolucao', 'Devolução'),
        ('perda', 'Perda/Danificado'),
        ('producao', 'Produção'),
        ('outro', 'Outro'),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES, default='ajuste')
    observacao = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_movimentacao = models.DateTimeField(auto_now_add=True)
    data_ocorrencia = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Movimentação de Estoque'
        verbose_name_plural = 'Movimentações de Estoque'
        ordering = ['-data_movimentacao']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.produto.nome} - {self.quantidade}"

    def save(self, *args, **kwargs):
        # Atualizar o estoque do produto
        if self.tipo == 'E':
            self.produto.estoque_atual += self.quantidade
        elif self.tipo == 'S':
            self.produto.estoque_atual -= self.quantidade
        
        self.produto.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Reverter o estoque ao excluir a movimentação
        if self.tipo == 'E':
            self.produto.estoque_atual -= self.quantidade
        elif self.tipo == 'S':
            self.produto.estoque_atual += self.quantidade
        
        self.produto.save()
        super().delete(*args, **kwargs)

class AjusteEstoque(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    estoque_anterior = models.IntegerField()
    estoque_novo = models.IntegerField()
    motivo = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_ajuste = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ajuste de Estoque'
        verbose_name_plural = 'Ajustes de Estoque'
        ordering = ['-data_ajuste']

    def __str__(self):
        return f"Ajuste - {self.produto.nome}"

    @property
    def diferenca(self):
        return self.estoque_novo - self.estoque_anterior