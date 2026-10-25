# Entrega local

O relatório final é gerado por `docs/build_report.py`. Ele usa `dados.txt`, a URL em `entrega/repositorio.txt` e a execução real da coleção Postman salva em `entrega/newman-results.json`.

## Reproduzir a validação

1. Use JDK 17 ou superior e inicie a API com `.\mvnw.cmd spring-boot:run`.
2. Instale/execute Newman 6.2.3 e rode a coleção. Para um teste com dados genéricos, use:

   ```powershell
   npx --yes newman@6.2.3 run postman\Baozi-Store.postman_collection.json -e postman\Baozi-Store-environment.example.json --reporters cli,json --reporter-json-export entrega\newman-results.json
   ```

3. Coloque a URL do repositório em `entrega/repositorio.txt` e gere o PDF com `python docs/build_report.py`. O gerador exige as doze imagens em `postman/capturas/` e as incorpora na seção 4.1.

O arquivo local `postman/Baozi-Store-local.postman_environment.json` usa os dados do aluno e fica excluído do Git. O resultado JSON do Newman, o PDF e as capturas também permanecem locais porque incluem dados pessoais. A versão entregue do relatório contém a execução de 15 requisições, 27 verificações automatizadas e as doze capturas individuais exigidas do Postman Web.
