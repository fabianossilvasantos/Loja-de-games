# Loja de Games

API REST para uma loja de games, construída com **Django 6.1** e **Django REST Framework**.
Projeto da Atividade Prática Integradora de Desenvolvimento de Sistemas I (IFRS — Campus Restinga).

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

Crie um superusuário — necessário para obter o token e para acessar o admin:

```bash
python manage.py createsuperuser
```

Rode o servidor:

```bash
python manage.py runserver
```

A API fica em `http://127.0.0.1:8000/api/` e o admin em `http://127.0.0.1:8000/admin/`.

## Domínio

A loja funciona no modelo de **loja única**: um único estabelecimento com estoque próprio,
vendendo para clientes cadastrados. Não há múltiplos vendedores.

## Modelos

| Modelo | Papel | Relacionamentos |
| --- | --- | --- |
| `Genero` | Tabela de apoio, nome único | — |
| `Desenvolvedora` | Estúdio que produziu o jogo | — |
| `Jogo` | Produto da loja | ForeignKey para `Desenvolvedora`, ManyToMany com `Genero` |
| `PerfilCliente` | Dados que o `User` do Django não guarda | OneToOne com `settings.AUTH_USER_MODEL` |
| `Pedido` | Cabeçalho da venda, com status | ForeignKey para o usuário |
| `ItemPedido` | Linha do pedido | ForeignKey para `Pedido` e para `Jogo` |

### Decisões de modelagem

**O `on_delete` varia conforme o relacionamento.** `Jogo` → `Desenvolvedora` usa `PROTECT`:
jogo é mercadoria, não pode sumir porque alguém editou o cadastro de um estúdio.
`ItemPedido` → `Pedido` usa `CASCADE`: item não existe sem o pedido.

**`Jogo.ativo` é soft delete.** O `DELETE` da API marca o jogo como inativo em vez de
apagar o registro. Apagar quebraria os pedidos que o referenciam — e o `PROTECT` no
`ItemPedido.jogo` impediria de qualquer forma.

**`ItemPedido.preco_praticado` congela o valor da compra.** Sem ele, um pedido antigo
passaria a exibir o preço de hoje, e o histórico mentiria.

## Endpoints

Todas as rotas ficam sob o prefixo `/api/`. Exceto as duas de autenticação, todas exigem
o cabeçalho `Authorization: Bearer <access>`.

### Autenticação

| Método | Rota | Descrição |
| --- | --- | --- |
| `POST` | `/api/token/` | Troca usuário e senha por um par de tokens |
| `POST` | `/api/token/refresh/` | Troca o `refresh` por um `access` novo |

**Obter o token**

```http
POST /api/token/
Content-Type: application/json

{
  "username": "fabiano",
  "password": "sua-senha"
}
```

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

O `access` vale 60 minutos; o `refresh`, um dia. Credenciais inválidas devolvem `401`.

**Renovar**

```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Jogos

| Método | Rota | Descrição |
| --- | --- | --- |
| `GET` | `/api/jogos/` | Lista todos os jogos |
| `POST` | `/api/jogos/` | Cria um jogo |
| `GET` | `/api/jogos/{id}/` | Detalha um jogo |
| `PUT` | `/api/jogos/{id}/` | Atualiza o jogo por completo |
| `PATCH` | `/api/jogos/{id}/` | Atualiza campos específicos |
| `DELETE` | `/api/jogos/{id}/` | Marca o jogo como inativo (soft delete) |
| `GET` | `/api/jogos/mais_vendidos/` | Ranking por unidades vendidas |
| `GET` | `/api/jogos/por_desenvolvedora/` | Quantidade de jogos por estúdio |

**Detalhar um jogo**

```http
GET /api/jogos/7/
Authorization: Bearer <access>
```

```json
{
  "id": 7,
  "titulo": "Elden Ring",
  "preco": "349.90",
  "estoque": 99,
  "ativo": true,
  "desenvolvedora": {
    "id": 4,
    "nome": "FromSoftware",
    "pais": "Japao",
    "ano_fundacao": 1986
  },
  "generos": [
    { "id": 1, "nome": "Acao" },
    { "id": 3, "nome": "RPG" }
  ]
}
```

**Criar um jogo**

Na leitura os relacionamentos vêm aninhados; na escrita, por id. Os campos
`desenvolvedora_id` e `generos_ids` não aparecem nas respostas.

```http
POST /api/jogos/
Authorization: Bearer <access>
Content-Type: application/json

