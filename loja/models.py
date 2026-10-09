from django.conf import settings
from django.db import models


class Genero(models.Model):
    # unique=True: evita "RPG" cadastrado duas vezes,
    # o que quebraria a consulta "jogos de RPG"
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome


class Desenvolvedora(models.Model):
    nome = models.CharField(max_length=100)
    pais = models.CharField(max_length=50)
    ano_fundacao = models.PositiveIntegerField()

    def __str__(self):
        return self.nome

class JogoManager(models.Manager): #gerenciador de objetos do modelo do jogo
    
    def disponiveis(self):
        return self.filter(estoque__gt=0, is_excluido=False) #retorna apenas os jogos que estão disponíveis (estoque maior que 0 e não excluídos)

class Jogo(models.Model):
    titulo = models.CharField(max_length=200)

    # DecimalField e nao FloatField: float tem erro de
    # arredondamento, inaceitavel em dinheiro
    preco = models.DecimalField(max_digits=8, decimal_places=2)

    estoque = models.PositiveIntegerField(default=0)

    # soft delete: o jogo some da vitrine mas continua no banco,
    # senao os pedidos antigos que o contem ficam quebrados
    is_excluido = models.BooleanField(default=False)

    # PROTECT: apagar a desenvolvedora e recusado enquanto ela
    # tiver jogos. Jogo e mercadoria, nao pode sumir por acidente.
    # related_name="jogos": permite desenvolvedora.jogos.all()
    desenvolvedora = models.ForeignKey(
        Desenvolvedora,
        on_delete=models.PROTECT,
        related_name="jogos",
    )

    # M2M: um jogo tem varios generos e um genero tem varios jogos.
    # O Django cria a tabela loja_jogo_generos sozinho.
    generos = models.ManyToManyField(Genero, related_name="jogos")

    objects = JogoManager() #associa o gerenciador de objetos ao modelo do jogo
    def __str__(self):
        return self.titulo #retorna o titulo do jogo como representação do objeto


class PerfilCliente(models.Model):  # classe para armazenar informações adicionais do cliente
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


class Pedido(models.Model):
    class Status(models.TextChoices):
        AGUARDANDO = "aguardando", "Aguardando"
        PAGO = "pago", "Pago"
        ENVIADO = "enviado", "Enviado"
        CANCELADO = "cancelado", "Cancelado"

    # PROTECT: pedido e registro contabil, pode ser cancelado
    # mas nao apagado. Se o cliente for apagado, o pedido continua.
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.AGUARDANDO,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.username} - {self.status}"


class ItemPedido(models.Model):
    # CASCADE: item nao existe sem o pedido
    # related_name="itens": permite pedido.itens.all()
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="itens",
    )

    # PROTECT: nao se apaga um jogo que ja foi vendido
    jogo = models.ForeignKey(
        Jogo,
        on_delete=models.PROTECT,
        related_name="itens_pedido",
    )

    # quantidade de unidades do jogo neste item do pedido
    
    quantidade = models.PositiveIntegerField(default=1)

    # preco congelado no momento da compra: o jogo pode mudar
    # de preco depois, este valor nunca muda
    preco_praticado = models.DecimalField(max_digits=8, decimal_places=2)

    
    
    def __str__(self):
        return f"{self.quantidade}x {self.jogo.titulo}"
