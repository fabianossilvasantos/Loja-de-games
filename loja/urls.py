from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import JogoViewSet, PedidoViewSet

router = DefaultRouter()
router.register(r'jogos', JogoViewSet) #registra a viewset
router.register(r'pedidos', PedidoViewSet) #registra a viewset

urlpatterns = [
    path('', include(router.urls)), #diz que tudo que começar com /api/ vai ser interpretado pelo router.
]