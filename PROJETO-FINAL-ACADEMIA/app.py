import hashlib
import fdb
from flask import Flask, render_template, request, redirect, url_for, session, flash

# DADOS DO FIREBIRD
# Exemplo de caminho no Windows:
# C:\\Banco\\academia.fdb
DB_HOST = 'localhost'
DB_PORT = '3050'
DB_ARQUIVO = r'C:\\Banco\\academia.fdb'
DB_USER = 'SYSDBA'
DB_PASSWORD = 'masterkey'  # troque pela senha do seu Firebird

app = Flask(__name__, static_folder='statics')
app.secret_key = 'chave-secreta-do-projeto'


# ---------- FUNÇÕES BÁSICAS ----------

def banco():
    """Abre a conexão com o Firebird."""
    return fdb.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_ARQUIVO,
        user=DB_USER,
        password=DB_PASSWORD,
        charset='UTF8'
    )


def proteger_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def senha_igual(senha_digitada, senha_salva):
    return proteger_senha(senha_digitada) == senha_salva


def senha_forte(senha):
    if len(senha) < 8:
        return False
    if not any(letra.isupper() for letra in senha):
        return False
    if not any(letra.islower() for letra in senha):
        return False
    if not any(letra.isdigit() for letra in senha):
        return False
    if not any(not letra.isalnum() for letra in senha):
        return False
    return True


def usuario_logado():
    if 'usuario_id' not in session:
        return None

    conexao = banco()
    cursor = conexao.cursor()
    cursor.execute(
        'SELECT ID, NAME, EMAIL, ACTIVE FROM USERS WHERE ID = ?',
        (session['usuario_id'],)
    )
    usuario = cursor.fetchone()
    cursor.close()
    conexao.close()
    return usuario


# ---------- ROTAS ----------

@app.route('/')
def inicio():
    return render_template('index.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        senha = request.form['password']
        confirmacao = request.form['password_confirmation']

        if len(nome) < 3:
            flash('Digite seu nome completo.', 'error')
        elif '@' not in email:
            flash('Digite um e-mail válido.', 'error')
        elif senha != confirmacao:
            flash('As senhas não conferem.', 'error')
        elif not senha_forte(senha):
            flash('A senha precisa ter 8 caracteres, maiúscula, minúscula, número e símbolo.', 'error')
        else:
            conexao = banco()
            cursor = conexao.cursor()
            try:
                hash_senha = proteger_senha(senha)
                cursor.execute(
                    'INSERT INTO USERS (NAME, EMAIL, PASSWORD_HASH) VALUES (?, ?, ?)',
                    (nome, email, hash_senha)
                )
                cursor.execute('SELECT ID FROM USERS WHERE EMAIL = ?', (email,))
                id_usuario = cursor.fetchone()[0]
                cursor.execute(
                    'INSERT INTO PASSWORD_HISTORY (USER_ID, PASSWORD_HASH) VALUES (?, ?)',
                    (id_usuario, hash_senha)
                )
                conexao.commit()
                flash('Cadastro realizado com sucesso.', 'success')
                return redirect(url_for('login'))
            except fdb.IntegrityError:
                conexao.rollback()
                flash('Este e-mail já está cadastrado.', 'error')
            finally:
                cursor.close()
                conexao.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        senha = request.form['password']

        conexao = banco()
        cursor = conexao.cursor()
        cursor.execute('SELECT * FROM USERS WHERE EMAIL = ?', (email,))
        usuario = cursor.fetchone()

        if usuario is None:
            flash('E-mail ou senha incorretos.', 'error')
        elif usuario[4] == 0:
            flash('Este usuário está bloqueado.', 'error')
        elif senha_igual(senha, usuario[3]):
            cursor.execute('UPDATE USERS SET FAILED_ATTEMPTS = 0 WHERE ID = ?', (usuario[0],))
            conexao.commit()
            session['usuario_id'] = usuario[0]
            cursor.close()
            conexao.close()
            return redirect(url_for('home'))
        else:
            tentativas = usuario[5] + 1
            if tentativas >= 3:
                cursor.execute(
                    'UPDATE USERS SET FAILED_ATTEMPTS = ?, ACTIVE = 0 WHERE ID = ?',
                    (tentativas, usuario[0])
                )
                flash('Usuário bloqueado após 3 tentativas.', 'error')
            else:
                cursor.execute(
                    'UPDATE USERS SET FAILED_ATTEMPTS = ? WHERE ID = ?',
                    (tentativas, usuario[0])
                )
                flash('Senha incorreta.', 'error')
            conexao.commit()

        cursor.close()
        conexao.close()

    return render_template('login.html')


@app.route('/home')
def home():
    usuario = usuario_logado()
    if usuario is None:
        flash('Faça login para continuar.', 'error')
        return redirect(url_for('login'))
    if usuario[3] == 0:
        session.clear()
        flash('Sua conta está bloqueada.', 'error')
        return redirect(url_for('login'))

    dados = {'id': usuario[0], 'name': usuario[1], 'email': usuario[2]}
    return render_template('home.html', user=dados)


@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    usuario = usuario_logado()
    if usuario is None:
        return redirect(url_for('login'))

    dados = {'id': usuario[0], 'name': usuario[1], 'email': usuario[2]}

    if request.method == 'POST':
        nome = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        nova_senha = request.form['new_password']

        conexao = banco()
        cursor = conexao.cursor()
        try:
            cursor.execute('SELECT PASSWORD_HASH FROM USERS WHERE ID = ?', (usuario[0],))
            senha_atual = cursor.fetchone()[0]
            hash_final = senha_atual

            if nova_senha:
                if not senha_forte(nova_senha):
                    flash('A nova senha não é forte o suficiente.', 'error')
                    return render_template('profile.html', user=dados)

                cursor.execute(
                    'SELECT PASSWORD_HASH FROM PASSWORD_HISTORY WHERE USER_ID = ? ORDER BY CREATED_AT DESC ROWS 3',
                    (usuario[0],)
                )
                for senha_antiga in cursor.fetchall():
                    if senha_igual(nova_senha, senha_antiga[0]):
                        flash('Não pode usar uma das 3 últimas senhas.', 'error')
                        return render_template('profile.html', user=dados)

                hash_final = proteger_senha(nova_senha)
                cursor.execute(
                    'INSERT INTO PASSWORD_HISTORY (USER_ID, PASSWORD_HASH) VALUES (?, ?)',
                    (usuario[0], hash_final)
                )

            cursor.execute(
                'UPDATE USERS SET NAME = ?, EMAIL = ?, PASSWORD_HASH = ? WHERE ID = ?',
                (nome, email, hash_final, usuario[0])
            )
            conexao.commit()
            flash('Perfil atualizado.', 'success')
            return redirect(url_for('perfil'))
        except fdb.IntegrityError:
            conexao.rollback()
            flash('Este e-mail já está sendo usado.', 'error')
        finally:
            cursor.close()
            conexao.close()

    return render_template('profile.html', user=dados)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


app.run(debug=True)
