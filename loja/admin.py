from django.contrib import admin
from .models import Desenvolvedora, Genero, ItemPedido, Jogo, Pedido, PerfilCliente

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1



@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "desenvolvedora", "preco", "estoque", "is_excluido") #  classifica as colunas que aparecem na listagem de jogos no admin
    list_filter = ("desenvolvedora", "generos", "is_excluido")
    search_fields = ("titulo",)
    filter_horizontal = ("generos",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "status", "criado_em")
    list_filter = ("status",)
    inlines = [ItemPedidoInline]


admin.site.register(Genero)
admin.site.register(Desenvolvedora)
admin.site.register(PerfilCliente)