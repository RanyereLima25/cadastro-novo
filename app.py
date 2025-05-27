from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import matplotlib.pyplot as plt
import io

app = Flask(__name__)
app.secret_key = 'chave-secreta'  # Troque por uma chave forte


# ------------------------------
# Banco de dados
# ------------------------------
def criar_banco():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT UNIQUE,
            senha TEXT,
            data_nascimento TEXT,
            classe TEXT
        )
    ''')
    conn.commit()
    conn.close()

criar_banco()


# ------------------------------
# Rotas
# ------------------------------
@app.route('/')
def index():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = sqlite3.connect('banco.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario and check_password_hash(usuario[3], senha):
            session['usuario'] = usuario[1]
            return redirect('/dashboard')
        else:
            flash('Login inválido')
            return redirect('/login')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/login')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha'])
        data_nascimento = request.form['data_nascimento']
        classe = request.form['classe']

        conn = sqlite3.connect('banco.db')
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO usuarios (nome, email, senha, data_nascimento, classe)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, email, senha, data_nascimento, classe))
            conn.commit()
            flash('Usuário cadastrado com sucesso!')
        except sqlite3.IntegrityError:
            flash('Email já cadastrado.')
        finally:
            conn.close()

        return redirect('/cadastro')

    return render_template('cadastro.html')


@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios')
    usuarios = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', usuarios=usuarios)


@app.route('/relatorios')
def relatorios():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    cursor.execute('SELECT classe, COUNT(*) FROM usuarios GROUP BY classe')
    por_classe = cursor.fetchall()

    cursor.execute('SELECT * FROM usuarios')
    todos = cursor.fetchall()

    cursor.execute('''
        SELECT * FROM usuarios 
        WHERE strftime('%m', data_nascimento) = strftime('%m', 'now')
    ''')
    aniversariantes = cursor.fetchall()

    conn.close()

    return render_template('relatorios.html', por_classe=por_classe, aniversariantes=aniversariantes, todos=todos)


@app.route('/grafico')
def grafico():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    cursor.execute('SELECT classe, COUNT(*) FROM usuarios GROUP BY classe')
    dados = cursor.fetchall()

    conn.close()

    classes = [d[0] for d in dados]
    quantidades = [d[1] for d in dados]

    plt.figure(figsize=(6,6))
    plt.pie(quantidades, labels=classes, autopct='%1.1f%%')
    plt.title('Distribuição por Classe')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')


# ------------------------------
# Rodar o app
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True)
