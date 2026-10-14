from rest_framework import serializers

from .models import (

    Desenvolvedora,
    Genero,
    ItemPedido,
    Jogo,
    Pedido,
)

class GeneroSerializer(serializers.ModelSerializer): #faz o mesmo que a classe de cima so que praGenero
    class Meta:
        model = Genero
        fields = ("id", "nome")

class DesenvolvedoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Desenvolvedora
        fields = ("id", "nome", "pais", "ano_fundacao")


class JogoSerializer(serializers.ModelSerializer): # aqui diz pra ele usar tudo que ta em jogo 
    # aninhados: em vez de devolver os ids, devolve os objetos inteiros
    desenvolvedora = DesenvolvedoraSerializer(read_only=True)
    generos = GeneroSerializer(many=True, read_only=True)

    class Meta:  # dentro de meta, você define:
        model = Jogo
        fields = ("id", "titulo", "preco", "estoque", "ativo", "desenvolvedora", "generos") # para que os campos sejam lidos e escritos, remova read_only=True


class ItemPedidoSerializer(serializers.ModelSerializer):
    # mostra o titulo em vez do id do jogo
    jogo = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ItemPedido
        fields = ("id", "jogo", "quantidade", "preco_praticado")


class PedidoSerializer(serializers.ModelSerializer):
    # o aninhado do requisito 7: os itens vem dentro do pedido.
    # "itens" e o related_name declarado no ItemPedido.pedido
    itens = ItemPedidoSerializer(many=True, read_only=True)
    cliente = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Pedido
        fields = ("id", "cliente", "status", "criado_em", "itens") #itens vai vir junto com o pedido, la no json, não vai ficar separado