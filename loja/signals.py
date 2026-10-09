from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Pedido


@receiver(pre_save, sender=Pedido) #definir o sinal que será disparado antes de salvar um pedido
def guardar_status_anterior(sender, instance, **kwargs):  
    
    if instance.pk:
        
        anterior = Pedido.objects.get(pk=instance.pk)
        instance._status_anterior = anterior.status
    else:
        instance._status_anterior = None
        
@receiver(post_save, sender=Pedido)   #definir o sinal que será disparado depois de salvar um pedido
def baixar_estoque(sender, instance, **kwargs): #diminuir o estoque dos jogos quando o pedido for pago
    
    virou_pago = (
        instance.status == Pedido.Status.PAGO
        and instance._status_anterior != Pedido.Status.PAGO
    )
    
    if not virou_pago:
        return
    
    for item in instance.itens.select_related("jogo"):
        jogo = item.jogo
        jogo.estoque = max(jogo.estoque - item.quantidade, 0)
        jogo.save()