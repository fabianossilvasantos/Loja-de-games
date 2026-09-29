# Loja de Games

API REST para uma loja de games, construída com **Django 6.1** e **Django REST Framework**.
Projeto da Atividade Prática Integradora de Desenvolvimento de Sistemas I (IFRS — Campus Restinga).

> **Projeto em construção.** No momento o repositório contém apenas o esqueleto do projeto
> Django. Modelos, endpoints e autenticação ainda não foram implementados — veja
> [Estado atual](#estado-atual).

## Tecnologias

- Python 3
- Django 6.1
- Django REST Framework 3.18
- djangorestframework-simplejwt 5.5
- SQLite (banco padrão de desenvolvimento)

## Instalação

Clone o repositório:

```bash
git clone https://github.com/fabianossilvasantos/Loja-de-games.git
cd Loja-de-games
```

Crie e ative um ambiente virtual:

```bash
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Aplique as migrations:

```bash
python manage.py migrate
```

Crie um superusuário para acessar o admin (opcional):

```bash
python manage.py createsuperuser
```

Rode o servidor:

```bash
python manage.py runserver
```

O admin fica disponível em `http://127.0.0.1:8000/admin/`.

## Domínio

A loja funciona no modelo de **loja única**: um único estabelecimento com estoque próprio,
vendendo para clientes cadastrados. Não há múltiplos vendedores.

## Modelos

Ainda não implementados. O planejamento até aqui:

| Modelo          | Relacionamento                          | Situação   |
| --------------- | --------------------------------------- | ---------- |
| `Jogo`          | ManyToMany com `Genero`                 | definido   |
| `Jogo`          | ForeignKey (entidade ainda não escolhida) | pendente |
| `Genero`        | —                                       | definido   |
| `PerfilCliente` | OneToOne com `User`                     | planejado  |
| `Pedido`        | ForeignKey para `User`                  | planejado  |

## Endpoints

Nenhum endpoint implementado até o momento. Esta seção será preenchida com método HTTP,
rota e exemplos de requisição/resposta conforme a API for construída.

## Estrutura do projeto

```
Loja-de-games/
├── config/              # Configuração do projeto Django
│   ├── settings.py
│   ├── urls.py          # Rotas raiz
│   ├── asgi.py
│   └── wsgi.py
├── loja/                # App principal
│   ├── models.py        # (vazio)
│   ├── views.py         # (vazio)
│   ├── admin.py
│   └── migrations/
├── manage.py
├── requirements.txt
├── CONVENTIONAL_COMMITS.md
└── README.md
```

## Convenção de commits

As mensagens de commit seguem o padrão Conventional Commits, documentado em
[CONVENTIONAL_COMMITS.md](CONVENTIONAL_COMMITS.md).

## Estado atual

O que já existe:

- Projeto Django criado com o app `loja` e o `rest_framework` registrados no `INSTALLED_APPS`.
- Banco SQLite criado com as migrations internas do Django (`auth`, `admin`, `sessions`).
- `.gitignore` cobrindo `venv/`, `db.sqlite3`, `__pycache__/`, `.vscode/`, logs e `.env`.
- `requirements.txt` com as versões das dependências travadas em `==`.
- Idioma `pt-br` e fuso `America/Sao_Paulo` definidos no `settings.py`.

O que falta:

- **Modelos**: `loja/models.py` está vazio. Falta definir o ForeignKey de `Jogo` e escrever
  as entidades do domínio.
- **API**: sem serializers, ViewSets ou router — nenhuma rota além do admin.
- **Autenticação**: o `djangorestframework-simplejwt` está instalado, mas não configurado
  no `settings.py` nem registrado no `urls.py`. Nenhuma permissão definida.
- **Padrões de projeto**: Manager customizado e Signal ainda não implementados.
- **Testes**: `loja/tests.py` está vazio.
- **Configuração**: `SECRET_KEY` e `DEBUG` estão fixos no `settings.py`, adequado apenas
  para desenvolvimento local.
