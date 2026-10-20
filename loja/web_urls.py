"""Rotas da interface grafica (HTML).

Ficam separadas das rotas da API (loja/urls.py, que e o router do DRF). No
config/urls.py, a API mora sob /api/ e esta interface sob /loja/.
"""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import web_views

# Namespace: permite escrever {% url 'web:jogo_list' %} nos templates sem
# colidir com os nomes de rota da API.
app_name = "web"

urlpatterns = [
    path("", web_views.jogo_list, name="jogo_list"),
    path("jogos/<int:pk>/", web_views.jogo_detail, name="jogo_detail"),
    path("pedidos/", web_views.pedido_list, name="pedido_list"),
    path("pedidos/<int:pk>/", web_views.pedido_detail, name="pedido_detail"),
    path(
        "pedidos/<int:pk>/mudar-status/",
        web_views.pedido_mudar_status,
        name="pedido_mudar_status",
    ),

    # Login/logout de SESSAO (nao JWT). O Django ja traz as views prontas;
    # so apontamos qual template o login deve usar. O logout, no Django 6, so
    # aceita POST - por isso no menu ele e um formulario, nao um link.
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="loja/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
