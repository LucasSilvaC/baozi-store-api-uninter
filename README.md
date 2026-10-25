# Baozi Store API

API REST de uma loja fictícia de pão chinês. O projeto cadastra clientes, produtos e pedidos usando Java, Spring Boot, Spring MVC, Spring Data JPA e banco relacional H2.

## Executar

Requisitos: JDK 17 ou superior e conexão com a internet na primeira execução do Maven Wrapper. O Spring Boot usado no projeto exige Java 17; se `java -version` mostrar Java 8, instale um JDK 17, por exemplo o [Eclipse Temurin 17](https://adoptium.net/temurin/releases/?version=17&os=windows&arch=x64&package=jdk).

```powershell
.\mvnw.cmd spring-boot:run
```

A API fica em `http://localhost:8080`. O banco H2 é em memória e é recriado quando a aplicação inicia. A coleção do Postman está em `postman/Baozi-Store.postman_collection.json`.

Para abrir o console H2, acesse `http://localhost:8080/h2-console` e use:

- JDBC URL: `jdbc:h2:mem:baozi`
- Usuário: `sa`
- Senha: em branco

## Entidades

- **Cliente:** `id` (Long), `nome` (String), `clienteDesde` (LocalDate).
- **Produto:** `id` (Long), `nome` (String), `preco` (BigDecimal), `estoque` (Boolean).
- **Pedido:** `id` (Long), `clienteId` (Long), `produtoId` (Long), `quantidade` (Integer). Cliente e produto são relacionamentos JPA com chaves estrangeiras.

O campo `estoque` informa se há unidades disponíveis. A API não calcula quantidade restante, pois o enunciado define esse campo como Boolean.

## Endpoints

| Recurso | Criar | Listar | Consultar | Atualizar | Excluir |
| --- | --- | --- | --- | --- | --- |
| Clientes | `POST /api/clientes` | `GET /api/clientes` | `GET /api/clientes/{id}` | `PUT /api/clientes/{id}` | `DELETE /api/clientes/{id}` |
| Produtos | `POST /api/produtos` | `GET /api/produtos` | `GET /api/produtos/{id}` | `PUT /api/produtos/{id}` | `DELETE /api/produtos/{id}` |
| Pedidos | `POST /api/pedidos` | `GET /api/pedidos` | `GET /api/pedidos/{id}` | `PUT /api/pedidos/{id}` | `DELETE /api/pedidos/{id}` |

As requisições e respostas usam JSON. Os POST retornam `201 Created`; consultas bem-sucedidas retornam `200 OK`; exclusões retornam `204 No Content`; IDs inexistentes retornam `404 Not Found`.

Ao criar um pedido, a API verifica se cliente e produto existem, se o produto está disponível e se a quantidade é positiva.

## Postman

1. Inicie a aplicação.
2. Importe `postman/Baozi-Store.postman_collection.json`.
3. Importe `postman/Baozi-Store-environment.example.json` e selecione-o. Altere `nomeCliente` para o nome que deseja usar na demonstração; o ambiente local com os dados do aluno fica fora do Git.
4. Execute as requisições da coleção em ordem. Os IDs retornados são guardados automaticamente para as consultas, atualizações e exclusões seguintes.

## Estrutura

O projeto separa o código nos pacotes mínimos solicitados: `model`, `repository` e `controller`. Os pacotes `dto` e `service` contêm os contratos JSON e regras de negócio dos pedidos.
