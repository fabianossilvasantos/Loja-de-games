from rest_framework import serializers

from .models import (
    Desenvolvedora,
    Genero,
    ItemPedido,
    Jogo,
    Pedido,
)


class GeneroSerializer(serializers.ModelSerializer): #faz o mesmo que a classe de cima so que pra Genero
    class Meta:
        model = Genero
        fields = ("id", "nome")


class DesenvolvedoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Desenvolvedora
        fields = ("id", "nome", "pais", "ano_fundacao")


class JogoSerializer(serializers.ModelSerializer): # aqui diz pra ele usar tudo que ta em jogo
    # LEITURA: objetos aninhados, para o JSON sair legivel
    desenvolvedora = DesenvolvedoraSerializer(read_only=True)
    generos = GeneroSerializer(many=True, read_only=True)

    # ESCRITA: recebe ids e grava nos mesmos campos do model.
    # source= diz em qual atributo do model o valor vai parar.
    # write_only= mantem esses campos fora do JSON de leitura.
    desenvolvedora_id = serializers.PrimaryKeyRelatedField(
        queryset=Desenvolvedora.objects.all(),
        source="desenvolvedora",
        write_only=True,
    )
    generos_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genero.objects.all(),
        source="generos",
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:  # dentro de meta, voce define:
        model = Jogo
        fields = ("id", "titulo", "preco", "estoque", "ativo",
                  "desenvolvedora", "generos",
                  "desenvolvedora_id", "generos_ids")


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
        fields = ("id", "cliente", "status", "criado_em", "itens") #itens vai vir junto com o pedido, la no json, nao vai ficar separado
