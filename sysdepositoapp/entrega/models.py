from django.db import models
from django.contrib.auth.models import User
from produto.models import Produto
from escola.models import Escola

class Entrega(models.Model):
    STATUS_CHOICES = [
        ('planejada', 'Planejada'),
        ('preparacao', 'Em Preparação'),
        ('transporte', 'Em Transporte'),
        ('entregue', 'Entregue'),
        ('cancelada', 'Cancelada'),
    ]

    TIPO_ENTREGA_CHOICES = [
        ('normal', 'Entrega Normal'),
        ('urgente', 'Entrega Urgente'),
        ('agendada', 'Entrega Agendada'),
    ]

    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='entregas')
    numero_pedido = models.CharField(max_length=50, unique=True, verbose_name='Número do Pedido')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planejada')
    tipo_entrega = models.CharField(max_length=20, choices=TIPO_ENTREGA_CHOICES, default='normal')
    data_entrega_prevista = models.DateField()
    data_entrega_real = models.DateField(blank=True, null=True)
    responsavel_entrega = models.CharField(max_length=100)
    motorista = models.CharField(max_length=100, blank=True, null=True)
    veiculo = models.CharField(max_length=50, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Entrega'
        verbose_name_plural = 'Entregas'
        ordering = ['-data_criacao']

    def save(self, *args, **kwargs):
        """
        Gera `numero_pedido` automaticamente no formato AAAAMMDDSSSS (ano+mes+dia+sequencial)
        O sequencial reinicia a cada dia. Para evitar colisões em concorrência, tentamos
        inserir dentro de uma transação e, em caso de IntegrityError (único), incrementamos
        o sequencial e re-tentamos algumas vezes.
        """
        if not self.numero_pedido:
            from django.utils import timezone
            from django.db import transaction, IntegrityError

            now = timezone.now()
            ano = now.year
            mes = now.month
            dia = now.day

            date_filter = {
                'data_criacao__year': ano,
                'data_criacao__month': mes,
                'data_criacao__day': dia,
            }

            # Tentativas para lidar com colisões concorrentes
            max_attempts = 10
            sequencial = 1

            for attempt in range(max_attempts):
                try:
                    with transaction.atomic():
                        # Bloqueia os registros do dia para reduzir condições de corrida
                        ultimo_pedido = type(self).objects.select_for_update().filter(**date_filter).order_by('-numero_pedido').first()

                        if ultimo_pedido:
                            try:
                                ultimo_seq = int(ultimo_pedido.numero_pedido[-4:])
                                sequencial = ultimo_seq + 1
                            except Exception:
                                # fallback: contar pedidos do dia
                                sequencial = type(self).objects.filter(**date_filter).count() + 1
                        else:
                            sequencial = 1

                        seq_str = str(sequencial).zfill(4)
                        candidate = f"{ano}{mes:02d}{dia:02d}{seq_str}"
                        self.numero_pedido = candidate

                        # Tenta salvar; se houver colisão de unique, IntegrityError será lançado
                        super().save(*args, **kwargs)

                        # Salvou com sucesso
                        return
                except IntegrityError:
                    # Colisão: incrementa e tenta novamente
                    sequencial += 1
                    continue

            # Se esgotarmos as tentativas, falha explícita para investigação
            raise IntegrityError('Não foi possível gerar um número de pedido único após várias tentativas.')

        # Se já possui número (edição), salva normalmente
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Entrega {self.numero_pedido} - {self.escola.nome}"

    @property
    def total_itens(self):
        return self.itens.aggregate(total=models.Sum('quantidade'))['total'] or 0

    @property
    def total_produtos(self):
        return self.itens.count()

    @property
    def atrasada(self):
        from django.utils import timezone
        if self.status not in ['entregue', 'cancelada'] and self.data_entrega_prevista < timezone.now().date():
            return True
        return False

    def finalizar_entrega(self):
        """Finaliza a entrega e atualiza o estoque"""
        if self.status != 'entregue':
            self.status = 'entregue'
            self.data_entrega_real = timezone.now().date()
            self.save()
            
            # Atualizar estoque para cada item
            for item in self.itens.all():
                MovimentacaoEstoque = apps.get_model('estoque', 'MovimentacaoEstoque')
                MovimentacaoEstoque.objects.create(
                    produto=item.produto,
                    tipo='S',  # Saída
                    quantidade=item.quantidade,
                    motivo='entrega',
                    observacao=f'Entrega {self.numero_pedido} - {self.escola.nome}',
                    usuario=self.usuario
                )

class ItemEntrega(models.Model):
    entrega = models.ForeignKey(Entrega, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    quantidade_entregue = models.IntegerField(default=0)
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Item de Entrega'
        verbose_name_plural = 'Itens de Entrega'
        unique_together = ['entrega', 'produto']

    def __str__(self):
        return f"{self.produto.nome} - {self.quantidade}"

    @property
    def subtotal(self):
        return self.produto.preco_venda * self.quantidade

    @property
    def entregue_completamente(self):
        return self.quantidade_entregue >= self.quantidade

class HistoricoStatus(models.Model):
    entrega = models.ForeignKey(Entrega, on_delete=models.CASCADE, related_name='historico_status')
    status_anterior = models.CharField(max_length=20)
    status_novo = models.CharField(max_length=20)
    observacao = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_mudanca = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Status'
        verbose_name_plural = 'Históricos de Status'
        ordering = ['-data_mudanca']

    def __str__(self):
        return f"{self.entrega.numero_pedido} - {self.status_anterior} → {self.status_novo}"