"""Cria os 10 usuarios iniciais da loja: 2 administradores e 8 compradores.

Uso:
    python manage.py criar_usuarios
    python manage.py criar_usuarios --promover-existentes

Senhas: nenhuma fica no codigo. Cada grupo tem a sua variavel de ambiente,
LOJA_SENHA_ADMINS e LOJA_SENHA_CLIENTES - assim a senha dos compradores de
exemplo (que circula em prints e no Postman) nunca abre o admin. O grupo sem
variavel recebe uma senha aleatoria por usuario, mostrada UMA vez no terminal.

Pode rodar de novo quantas vezes quiser: quem ja existe nao e duplicado nem
tem a senha trocada. No fim sai um resumo; se algum admin foi ignorado, o
comando termina com erro (codigo 1), mesmo tendo gravado os demais.
"""

import os
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from loja.models import PerfilCliente

User = get_user_model()

ADMINS = [
    {"username": "fabiano", "first_name": "Fabiano", "last_name": ""},
    {"username": "pamela", "first_name": "Pamela", "last_name": ""},
]

# DADOS DE EXEMPLO: compradores ficticios, inventados para testar a loja.
# Nao sao pessoas reais. O dominio example.com e reservado (RFC 2606) e
# nunca entrega e-mail a ninguem. Telefone e endereco ficam vazios.
COMPRADORES = [
    {"username": "ana.souza", "first_name": "Ana", "last_name": "Souza"},
    {"username": "bruno.lima", "first_name": "Bruno", "last_name": "Lima"},
    {"username": "carla.mendes", "first_name": "Carla", "last_name": "Mendes"},
    {"username": "diego.rocha", "first_name": "Diego", "last_name": "Rocha"},
    {"username": "elisa.martins", "first_name": "Elisa", "last_name": "Martins"},
    {"username": "felipe.costa", "first_name": "Felipe", "last_name": "Costa"},
    {"username": "gabriela.alves", "first_name": "Gabriela", "last_name": "Alves"},
    {"username": "henrique.dias", "first_name": "Henrique", "last_name": "Dias"},
]

VARIAVEL_ADMINS = "LOJA_SENHA_ADMINS"
VARIAVEL_CLIENTES = "LOJA_SENHA_CLIENTES"


def novo_usuario(dados, admin):
    """Monta o usuario (ainda sem salvar) a partir de um item das listas."""
    return User(
        username=dados["username"],
        first_name=dados["first_name"],
        last_name=dados["last_name"],
        email=f"{dados['username']}@example.com",
        is_staff=admin,
        is_superuser=admin,
    )


