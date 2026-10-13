from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Pedido


@receiver(pre_save, sender=Pedido) #definir o sinal que será disparado antes de salvar um pedido
def guardar_status_anterior(sender, instance, **kwargs):
    # Por que este signal existe: o post_save entrega o pedido ja gravado,
    # entao so enxerga o estado FINAL. Sem saber qual era o status antes,
    # nao da para distinguir "virou pago agora" de "ja estava pago e foi
    # salvo de novo" - e o estoque baixaria a cada salvamento.
    #
    # O pre_save roda ANTES da gravacao, quando o banco ainda tem o valor
    # antigo. E a unica janela para descobrir o que mudou.
    if instance.pk:
        # pk existe = o pedido ja esta no banco, ha um passado para consultar
        anterior = Pedido.objects.get(pk=instance.pk)
        # atributo temporario, so na memoria: nao e campo, nao vai para o banco.
        # serve para levar a informacao daqui ate o post_save.
        instance._status_anterior = anterior.status
    else:
        # pedido nascendo agora: nao existe "antes"
        instance._status_anterior = None


@receiver(post_save, sender=Pedido)   #definir o sinal que será disparado depois de salvar um pedido
def baixar_estoque(sender, instance, **kwargs): #diminuir o estoque dos jogos quando o pedido for pago
    # A baixa acontece no PAGAMENTO, nao na criacao do item: enquanto o
    # pedido esta "aguardando", o produto ainda pertence a loja.
    # O enunciado pede "ao confirmar um pedido".
    virou_pago = (
        instance.status == Pedido.Status.PAGO
        and instance._status_anterior != Pedido.Status.PAGO
    )

    # as duas condicoes juntas detectam a TRANSICAO. So "e pago" dispararia
    # em qualquer salvamento do pedido, descontando o estoque repetidamente.
    if not virou_pago:
        return

    for item in instance.itens.select_related("jogo"):
        jogo = item.jogo
        # max(..., 0) impede negativo, que o PositiveIntegerField recusaria.
        # E paliativo: o certo seria recusar a venda acima do estoque.
        jogo.estoque = max(jogo.estoque - item.quantidade, 0)
        jogo.save()


@receiver(post_save, sender=Pedido)
def devolver_estoque(sender, instance, **kwargs): #devolver ao estoque quando o pedido for cancelado
    # Operacao inversa do baixar_estoque. Sem ela, cancelar um pedido pago
    # deixava as unidades presas: a loja passava a achar que tinha menos
    # mercadoria do que realmente tinha na prateleira.
    #
    # O conjunto lista os status em que o estoque JA tinha sido baixado.
    # Cancelar um pedido "aguardando" nao devolve nada - nele o estoque
    # nunca desceu, e devolver criaria unidades do nada.
    # ENVIADO entra porque so se chega nele passando por PAGO.
    virou_cancelado = (
        instance.status == Pedido.Status.CANCELADO
        and instance._status_anterior in {Pedido.Status.PAGO, Pedido.Status.ENVIADO}
    )

    if not virou_cancelado:
        return

    for item in instance.itens.select_related("jogo"):
        jogo = item.jogo
        # sem max() aqui: somar dois positivos nunca da negativo
        jogo.estoque = jogo.estoque + item.quantidade
        jogo.save()
