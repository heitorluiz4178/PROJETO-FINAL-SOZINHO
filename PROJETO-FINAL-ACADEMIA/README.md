# FitLife Academia — Firebird e DBeaver

O banco deste projeto é o **Firebird**. O **DBeaver não é o banco**: ele é o programa usado para abrir o Firebird, executar SQL e visualizar as tabelas.

## Bibliotecas externas

```text
Flask
fdb
```

- `Flask`: cria o site.
- `fdb`: conecta o Python ao Firebird.

As bibliotecas `hashlib`, `secrets` e `hmac` já vêm com o Python.

## 1. Criar o banco Firebird

No DBeaver, crie uma conexão Firebird apontando para o arquivo do banco, por exemplo:

```text
C:\\Banco\\academia.fdb
```

Depois abra o arquivo `schema.sql` no DBeaver e execute todo o conteúdo. Ele cria as tabelas `USERS` e `PASSWORD_HISTORY`.

O script foi escrito para Firebird 3 ou superior.

## 2. Configurar o app.py

No início do arquivo `app.py`, altere estas informações:

```python
DB_HOST = 'localhost'
DB_PORT = '3050'
DB_ARQUIVO = r'C:\\Banco\\academia.fdb'
DB_USER = 'SYSDBA'
DB_PASSWORD = 'masterkey'
```

O valor de `DB_ARQUIVO` precisa ser exatamente o caminho do arquivo `.fdb` no seu computador.

## 3. Instalar e executar no PyCharm

No terminal do PyCharm:

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

No Linux ou macOS, use `source .venv/bin/activate` no lugar da segunda linha.

Abra no navegador:

```text
http://127.0.0.1:5000
```

## Rotas

- `/` — página inicial.
- `/cadastro` — cadastro de usuário.
- `/login` — login.
- `/home` — página protegida.
- `/perfil` — edição de usuário.
- `/logout` — saída.

## Regras do trabalho

O projeto possui cadastro, login, logout, senha forte, hash da senha, e-mail único, bloqueio após 3 tentativas, páginas protegidas e bloqueio das 3 últimas senhas.
