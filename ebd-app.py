from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import matplotlib.pyplot as plt
import io

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

DATABASE = 'app.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Tabela usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            nascimento DATE,
            classe TEXT,
            tempo INTEGER
        )
    ''')
    conn.commit()
    conn.close()

@app.before_first_request
def initialize():
    init_db()

# --------- AUTENTICAÇÃO ---------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sessão.', 'info')
    return redirect(url_for('login'))

# --------- CADASTRO ---------

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        nascimento = request.form['nascimento']  # formata YYYY-MM-DD
        senha = request.form['password']
        classe = request.form['classe']
        tempo = request.form.get('tempo', 0)

        hashed_password = generate_password_hash(senha)

        conn = get_db()
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password, email, nascimento, classe, tempo) VALUES (?, ?, ?, ?, ?, ?)',
                      (username, hashed_password, email, nascimento, classe, tempo))
            conn.commit()
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Usuário ou email já cadastrado.', 'danger')
        finally:
            conn.close()

    return render_template('cadastro.html')

# --------- DASHBOARD / VISUALIZAÇÃO ---------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return render_template('dashboard.html', users=users)

# --------- RELATÓRIOS ---------

@app.route('/relatorios')
def relatorios():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    # Exemplo: relatório geral (quantidade por classe)
    c.execute("SELECT classe, COUNT(*) as total FROM users GROUP BY classe")
    por_classe = c.fetchall()

    # Aniversariantes do mês atual
    mes_atual = datetime.now().month
    c.execute("SELECT username, nascimento FROM users WHERE strftime('%m', nascimento) = ?", (f'{mes_atual:02}',))
    aniversariantes = c.fetchall()

    # Tempo médio
    c.execute("SELECT AVG(tempo) as media_tempo FROM users")
    media_tempo = c.fetchone()['media_tempo']

    conn.close()
    return render_template('relatorios.html', por_classe=por_classe, aniversariantes=aniversariantes, media_tempo=media_tempo)

# --------- GRÁFICOS ---------

@app.route('/grafico.png')
def grafico():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT classe, COUNT(*) as total FROM users GROUP BY classe")
    data = c.fetchall()
    conn.close()

    classes = [row['classe'] for row in data]
    total = [row['total'] for row in data]

    plt.figure(figsize=(6,4))
    plt.bar(classes, total, color='skyblue')
    plt.title('Usuários por Classe')
    plt.xlabel('Classe')
    plt.ylabel('Quantidade')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return send_file(img, mimetype='image/png')

# --------- RUN ---------

if __name__ == '__main__':
    app.run(debug=True)
