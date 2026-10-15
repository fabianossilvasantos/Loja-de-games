from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Desenvolvedora, Jogo, Pedido
from .serializers import JogoSerializer, PedidoSerializer


class JogoViewSet(viewsets.ModelViewSet): # ModelViewSet é uma classe que já vem com todos os metodos de view que eu preciso, como listar, buscar, criar, atualizar e deletar.
    # select_related/prefetch_related: traz desenvolvedora e generos
    # na mesma consulta. Sem isso, listar 10 jogos faria 21 idas ao banco.
    queryset = Jogo.objects.select_related("desenvolvedora").prefetch_related("generos")
    serializer_class = JogoSerializer
    permission_classes = [IsAuthenticated] # só usuários logados veem jogos

    def perform_destroy(self, instance):
        # soft delete: o DELETE da API marca como inativo em vez de apagar.
        # Apagar de verdade quebraria os pedidos que referenciam este jogo,
        # e o PROTECT no ItemPedido.jogo impediria de qualquer forma.
        instance.ativo = False
        instance.save()

    @action(detail=False)
    def mais_vendidos(self, request):
        """Soma as quantidades vendidas de cada jogo, do maior para o menor."""
        # itens_pedido e o related_name declarado no ItemPedido.jogo.
        # Coalesce troca NULL por 0: Sum sobre zero linhas devolve NULL,
        # e jogo sem venda nenhuma apareceria como null no JSON.
        dados = (
            Jogo.objects
            .annotate(total_vendido=Coalesce(Sum("itens_pedido__quantidade"), 0))
            .order_by("-total_vendido")
            .values("id", "titulo", "total_vendido")
        )
        return Response(dados)

    @action(detail=False)
    def por_desenvolvedora(self, request):
        """Conta quantos jogos cada desenvolvedora tem no catalogo."""
        # jogos e o related_name declarado no Jogo.desenvolvedora
        dados = (
            Desenvolvedora.objects
            .annotate(total_jogos=Count("jogos"))
            .order_by("-total_jogos", "nome")
            .values("id", "nome", "total_jogos")
        )
        return Response(dados)


class PedidoViewSet(viewsets.ModelViewSet): # ModelViewSet é uma classe que já vem com todos os metodos de view que eu preciso, como listar, buscar, criar, atualizar e deletar.
    queryset = Pedido.objects.select_related("cliente").prefetch_related("itens__jogo")
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated] # só usuários logados veem pedidos
