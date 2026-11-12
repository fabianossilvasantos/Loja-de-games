"""Testes do comando `python manage.py criar_usuarios`."""

import os
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from .management.commands.criar_usuarios import (
    ADMINS, COMPRADORES, VARIAVEL_ADMINS, VARIAVEL_CLIENTES,
)
from .models import PerfilCliente

User = get_user_model()

SENHA_ADMINS = "Admin-de-teste-9xQ"  # senhas que so existem no banco de teste
SENHA_CLIENTES = "Cliente-de-teste-4Wm"


# Hasher rapido so nos testes: o padrao (PBKDF2) deixaria cada teste lento.
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CriarUsuariosTest(TestCase):

    def rodar(self, *args, admins=None, clientes=None):
        """Roda o comando com as variaveis pedidas. Devolve a saida (stdout + stderr).

        A saida fica tambem em self.ultima_saida, mesmo se o comando der erro.
        """
        ambiente = {k: v for k, v in os.environ.items()
                    if k not in (VARIAVEL_ADMINS, VARIAVEL_CLIENTES)}
        if admins is not None:
            ambiente[VARIAVEL_ADMINS] = admins
        if clientes is not None:
            ambiente[VARIAVEL_CLIENTES] = clientes
        saida, erros = StringIO(), StringIO()
        try:
            with mock.patch.dict(os.environ, ambiente, clear=True):
                call_command("criar_usuarios", *args, stdout=saida, stderr=erros)
        finally:
            self.ultima_saida = saida.getvalue() + erros.getvalue()
        return self.ultima_saida

    def rodar_com_senhas(self, *args):
        return self.rodar(*args, admins=SENHA_ADMINS, clientes=SENHA_CLIENTES)

    def senhas_impressas(self, saida):
        """Le as linhas '  username: senha' do fim da saida."""
        senhas = {}
        for linha in saida.splitlines():
            if linha.startswith("  ") and ": " in linha:
                username, senha = linha.strip().split(": ", 1)
                senhas[username] = senha
        return senhas

    # --- os 10 usuarios ------------------------------------------------------

    def test_cria_os_10_usuarios(self):
        self.rodar_com_senhas()
        self.assertEqual(User.objects.count(), 10)

    def test_papeis(self):
        self.rodar_com_senhas()
        admins = User.objects.filter(is_staff=True, is_superuser=True)
        self.assertEqual(sorted(admins.values_list("username", flat=True)), ["fabiano", "pamela"])
        self.assertEqual(User.objects.get(username="fabiano").first_name, "Fabiano")
        self.assertEqual(User.objects.get(username="pamela").first_name, "Pamela")
        self.assertEqual(User.objects.filter(is_staff=False, is_superuser=False).count(), 8)

    def test_so_compradores_ganham_perfil_vazio(self):
        self.rodar_com_senhas()
        self.assertEqual(PerfilCliente.objects.count(), 8)
        for dados in COMPRADORES:
            perfil = PerfilCliente.objects.get(usuario__username=dados["username"])
            self.assertEqual((perfil.telefone, perfil.endereco), ("", ""))
        for dados in ADMINS:
            self.assertFalse(PerfilCliente.objects.filter(usuario__username=dados["username"]).exists())

    def test_emails_de_exemplo(self):
        self.rodar_com_senhas()
        for usuario in User.objects.all():
            self.assertEqual(usuario.email, f"{usuario.username}@example.com")

    # --- senhas -------------------------------------------------------------

    def test_cada_grupo_usa_a_sua_senha_e_ela_nao_vaza(self):
        saida = self.rodar_com_senhas()
        for dados in ADMINS:
            self.assertTrue(User.objects.get(username=dados["username"]).check_password(SENHA_ADMINS))
        for dados in COMPRADORES:
            self.assertTrue(User.objects.get(username=dados["username"]).check_password(SENHA_CLIENTES))
        self.assertNotIn(SENHA_ADMINS, saida)
        self.assertNotIn(SENHA_CLIENTES, saida)

    def test_grupo_sem_variavel_recebe_senhas_aleatorias(self):
        saida = self.rodar(clientes=SENHA_CLIENTES)  # sem a variavel dos admins
        impressas = self.senhas_impressas(saida)
        self.assertEqual(sorted(impressas), ["fabiano", "pamela"])
        self.assertNotEqual(impressas["fabiano"], impressas["pamela"])
        for username, senha in impressas.items():
            self.assertTrue(User.objects.get(username=username).check_password(senha))
        self.assertIn("NAO serao mostradas de novo", saida)

    def test_sem_variaveis_gera_10_senhas_diferentes(self):
        impressas = self.senhas_impressas(self.rodar())
        self.assertEqual(len(impressas), 10)
        self.assertEqual(len(set(impressas.values())), 10)

    def test_recusa_a_mesma_senha_nos_dois_grupos(self):
        with self.assertRaises(CommandError):
            self.rodar(admins=SENHA_ADMINS, clientes=SENHA_ADMINS)
        self.assertEqual(User.objects.count(), 0)

    def test_recusa_senha_fraca(self):
        with self.assertRaises(CommandError):
            self.rodar(admins="123", clientes=SENHA_CLIENTES)
        self.assertEqual(User.objects.count(), 0)

    def test_recusa_senha_parecida_com_o_username(self):
        with self.assertRaises(CommandError) as erro:
            self.rodar(admins=SENHA_ADMINS, clientes="ana.souza2026")
        self.assertNotIn("ana.souza2026", str(erro.exception))  # a senha nao aparece
        self.assertEqual(User.objects.count(), 0)

    def test_recusa_senha_vazia_ou_so_espacos(self):
        for senha in ("", "        ", "  \r\n"):
            with self.subTest(senha=repr(senha)), self.assertRaises(CommandError):
                self.rodar(admins=senha, clientes=SENHA_CLIENTES)
        self.assertEqual(User.objects.count(), 0)

    def test_tira_a_quebra_de_linha_do_fim(self):
        self.rodar(admins=SENHA_ADMINS + "\r\n", clientes=SENHA_CLIENTES + "\n")
        self.assertTrue(User.objects.get(username="fabiano").check_password(SENHA_ADMINS))
        self.assertTrue(User.objects.get(username="ana.souza").check_password(SENHA_CLIENTES))

    # --- rodar de novo --------------------------------------------------------

    def test_rodar_de_novo_nao_duplica_nem_troca_senha(self):
        self.rodar_com_senhas()
        senhas_antes = dict(User.objects.values_list("username", "password"))

        saida = self.rodar(admins="Outra-senha-7Kp", clientes="Mais-outra-2Rv")
        saida += self.rodar()  # sem variaveis: tambem nao pode gerar senha nova

        self.assertEqual(User.objects.count(), 10)
        self.assertEqual(PerfilCliente.objects.count(), 8)
        self.assertEqual(dict(User.objects.values_list("username", "password")), senhas_antes)
        self.assertEqual(self.senhas_impressas(saida), {})
        self.assertNotIn("criado:", saida)

    def test_username_com_maiusculas_e_o_mesmo_usuario(self):
        User.objects.create_user("Fabiano", password="senha-antiga-3Zt",
                                 is_staff=True, is_superuser=True)
        self.rodar_com_senhas()
        self.assertEqual(User.objects.filter(username__iexact="fabiano").count(), 1)
        self.assertEqual(User.objects.count(), 10)

    # --- usuario que ja existe ------------------------------------------------

    def test_admin_existente_sem_ser_admin_nao_e_promovido(self):
        User.objects.create_user("pamela", password="senha-antiga-3Zt")
        # admin ignorado: o comando termina com erro (codigo 1), mas grava os outros
        with self.assertRaises(CommandError) as erro:
            self.rodar_com_senhas()
        self.assertIn("pamela", str(erro.exception))
        pamela = User.objects.get(username="pamela")
        self.assertFalse(pamela.is_staff or pamela.is_superuser)
        self.assertTrue(pamela.check_password("senha-antiga-3Zt"))
        self.assertIn("IGNORADO:    pamela", self.ultima_saida)
        self.assertIn("--promover-existentes", self.ultima_saida)
        self.assertIn("Resumo: 9 criado, 0 ja existia, 0 promovido, 1 ignorado.",
                      self.ultima_saida)
        self.assertEqual(User.objects.count(), 10)  # os outros 9 foram criados

    def test_resumo_no_fim(self):
        saida = self.rodar_com_senhas()
        self.assertIn("Resumo: 10 criado, 0 ja existia, 0 promovido, 0 ignorado.", saida)
        saida = self.rodar_com_senhas()
        self.assertIn("Resumo: 0 criado, 10 ja existia, 0 promovido, 0 ignorado.", saida)

    def test_mais_de_uma_conta_com_o_mesmo_nome_e_pulada(self):
        User.objects.create_user("Fabiano", password="senha-antiga-3Zt")
        User.objects.create_user("FABIANO", password="senha-antiga-3Zt")
        User.objects.create_user("Ana.Souza", password="senha-antiga-3Zt")
        User.objects.create_user("ANA.SOUZA", password="senha-antiga-3Zt")
        with self.assertRaises(CommandError):  # um admin ficou de fora
            self.rodar_com_senhas()
        self.assertIn("FABIANO, Fabiano", self.ultima_saida)  # ordem alfabetica (ASCII)
        self.assertIn("ANA.SOUZA, Ana.Souza", self.ultima_saida)
        # nenhuma das duplicadas foi mexida, e nao nasceu uma terceira
        self.assertEqual(User.objects.filter(username__iexact="fabiano").count(), 2)
        self.assertEqual(User.objects.filter(username__iexact="ana.souza").count(), 2)
        self.assertFalse(User.objects.filter(username__iexact="fabiano", is_staff=True).exists())
        self.assertFalse(PerfilCliente.objects.filter(usuario__username__iexact="ana.souza").exists())

    def test_comprador_duplicado_nao_da_erro(self):
        User.objects.create_user("Ana.Souza", password="x")
        User.objects.create_user("ANA.SOUZA", password="x")
        saida = self.rodar_com_senhas()  # so comprador ignorado: termina sem erro
        self.assertIn("IGNORADO:    ana.souza", saida)
        self.assertIn("1 ignorado", saida)

    def test_avisa_comprador_existente_inativo_ou_admin(self):
        User.objects.create_user("bruno.lima", password="senha-antiga-3Zt", is_active=False)
        User.objects.create_user("carla.mendes", password="senha-antiga-3Zt",
                                 is_staff=True, is_superuser=True)
        saida = self.rodar_com_senhas()
        self.assertIn("comprador bruno.lima esta inativo", saida)
        self.assertIn("comprador carla.mendes tem acesso de administrador", saida)
        # so avisa, nao muda nada
        self.assertFalse(User.objects.get(username="bruno.lima").is_active)
        self.assertTrue(User.objects.get(username="carla.mendes").is_superuser)
        self.assertTrue(User.objects.get(username="carla.mendes").check_password("senha-antiga-3Zt"))

    def test_mensagens_so_aparecem_depois_de_gravar(self):
        original = PerfilCliente.objects.get_or_create

        def falha_no_terceiro(*args, **kwargs):
            if PerfilCliente.objects.count() == 2:
                raise RuntimeError("falha simulada")
            return original(*args, **kwargs)

        with mock.patch.object(PerfilCliente.objects, "get_or_create",
                               side_effect=falha_no_terceiro):
            with self.assertRaises(RuntimeError):
                self.rodar_com_senhas()
        # nada foi gravado, entao a tela nao pode dizer "criado" para ninguem
        self.assertNotIn("criado:", self.ultima_saida)
        self.assertEqual(User.objects.count(), 0)

    def test_recusa_senha_com_espaco_nas_pontas(self):
        for senha in (" " + SENHA_ADMINS, SENHA_ADMINS + " ", SENHA_ADMINS + " \r\n"):
            with self.subTest(senha=repr(senha)), self.assertRaises(CommandError) as erro:
                self.rodar(admins=senha, clientes=SENHA_CLIENTES)
            self.assertIn("espaco", str(erro.exception))
            self.assertNotIn(SENHA_ADMINS, str(erro.exception))
        self.assertEqual(User.objects.count(), 0)

    def test_promover_existentes(self):
        User.objects.create_user("pamela", password="senha-antiga-3Zt", is_active=False)
        saida = self.rodar_com_senhas("--promover-existentes")
        pamela = User.objects.get(username="pamela")
        self.assertTrue(pamela.is_staff and pamela.is_superuser and pamela.is_active)
        self.assertTrue(pamela.check_password("senha-antiga-3Zt"))  # senha mantida
        self.assertIn("promovido:   pamela", saida)

    def test_comprador_existente_ganha_perfil_e_mantem_senha(self):
        User.objects.create_user("ana.souza", password="senha-antiga-3Zt")
        self.rodar_com_senhas()
        ana = User.objects.get(username="ana.souza")
        self.assertTrue(ana.check_password("senha-antiga-3Zt"))
        self.assertTrue(PerfilCliente.objects.filter(usuario=ana).exists())

    # --- tudo ou nada -----------------------------------------------------------

    def test_falha_no_meio_desfaz_tudo(self):
        original = PerfilCliente.objects.get_or_create
        chamadas = []

        def falha_no_quinto(*args, **kwargs):
            chamadas.append(1)
            if len(chamadas) == 5:
                raise RuntimeError("falha simulada")
            return original(*args, **kwargs)

        with mock.patch.object(PerfilCliente.objects, "get_or_create", side_effect=falha_no_quinto):
            with self.assertRaises(RuntimeError):
                self.rodar()
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(PerfilCliente.objects.count(), 0)