{
  "titulo": "Hollow Knight",
  "preco": "49.90",
  "estoque": 30,
  "ativo": true,
  "desenvolvedora_id": 1,
  "generos_ids": [1, 2]
}
```

Devolve `201` com o jogo criado, no mesmo formato do `GET`.

**Atualizar um campo**

```http
PATCH /api/jogos/7/
Authorization: Bearer <access>
Content-Type: application/json

{ "estoque": 99 }
```

Devolve `200` com o jogo completo. Os demais campos permanecem.

**Remover um jogo**

```http
DELETE /api/jogos/7/
Authorization: Bearer <access>
```

Devolve `204 No Content`. O registro **não é apagado**: o campo `ativo` passa a `false`,
e um `GET` na mesma rota continua devolvendo `200`.

### Pedidos

| Método | Rota | Descrição |
| --- | --- | --- |
| `GET` | `/api/pedidos/` | Lista todos os pedidos |
| `POST` | `/api/pedidos/` | Cria um pedido |
| `GET` | `/api/pedidos/{id}/` | Detalha um pedido e seus itens |
| `PUT` | `/api/pedidos/{id}/` | Atualiza o pedido por completo |
| `PATCH` | `/api/pedidos/{id}/` | Atualiza campos específicos |
| `DELETE` | `/api/pedidos/{id}/` | Remove o pedido e seus itens |

**Criar um pedido**

O cliente manda apenas os itens (jogo e quantidade). O servidor define o dono (o usuário
autenticado), cria o pedido como `aguardando` e **congela o preço** de cada item com o preço
atual do jogo. Jogo inativo é recusado com `400`.

```http
POST /api/pedidos/
Authorization: Bearer <access>
Content-Type: application/json

