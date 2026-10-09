from django.test import TestCase

# Create your tests here.

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Desenvolvedora, ItemPedido, Jogo, Pedido


class SignalEstoqueTest(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("teste", password="x")
        dev = Desenvolvedora.objects.create(
            nome="Estudio Teste", pais="BR", ano_fundacao=2000
        )
        self.jogo = Jogo.objects.create(
            titulo="Jogo de Teste",
            preco=Decimal("100.00"),
            estoque=10,
            desenvolvedora=dev,
        )
        self.pedido = Pedido.objects.create(
            cliente=self.usuario, status=Pedido.Status.AGUARDANDO
        )
        ItemPedido.objects.create(
            pedido=self.pedido, jogo=self.jogo, quantidade=3,
            preco_praticado=self.jogo.preco,
        )

    def test_baixa_estoque_ao_confirmar(self):
        self.pedido.status = Pedido.Status.PAGO
        self.pedido.save()
        self.jogo.refresh_from_db()
        self.assertEqual(self.jogo.estoque, 7)

    def test_nao_baixa_duas_vezes(self):
        self.pedido.status = Pedido.Status.PAGO
        self.pedido.save()
        self.pedido.save()
        self.jogo.refresh_from_db()
        self.assertEqual(self.jogo.estoque, 7)

    def test_nao_baixa_enquanto_aguardando(self):
        self.pedido.save()
        self.jogo.refresh_from_db()
        self.assertEqual(self.jogo.estoque, 10)


class ManagerDisponiveisTest(TestCase):
    def setUp(self):
        dev = Desenvolvedora.objects.create(
            nome="Estudio Teste", pais="BR", ano_fundacao=2000
        )
        comum = dict(preco=Decimal("100.00"), desenvolvedora=dev)
        Jogo.objects.create(titulo="A venda", estoque=5, **comum)
        Jogo.objects.create(titulo="Sem estoque", estoque=0, **comum)
        Jogo.objects.create(
            titulo="Excluido", estoque=5, is_excluido=True, **comum
        )

    def test_disponiveis_filtra_os_dois_motivos(self):
        self.assertEqual(Jogo.objects.count(), 3)
        self.assertEqual(Jogo.objects.disponiveis().count(), 1)

