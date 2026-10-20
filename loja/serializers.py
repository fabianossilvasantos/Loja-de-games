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


class ItemPedidoEntradaSerializer(serializers.Serializer):
    # ESCRITA dos itens: o cliente manda so o jogo (id) e a quantidade.
    # O preco NAO vem daqui - quem define e o servidor, no create() abaixo.
    jogo = serializers.PrimaryKeyRelatedField(queryset=Jogo.objects.all())
    quantidade = serializers.IntegerField(min_value=1)
    
    def validate_jogo(self, jogo):
        if not jogo.ativo:
            raise serializers.ValidationError(
                f"O jogo '{jogo}' nao esta a venda (inativo)."
            )
        return jogo


class PedidoSerializer(serializers.ModelSerializer):
    # o aninhado do requisito 7: os itens vem dentro do pedido.
    # "itens" e o related_name declarado no ItemPedido.pedido
    itens = ItemPedidoSerializer(many=True, read_only=True)
    cliente = serializers.StringRelatedField(read_only=True)
    # campo de escrita (write_only): aparece no POST, some na leitura
    itens_entrada = ItemPedidoEntradaSerializer(many=True, write_only=True, required=False)

    def validate(self, dados):
        # Recusa o pagamento se faltar estoque (corrige o oversell).
        # So checa quando esta VIRANDO pago (nao era pago, e vai ser).
        novo = dados.get("status")
        if (self.instance and novo == Pedido.Status.PAGO
                and self.instance.status != Pedido.Status.PAGO):
            faltando = self.instance.itens_sem_estoque()
            if faltando:
                nomes = ", ".join(
                    f"{i.jogo} (tem {i.jogo.estoque}, pediu {i.quantidade})" for i in faltando
                )
                raise serializers.ValidationError(f"Estoque insuficiente: {nomes}.")
        return dados

    def create(self, validated_data):
        # cliente e status ja vieram da view (perform_create).
        # Aqui a gente separa os itens e cria cada ItemPedido.
        itens = validated_data.pop("itens_entrada", [])
        pedido = Pedido.objects.create(**validated_data)
        for item in itens:
            jogo = item["jogo"]
            ItemPedido.objects.create(
                pedido=pedido,
                jogo=jogo,
                quantidade=item["quantidade"],
                preco_praticado=jogo.preco,  # <- servidor congela o preco do momento
            )
        return pedido

    class Meta:
        model = Pedido
        fields = ("id", "cliente", "status", "criado_em", "itens", "itens_entrada") #itens vai vir junto com o pedido, la no json, nao vai ficar separado
