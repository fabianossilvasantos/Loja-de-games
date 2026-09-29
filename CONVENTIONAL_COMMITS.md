# Conventional Commits

Guia da convenção de mensagens de commit adotada neste repositório.

## O que é

Conventional Commits é um padrão para escrever mensagens de commit. A ideia é que a
mensagem siga uma estrutura fixa, começando por um **tipo** que diz qual é a natureza
da mudança.

Sem padrão:

```
alteracoes
ajustes finais
agora vai
corrigi o bug
```

Com padrão:

```
feat: adiciona endpoint de jogos em promocao
fix: corrige estoque negativo ao confirmar pedido
docs: atualiza lista de endpoints no README
```

A diferença prática: dá para ler o histórico e entender o que aconteceu sem abrir cada
commit, dá para filtrar (`git log --oneline --grep "^feat"`), e ferramentas conseguem
gerar changelog e calcular a próxima versão automaticamente.

## Estrutura

```
<tipo>(<escopo opcional>): <descrição>

<corpo opcional>

<rodapé opcional>
```

Exemplo completo:

```
feat(loja): adiciona filtro de jogos disponiveis

Adiciona o query param ?disponivel=true no endpoint de jogos para
permitir listar apenas os titulos com estoque maior que zero.

Closes #7
```

Na maioria dos casos só a primeira linha basta.

## Os tipos