{
  "itens_entrada": [
    { "jogo": 7, "quantidade": 2 },
    { "jogo": 5, "quantidade": 1 }
  ]
}
```

Devolve `201` com o pedido no mesmo formato do `GET` — o `preco_praticado` de cada item vem
preenchido pelo servidor, não pelo cliente.

**Detalhar um pedido**

Os itens vêm aninhados, com o título do jogo e o preço praticado na compra.

```http
GET /api/pedidos/8/
Authorization: Bearer <access>
```

```json
{
  "id": 8,
  "cliente": "pamela",
  "status": "pago",
  "criado_em": "2026-10-13T16:14:30.054373-03:00",
  "itens": [
    { "id": 13, "jogo": "Elden Ring", "quantidade": 1, "preco_praticado": "349.90" },
    { "id": 14, "jogo": "Street Fighter 6", "quantidade": 2, "preco_praticado": "299.90" },
    { "id": 15, "jogo": "Uncharted 4", "quantidade": 4, "preco_praticado": "149.90" }
  ]
}
```

Os valores possíveis de `status` são `aguardando`, `pago`, `enviado` e `cancelado`.
Alterá-lo tem efeito sobre o estoque — veja [Regras de negócio](#regras-de-negócio).

**Pagamento e estoque.** Mudar o status para `pago` (via `PATCH`) baixa o estoque pelo
signal. Se faltar estoque para algum item, o pagamento é **recusado com `400`** e o status
não muda.

### Consultas agregadas

**Jogos mais vendidos**

```http
GET /api/jogos/mais_vendidos/
Authorization: Bearer <access>
```

```json
[
  { "id": 5, "titulo": "Uncharted 4", "total_vendido": 4 },
  { "id": 7, "titulo": "Elden Ring", "total_vendido": 3 },
  { "id": 9, "titulo": "Battlefield 2042", "total_vendido": 3 }
]
```

Jogos sem venda aparecem com `0`, não `null`.

**Jogos por desenvolvedora**

```http
GET /api/jogos/por_desenvolvedora/
Authorization: Bearer <access>
```

```json
[
  { "id": 1, "nome": "Capcom", "total_jogos": 4 },
  { "id": 4, "nome": "FromSoftware", "total_jogos": 2 },
  { "id": 3, "nome": "Naughty Dog", "total_jogos": 2 }
]
```

### Sem autenticação

Qualquer rota sob `/api/`, exceto as de token, devolve `401` sem o cabeçalho:

```json
{ "detail": "As credenciais de autenticação não foram fornecidas." }
```

## Interface web

Além da API, há uma interface gráfica renderizada pelo servidor (Django templates), sob o
prefixo `/loja/`:

| Rota | Descrição |
| --- | --- |
| `/loja/` | Catálogo de jogos (público) |
| `/loja/jogos/{id}/` | Detalhe de um jogo |
| `/loja/pedidos/` | Lista de pedidos (exige login) |
| `/loja/pedidos/{id}/` | Detalhe do pedido, com mudança de status |
| `/loja/login/` · `/loja/logout/` | Entrar e sair (sessão) |

Ao contrário da API (que usa JWT), a interface usa **login de sessão** do Django. Mudar o
status de um pedido pela tela dispara o mesmo signal de estoque — e também recusa o
pagamento sem estoque.

## Regras de negócio

**Baixa de estoque no pagamento.** Um signal observa o `Pedido`. Quando o status muda para
`pago`, o estoque de cada jogo do pedido é reduzido. Enquanto o pedido está `aguardando`, o
produto ainda pertence à loja e o estoque não se altera.

**Devolução ao cancelar.** Se um pedido sai de `pago` ou `enviado` para `cancelado`, as
unidades voltam ao estoque. Cancelar um pedido `aguardando` não devolve nada — nele o
estoque nunca foi baixado.

A detecção usa dois signals: `pre_save` lê o status ainda gravado no banco, e `post_save`
compara com o novo. Sem isso, salvar o mesmo pedido duas vezes baixaria o estoque duas
vezes.

**Disponibilidade.** O Manager customizado `Jogo.objects.disponiveis()` devolve apenas
jogos com `estoque > 0` **e** `ativo = True`. São condições distintas: estoque é fato do
depósito, `ativo` é decisão comercial.

**Criação de pedido (padrão de mercado).** Na API, o dono do pedido é sempre o usuário
autenticado — nunca vem no corpo da requisição —, o pedido nasce `aguardando`, e o
`preco_praticado` é copiado do jogo pelo servidor (o cliente não dita o preço). Jogo inativo
não entra no pedido, e o pagamento só é aceito se houver estoque para todos os itens. Essa
regra de estoque fica num único método (`Pedido.itens_sem_estoque()`), reaproveitado pela API
e pela interface.

## Evidências

A pasta [`evidencias/`](evidencias/) traz a coleção do Postman com os fluxos da API,
incluindo os três cenários de autenticação: obtenção do token, requisição autenticada e
requisição sem token.

Para usar: importe o arquivo no Postman, rode a requisição `Login`, copie o `access` e
cole na aba **Authorization** da coleção, como *Bearer Token*.

## Testes

```bash
python manage.py test loja
```

Os testes cobrem o signal de estoque, o Manager de disponibilidade e as regras de mercado do
pedido (dono, preço no servidor, jogo inativo e validação de estoque no pagamento). Eles
rodam automaticamente a cada pull request, pelo workflow em
[`.github/workflows/ci.yml`](.github/workflows/ci.yml), junto com `manage.py check` e a
verificação de migrations pendentes.

## Estrutura do projeto

```
Loja-de-games/
├── .github/workflows/
│   └── ci.yml               # verificações automáticas nos pull requests
├── config/                  # configuração do projeto Django
│   ├── settings.py          # DRF, JWT, idioma e fuso
│   ├── urls.py              # rotas de token e include do app
│   ├── asgi.py
│   └── wsgi.py
├── loja/                    # app principal
│   ├── models.py            # os seis models e o Manager customizado
│   ├── serializers.py       # tradução model ↔ JSON, com aninhamento
│   ├── views.py             # ViewSets, permissões e consultas agregadas
│   ├── urls.py              # Router do DRF
│   ├── web_views.py         # views da interface web (HTML)
│   ├── web_urls.py          # rotas da interface web
│   ├── templates/loja/      # páginas HTML da interface
│   ├── static/loja/         # CSS da interface
│   ├── signals.py           # baixa e devolução de estoque
│   ├── admin.py
│   ├── tests.py
│   └── migrations/
├── evidencias/              # coleção do Postman
├── manage.py
├── requirements.txt
├── CONVENTIONAL_COMMITS.md
└── README.md
```

## Convenção de commits

As mensagens de commit seguem o padrão Conventional Commits, documentado em
[CONVENTIONAL_COMMITS.md](CONVENTIONAL_COMMITS.md).

## Limitações conhecidas

- **Estoque e preço só são garantidos pela API.** Ao criar pedido pela API, o servidor
  congela o preço e recusa pagamento sem estoque. Pelo admin/ORM, o `preco_praticado` ainda
  é digitado à mão e não há validação de estoque.
- **Permissão de acesso é por autenticação, não por dono.** Qualquer usuário autenticado
  acessa todos os pedidos, inclusive os de outros clientes.
- **Sem paginação.** As listagens devolvem todos os registros de uma vez.
- **`SECRET_KEY` e `DEBUG` fixos no `settings.py`**, adequado apenas para desenvolvimento
  local.
