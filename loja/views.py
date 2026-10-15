from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Jogo, Pedido
from .serializers import JogoSerializer, PedidoSerializer


class JogoViewSet(viewsets.ModelViewSet): # ModelViewSet é uma classe que já vem com todos os metodos de view que eu preciso, como listar, buscar, criar, atualizar e deletar. 
    # select_related/prefetch_related: traz desenvolvedora e generos
    # na mesma consulta. Sem isso, listar 10 jogos faria 21 idas ao banco.
    queryset = Jogo.objects.select_related("desenvolvedora").prefetch_related("generos") #essa parte aqui diz pra ele buscar os jogos, mas ja trazer junto com a desenvolvedora e os generos.
    serializer_class = JogoSerializer
    permission_classes = [IsAuthenticated] # só usuários logados veem jogos


    def perform_destroy(self, instance):
        # soft delete: o DELETE da API marca como inativo em vez de apagar.
        # Apagar de verdade quebraria os pedidos que referenciam este jogo,
        # e o PROTECT no ItemPedido.jogo impediria de qualquer forma.
        instance.ativo = False
        instance.save()

class PedidoViewSet(viewsets.ModelViewSet): # ModelViewSet é uma classe que já vem com todos os metodos de view que eu preciso, como listar, buscar, criar, atualizar e deletar. 
    queryset = Pedido.objects.select_related("cliente").prefetch_related("itens__jogo") #essa parte aqui diz pra ele buscar os pedidos, mas ja trazer junto com o cliente e os itens.
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated] # só usuários logados veem pedidos