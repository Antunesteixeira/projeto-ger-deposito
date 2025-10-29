from django.db import models
from django.urls import reverse

class Escola(models.Model):
    TIPO_ESCOLA_CHOICES = [
        ('municipal', 'Municipal'),
        ('estadual', 'Estadual'),
        ('federal', 'Federal'),
        ('particular', 'Particular'),
    ]
    
    NIVEL_ESCOLA_CHOICES = [
        ('infantil', 'Educação Infantil'),
        ('fundamental', 'Ensino Fundamental'),
        ('medio', 'Ensino Médio'),
        ('tecnico', 'Ensino Técnico'),
        ('superior', 'Ensino Superior'),
    ]

    nome = models.CharField(max_length=200, verbose_name='Nome da Escola')
    codigo_inep = models.CharField(max_length=20, blank=True, null=True, verbose_name='Código INEP')
    tipo_escola = models.CharField(max_length=20, choices=TIPO_ESCOLA_CHOICES, default='municipal')
    nivel_ensino = models.CharField(max_length=20, choices=NIVEL_ESCOLA_CHOICES, default='fundamental')
    endereco = models.TextField(verbose_name='Endereço Completo')
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100, default='Magalhães de Almeida')
    estado = models.CharField(max_length=2, default='MA')
    cep = models.CharField(max_length=10, blank=True, null=True, default='65560-000')
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    diretor = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nome do Diretor')
    responsavel_contato = models.CharField(max_length=100, blank=True, null=True, verbose_name='Responsável para Contato')
    telefone_responsavel = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone do Responsável')
    quantidade_alunos = models.IntegerField(default=0, verbose_name='Quantidade de Alunos')
    observacoes = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Escola'
        verbose_name_plural = 'Escolas'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['cidade']),
            models.Index(fields=['ativo']),
        ]

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse('escola:detalhe_escola', kwargs={'pk': self.pk})

    @property
    def endereco_completo(self):
        return f"{self.endereco}, {self.bairro}, {self.cidade} - {self.estado}"

    @property
    def total_entregas(self):
        from entrega.models import Entrega
        return Entrega.objects.filter(escola=self).count()

    @property
    def entregas_pendentes(self):
        from entrega.models import Entrega
        return Entrega.objects.filter(escola=self, status__in=['planejada', 'preparacao']).count()

class ContatoEscola(models.Model):
    TIPO_CONTATO_CHOICES = [
        ('telefone', 'Telefone'),
        ('email', 'E-mail'),
        ('whatsapp', 'WhatsApp'),
        ('outro', 'Outro'),
    ]

    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='contatos')
    tipo = models.CharField(max_length=20, choices=TIPO_CONTATO_CHOICES)
    valor = models.CharField(max_length=100)
    observacao = models.CharField(max_length=100, blank=True, null=True)
    principal = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Contato da Escola'
        verbose_name_plural = 'Contatos das Escolas'
        ordering = ['-principal', 'tipo']

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.valor}"

class HistoricoEscola(models.Model):
    TIPO_EVENTO_CHOICES = [
        ('cadastro', 'Cadastro'),
        ('atualizacao', 'Atualização'),
        ('visita', 'Visita'),
        ('entrega', 'Entrega'),
        ('observacao', 'Observação'),
        ('outro', 'Outro'),
    ]

    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='historico')
    tipo_evento = models.CharField(max_length=20, choices=TIPO_EVENTO_CHOICES)
    descricao = models.TextField()
    data_evento = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Histórico da Escola'
        verbose_name_plural = 'Históricos das Escolas'
        ordering = ['-data_evento']

    def __str__(self):
        return f"{self.escola.nome} - {self.get_tipo_evento_display()} - {self.data_evento.date()}"