| Tipo | Quando usar |
| :--- | :--- |
| ![feat](https://img.shields.io/badge/feat-2EA44F?style=flat-square) | Nova funcionalidade para quem usa a API |
| ![fix](https://img.shields.io/badge/fix-D73A4A?style=flat-square) | Correção de um bug |
| ![docs](https://img.shields.io/badge/docs-0969DA?style=flat-square) | Só documentação (README, comentários, este arquivo) |
| ![style](https://img.shields.io/badge/style-8250DF?style=flat-square) | Formatação que não muda comportamento (espaços, identação) |
| ![refactor](https://img.shields.io/badge/refactor-BF8700?style=flat-square) | Reescrita que não corrige bug nem adiciona funcionalidade |
| ![perf](https://img.shields.io/badge/perf-E36209?style=flat-square) | Mudança que melhora desempenho |
| ![test](https://img.shields.io/badge/test-0E8A8A?style=flat-square) | Adiciona ou corrige testes |
| ![build](https://img.shields.io/badge/build-6E4C1E?style=flat-square) | Sistema de build ou dependências (`requirements.txt`, `Dockerfile`) |
| ![ci](https://img.shields.io/badge/ci-24292F?style=flat-square) | Configuração de integração contínua (GitHub Actions, pipelines) |
| ![chore](https://img.shields.io/badge/chore-6E7781?style=flat-square) | Manutenção que não entra em nenhuma categoria acima |
| ![revert](https://img.shields.io/badge/revert-82071E?style=flat-square) | Desfaz um commit anterior |

As cores agrupam os tipos por família: **verde e vermelho** são os dois que mudam o
comportamento da API (`feat` e `fix`), **azul** é documentação, **roxo, âmbar, laranja e
turquesa** mexem na qualidade do código sem alterar o que a API entrega, e os **tons de
cinza e marrom** são infraestrutura e manutenção.

### As dúvidas mais comuns

**![feat](https://img.shields.io/badge/feat-2EA44F?style=flat-square) ou ![fix](https://img.shields.io/badge/fix-D73A4A?style=flat-square)?**
Se antes não existia, é `feat`. Se existia mas funcionava errado, é `fix`.

**![refactor](https://img.shields.io/badge/refactor-BF8700?style=flat-square) ou ![fix](https://img.shields.io/badge/fix-D73A4A?style=flat-square)?**
Se o comportamento visível mudou, é `fix`. Se só a organização interna do código mudou e
a saída é idêntica, é `refactor`.

**![chore](https://img.shields.io/badge/chore-6E7781?style=flat-square) ou ![build](https://img.shields.io/badge/build-6E4C1E?style=flat-square)?**
Mexeu em dependências ou no processo de gerar o projeto, é `build`. `chore` é o
guarda-chuva do que sobra: configuração inicial, `.gitignore`, limpeza de arquivos.

**![docs](https://img.shields.io/badge/docs-0969DA?style=flat-square) ou ![feat](https://img.shields.io/badge/feat-2EA44F?style=flat-square)?**
Documentação nunca é `feat`, mesmo quando dá trabalho. Se o código não mudou, é `docs`.

## Escopo

O escopo é opcional e vai entre parênteses, indicando a parte do projeto afetada:

```
feat(loja): adiciona ordenacao por preco
fix(config): corrige ALLOWED_HOSTS vazio em producao
```

Neste projeto os escopos naturais são `loja` (o app do domínio) e `config` (a configuração
do projeto). Em um projeto pequeno, omitir o escopo é perfeitamente aceitável.

## Como escrever a descrição

- **Modo imperativo**: "adiciona", não "adicionado" nem "adicionando". A frase completa
  o sentido de "Se aplicado, este commit vai _adicionar..._".
- **Minúscula** na primeira letra.
- **Sem ponto final.**
- **Até ~50 caracteres.** Se não couber, o resto vai no corpo.
- **Diga o quê, não o como.** O diff já mostra o como.

| ❌ Ruim | ✅ Bom |
| :--- | :--- |
| `feat: Adicionei o serializer.` | `feat: adiciona serializer de Jogo` |
| `fix: bug` | `fix: impede preco negativo em Jogo` |
| `chore: mudancas` | `chore: adiciona gitignore do Python` |
| `feat: mudei o views.py e o urls.py` | `feat: expoe CRUD de jogos via router` |

## Breaking changes

Quando a mudança quebra compatibilidade com quem já consome a API, marque com `!` depois
do tipo:

```
feat!: renomeia campo preco_centavos para preco
```

Ou descreva no rodapé, que é o formato preferido quando precisa de explicação:

```
feat: renomeia campo preco_centavos para preco

BREAKING CHANGE: o campo preco_centavos foi renomeado para preco
em JogoSerializer. Clientes que enviam ou leem preco_centavos
precisam ser atualizados.
```

## Relação com versionamento semântico

Se o projeto usar [SemVer](https://semver.org/lang/pt-BR/) (`MAJOR.MINOR.PATCH`), os
tipos mapeiam direto:

| Tipo de commit | Incremento | Exemplo |
| :--- | :--- | :--- |
| ![fix](https://img.shields.io/badge/fix-D73A4A?style=flat-square) | PATCH | `1.0.0` → `1.0.1` |
| ![feat](https://img.shields.io/badge/feat-2EA44F?style=flat-square) | MINOR | `1.0.0` → `1.1.0` |
| ![BREAKING CHANGE](https://img.shields.io/badge/BREAKING%20CHANGE-82071E?style=flat-square) | MAJOR | `1.0.0` → `2.0.0` |

Os demais tipos (`docs`, `chore`, `style`, `test`...) não geram nova versão.

## Um commit, uma mudança

O padrão só ajuda se cada commit tiver um propósito único. Se você precisa escrever
"e" na descrição, provavelmente são dois commits:

```
# Ruim
feat: adiciona serializers e corrige bug do admin

# Bom
feat: adiciona serializers de Jogo e Genero
fix: corrige registro duplicado no admin
```

Para dividir mudanças que já estão no diretório de trabalho, use `git add` por arquivo
em vez de `git add -A`.

## O histórico deste projeto

O repositório começa com 14 commits de andaime, todos marcados como
![chore](https://img.shields.io/badge/chore-6E7781?style=flat-square):

```
chore(loja): adiciona pacote de migrations
chore(loja): adiciona tests.py
chore(loja): adiciona admin.py
chore(loja): adiciona views.py
chore(loja): adiciona models.py
chore(loja): adiciona AppConfig do app loja
chore(loja): adiciona __init__ do app
chore(config): adiciona entrypoint wsgi
chore(config): adiciona entrypoint asgi
chore(config): adiciona urls raiz do projeto
chore(config): adiciona settings e registra rest_framework e loja
chore(config): adiciona __init__ do pacote de configuracao
chore: adiciona manage.py
chore: adiciona .gitignore
```

Nenhum deles é `feat`, e isso está correto: `models.py` e `views.py` foram commitados
vazios, com o comentário gerado pelo Django. São andaimes, não funcionalidade. O primeiro
`feat` aparece quando o projeto passar a fazer alguma coisa:

| Tipo | Commit |
| :--- | :--- |
| ![feat](https://img.shields.io/badge/feat-2EA44F?style=flat-square) | `feat(loja): cria modelos Jogo e Genero com migrations` |
| ![feat](https://img.shields.io/badge/feat-2EA44F?style=flat-square) | `feat(loja): adiciona serializers de Jogo e Genero` |
| ![feat](https://img.shields.io/badge/feat-2EA44F?style=flat-square) | `feat(loja): expoe CRUD de jogos via router do DRF` |
| ![feat](https://img.shields.io/badge/feat-2EA44F?style=flat-square) | `feat(auth): adiciona rotas de obtencao e refresh de token JWT` |

### Uma ressalva sobre esses 14 commits

Eles foram divididos por **arquivo**, não por mudança lógica. Funciona para mostrar que o
histórico não foi feito de uma vez só, mas alguns commits intermediários não deixam o
projeto em estado executável — `config/settings.py` entrou registrando o app `loja` antes
de o app existir, por exemplo.

A regra que vale daqui para frente: **cada commit deve deixar o projeto funcionando**.
O model, sua migration e o registro no admin pertencem ao mesmo commit. O serializer, a
view e a rota que o expõem, também.

## Referência

Especificação oficial: <https://www.conventionalcommits.org/pt-br/v1.0.0/>
