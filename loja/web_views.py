"""Interface grafica da loja (Caminho A: o Django monta o HTML no servidor).

Estas views NAO sao a API. A API (loja/views.py) devolve JSON para um programa
consumir; estas devolvem HTML pronto para um humano ver na tela. As duas falam
com os MESMOS models - muda so o formato de saida: Serializer -> JSON la,
template -> HTML aqui.

Autenticacao tambem muda: a API usa token JWT, estas paginas usam o login de
SESSAO padrao do Django (cookie). Por isso o @login_required, e nao uma
permission_classes do DRF.
"""
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Jogo, Pedido


# Transicoes de status permitidas pela interface, a partir de cada status atual.
# Seguem o ciclo de vida natural do pedido - e cada uma exercita o signal de um
# jeito diferente:
#   aguardando -> pago        o signal BAIXA o estoque
#   pago/enviado -> cancelado o signal DEVOLVE o estoque
#   aguardando -> cancelado   o signal NAO mexe (nunca chegou a baixar)
TRANSICOES = {
    Pedido.Status.AGUARDANDO: [Pedido.Status.PAGO, Pedido.Status.CANCELADO],
    Pedido.Status.PAGO: [Pedido.Status.ENVIADO, Pedido.Status.CANCELADO],
    Pedido.Status.ENVIADO: [Pedido.Status.CANCELADO],
    Pedido.Status.CANCELADO: [],
}


def jogo_list(request):
    # select_related (FK) + prefetch_related (M2M) trazem desenvolvedora e
    # generos na mesma ida ao banco. Sem isso, o template dispararia uma
    # consulta por jogo ao pedir jogo.desenvolvedora.nome (problema N+1).
    jogos = (
        Jogo.objects
        .select_related("desenvolvedora")
        .prefetch_related("generos")
        .order_by("titulo")
    )
    return render(request, "loja/jogo_list.html", {"jogos": jogos})


def jogo_detail(request, pk):
    jogo = get_object_or_404(
        Jogo.objects.select_related("desenvolvedora").prefetch_related("generos"),
        pk=pk,
    )
    return render(request, "loja/jogo_detail.html", {"jogo": jogo})


@login_required  # pagina protegida: pedido e dado do cliente, exige estar logado
def pedido_list(request):
    pedidos = (
        Pedido.objects
        .select_related("cliente")
        .prefetch_related("itens__jogo")
        .order_by("-criado_em")
    )
    return render(request, "loja/pedido_list.html", {"pedidos": pedidos})


@login_required
def pedido_detail(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related("cliente").prefetch_related("itens__jogo"),
        pk=pk,
    )
    # O subtotal de cada item e o total do pedido sao calculados aqui, na view.
    # O preco_praticado ja esta congelado em cada item (nao muda se o jogo
    # mudar de preco depois), entao e so multiplicar. Faco em Python para nao
    # precisar mexer no model so por causa da tela.
    itens = list(pedido.itens.all())
    for item in itens:
        item.subtotal = item.quantidade * item.preco_praticado
    total = sum((item.subtotal for item in itens), Decimal("0.00"))

    # Botoes de status que a tela vai oferecer, ja com o rotulo legivel.
    proximos = TRANSICOES.get(pedido.status, [])
    transicoes = [(s, Pedido.Status(s).label) for s in proximos]

    return render(
        request,
        "loja/pedido_detail.html",
        {"pedido": pedido, "itens": itens, "total": total, "transicoes": transicoes},
    )


@login_required
def pedido_mudar_status(request, pk):
    """Muda o status do pedido e deixa o signal cuidar do estoque.

    So aceita POST e so permite as transicoes de TRANSICOES - assim a interface
    nao cria estados estranhos (ex.: voltar de pago para aguardando, que
    deixaria o estoque baixado sem o pedido estar pago).
    """
    pedido = get_object_or_404(Pedido, pk=pk)
    novo = request.POST.get("status")
    permitidos = TRANSICOES.get(pedido.status, [])

    if request.method == "POST" and novo in permitidos:
        # Mercado: nao deixa pagar sem estoque (mesma regra da API).
        faltando = pedido.itens_sem_estoque() if novo == Pedido.Status.PAGO else []
        if faltando:
            nomes = ", ".join(
                f"{i.jogo} (tem {i.jogo.estoque}, pediu {i.quantidade})" for i in faltando
            )
            messages.error(request, f"Não dá para pagar: estoque insuficiente — {nomes}.")
            return redirect("web:pedido_detail", pk=pedido.pk)

        anterior = pedido.status
        pedido.status = novo
        pedido.save()  # <-- aqui o signal dispara: baixa ou devolve o estoque

        # A mensagem so narra, para a tela, o que o signal acabou de fazer.
        if novo == Pedido.Status.PAGO:
            efeito = "o signal baixou o estoque"
        elif novo == Pedido.Status.CANCELADO and anterior in (
            Pedido.Status.PAGO,
            Pedido.Status.ENVIADO,
        ):
            efeito = "o signal devolveu o estoque"
        else:
            efeito = "o estoque nao mudou"
        messages.success(
            request,
            f"Pedido #{pedido.id}: status alterado para "
            f"{pedido.get_status_display()} — {efeito}.",
        )

    return redirect("web:pedido_detail", pk=pedido.pk)
