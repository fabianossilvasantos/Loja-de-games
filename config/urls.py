"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path          # ← include entra aqui
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [ #configura a url raiz do projeto, aqui que o django começa a procurar as urls.
    path('admin/', admin.site.urls), # url padrão do admin do django.
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"), #url para obter o token.
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"), #url para atualizar o token.
    path("api/", include("loja.urls")), #aqui vai chamar tudo que estiver dentro do arquivo urls.py do app loja.
    path("loja/", include("loja.web_urls")), #interface grafica (HTML) - separada da API.
]