class Command(BaseCommand):
    help = "Cria 2 administradores e 8 compradores de exemplo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--promover-existentes",
            action="store_true",
            help="Torna admin um 'fabiano' ou 'pamela' que ja exista sem ser admin.",
        )

    def handle(self, *args, **options):
        # 1. Le e valida as senhas ANTES de gravar qualquer coisa.
        senha_admins = self.ler_senha(VARIAVEL_ADMINS, ADMINS)
        senha_clientes = self.ler_senha(VARIAVEL_CLIENTES, COMPRADORES)
        if senha_admins and senha_admins == senha_clientes:
            raise CommandError(
                f"{VARIAVEL_ADMINS} e {VARIAVEL_CLIENTES} sao iguais. Use senhas "
                "diferentes: quem souber a senha dos compradores entraria como admin."
            )

        # 2. Grava tudo ou nada: se algo falhar no meio, o banco volta ao inicio.
        #    As mensagens ficam guardadas e so aparecem DEPOIS do commit: assim
        #    a tela nunca diz "criado" para um usuario que acabou desfeito.
        self.mensagens = []        # (texto, e_aviso)
        self.senhas_geradas = []   # (username, senha)
        self.contagem = {"criado": 0, "ja existia": 0, "promovido": 0, "ignorado": 0}
        self.admins_ignorados = []
        with transaction.atomic():
            for dados in ADMINS:
                self.criar(dados, True, senha_admins, options)
            for dados in COMPRADORES:
                self.criar(dados, False, senha_clientes, options)

        # 3. Banco gravado: agora sim mostra o que aconteceu.
        for texto, e_aviso in self.mensagens:
            if e_aviso:
                self.stderr.write(self.style.WARNING(texto))
            else:
                self.stdout.write(texto)

        # As senhas geradas saem na saida padrao, uma unica vez.
        if self.senhas_geradas:
            self.stdout.write(self.style.WARNING(
                "\nSenhas geradas. Anote agora: elas NAO serao mostradas de novo."
            ))
            for username, senha in self.senhas_geradas:
                self.stdout.write(f"  {username}: {senha}")

        resumo = ", ".join(f"{qtd} {nome}" for nome, qtd in self.contagem.items())
        self.stdout.write(f"\nResumo: {resumo}.")

        # Admin ignorado = a loja pode ter ficado sem administrador. Os outros
        # usuarios ja foram gravados, mas o comando termina com erro (codigo 1)
        # para isso nao passar despercebido num script.
        if self.admins_ignorados:
            raise CommandError(
                "Admin(s) ignorado(s): " + ", ".join(self.admins_ignorados)
                + ". Veja os avisos acima; os demais usuarios foram gravados."
            )

    def ler_senha(self, variavel, usuarios):
        """Devolve a senha da variavel de ambiente, ou None se ela nao existir."""
        senha = os.environ.get(variavel)
        if senha is None:
            return None

        senha = senha.rstrip("\r\n")  # quebra de linha que vem junto ao copiar de um .env
        if not senha.strip():
            raise CommandError(f"{variavel} esta vazia ou so tem espacos.")
        if senha != senha.strip():
            # espaco escondido na ponta: a pessoa digitaria a senha sem ele e nao entraria
            raise CommandError(f"{variavel} comeca ou termina com espaco. Tire o espaco.")

        # Valida contra CADA usuario do grupo: assim o Django recusa tambem
        # senha parecida com o username ou o nome da pessoa.
        for dados in usuarios:
            try:
                validate_password(senha, user=novo_usuario(dados, False))
            except ValidationError as erro:
                # a mensagem traz so o motivo, nunca a senha
                raise CommandError(
                    f"{variavel} recusada para '{dados['username']}': "
                    + " ".join(erro.messages)
                )
        return senha

    def avisar(self, texto):
        self.mensagens.append((texto, True))

    def informar(self, texto):
        self.mensagens.append((texto, False))

    def ignorar(self, username, admin, motivo):
        self.avisar(f"IGNORADO:    {username} - {motivo}")
        self.contagem["ignorado"] += 1
        if admin:
            self.admins_ignorados.append(username)

    def criar(self, dados, admin, senha, options):
        username = dados["username"]

        # iexact: "Fabiano" e "fabiano" sao a mesma pessoa, nao duas contas.
        achados = list(User.objects.filter(username__iexact=username))
        if len(achados) > 1:
            # Ex.: "Fabiano" e "FABIANO" no banco. Nao da para saber qual e o
            # certo, entao nao mexe em nenhum.
            nomes = ", ".join(sorted(u.username for u in achados))
            self.ignorar(username, admin, f"ha mais de uma conta com esse nome ({nomes}). "
                                          "Resolva a duplicidade no admin e rode de novo.")
            return

        if not achados:
            usuario = novo_usuario(dados, admin)
            if senha is None:
                senha_gerada = secrets.token_urlsafe(12)
                self.senhas_geradas.append((username, senha_gerada))
                usuario.set_password(senha_gerada)
            else:
                usuario.set_password(senha)
            usuario.save()
            self.informar(f"criado:      {username}")
            self.contagem["criado"] += 1
        else:
            usuario = achados[0]
            # Nunca troca a senha de quem ja existe.
            if admin and not (usuario.is_staff and usuario.is_superuser and usuario.is_active):
                if not options["promover_existentes"]:
                    # Nao promove em silencio: a conta pode ser de outra pessoa.
                    self.ignorar(usuario.username, admin,
                                 "ja existe e nao e admin ativo. Confira a conta e, se for "
                                 "mesmo dela, rode com --promover-existentes.")
                    return
                usuario.is_staff = usuario.is_superuser = usuario.is_active = True
                usuario.save()
                self.avisar(f"promovido:   {usuario.username} virou admin "
                            "(a senha atual foi mantida)")
                self.contagem["promovido"] += 1
            else:
                self.informar(f"ja existia:  {usuario.username}")
                self.contagem["ja existia"] += 1
                if not admin:
                    self.conferir_comprador(usuario)

        if not admin:
            # get_or_create: nao duplica nem apaga telefone/endereco ja preenchidos
            PerfilCliente.objects.get_or_create(usuario=usuario)

    def conferir_comprador(self, usuario):
        """Avisa (sem mudar nada) se um comprador que ja existia parece estranho."""
        problemas = []
        if not usuario.is_active:
            problemas.append("esta inativo (nao consegue entrar)")
        if usuario.is_superuser or usuario.is_staff:
            problemas.append("tem acesso de administrador")
        if problemas:
            self.avisar(f"atencao:     comprador {usuario.username} " + " e ".join(problemas)
                        + ". Nada foi alterado; confira no admin.")
