from django.test import TestCase

# Create your tests here.

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient

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
            titulo="Inativo", estoque=5, ativo=False, **comum
        )

    def test_disponiveis_filtra_os_dois_motivos(self):
        self.assertEqual(Jogo.objects.count(), 3)
        self.assertEqual(Jogo.objects.disponiveis().count(), 1)


class PedidoMercadoAPITest(TestCase):
    """Regras de mercado na criacao e no pagamento de pedido pela API."""

    def setUp(self):
        self.user = get_user_model().objects.create_user("comprador", password="x")
        dev = Desenvolvedora.objects.create(nome="Dev", pais="BR", ano_fundacao=2000)
        self.jogo = Jogo.objects.create(
            titulo="A venda", preco=Decimal("100.00"), estoque=5, desenvolvedora=dev
        )
        self.inativo = Jogo.objects.create(
            titulo="Fora de venda", preco=Decimal("50.00"), estoque=5,
            ativo=False, desenvolvedora=dev,
        )
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def _cria(self, jogo, qtd, preco_falso=None):
        item = {"jogo": jogo.id, "quantidade": qtd}
        if preco_falso is not None:
            item["preco_praticado"] = preco_falso  # tenta furar o preco
        return self.api.post("/api/pedidos/", {"itens_entrada": [item]}, format="json")

    def test_dono_e_usuario_logado_e_nasce_aguardando(self):
        r = self._cria(self.jogo, 2)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["cliente"], "comprador")
        self.assertEqual(r.data["status"], "aguardando")

    def test_preco_vem_do_servidor(self):
        r = self._cria(self.jogo, 1, preco_falso="0.01")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["itens"][0]["preco_praticado"], "100.00")

    def test_recusa_jogo_inativo(self):
        self.assertEqual(self._cria(self.inativo, 1).status_code, 400)

    def test_recusa_pagar_sem_estoque(self):
        pedido_id = self._cria(self.jogo, 99).data["id"]
        r = self.api.patch(
            f"/api/pedidos/{pedido_id}/", {"status": "pago"}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.jogo.refresh_from_db()
        self.assertEqual(self.jogo.estoque, 5)  # intacto

    def test_pagar_com_estoque_baixa(self):
        pedido_id = self._cria(self.jogo, 2).data["id"]
        r = self.api.patch(
            f"/api/pedidos/{pedido_id}/", {"status": "pago"}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.jogo.refresh_from_db()
        self.assertEqual(self.jogo.estoque, 3)

