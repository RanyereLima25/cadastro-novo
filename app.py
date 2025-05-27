import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------------
# Configuração da página
# ---------------------------------
st.set_page_config(page_title="Sistema Completo de Cadastro", layout="wide")
st.title("🔐 Sistema de Cadastro - Escola Biblica Dominical (EBD)")

# ---------------------------------
# Conexão com o banco de dados
# ---------------------------------
conn = sqlite3.connect('cadastro.db', check_same_thread=False)
cursor = conn.cursor()

# ---------------------------------
# Criação das tabelas
# ---------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pessoas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE,
    nascimento TEXT,
    email TEXT,
    telefone TEXT,
    tipo TEXT,
    matricula TEXT,
    classe TEXT,
    sala TEXT,
    ano_ingresso TEXT,
    cep TEXT,
    rua TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cidade TEXT,
    estado TEXT,
    data_cadastro TEXT
);
""")
conn.commit()

# ---------------------------------
# Funções Auxiliares
# ---------------------------------

def criar_usuario(login, senha):
    try:
        senha_hash = generate_password_hash(senha)
        cursor.execute("INSERT INTO usuarios (login, senha_hash) VALUES (?, ?)", (login, senha_hash))
        conn.commit()
        return True
    except:
        return False

def verificar_login(login, senha):
    cursor.execute("SELECT senha_hash FROM usuarios WHERE login = ?", (login,))
    resultado = cursor.fetchone()
    if resultado and check_password_hash(resultado[0], senha):
        return True
    return False

def cadastrar_pessoa(dados):
    data_cadastro = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("""
        INSERT INTO pessoas (
            nome, cpf, nascimento, email, telefone, tipo, matricula, classe,
            sala, ano_ingresso, cep, rua, numero, complemento, bairro, cidade, estado, data_cadastro
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (*dados, data_cadastro))
    conn.commit()

def carregar_cadastros():
    return pd.read_sql_query("SELECT * FROM pessoas", conn)

# ---------------------------------
# Sistema de Navegação Linear
# ---------------------------------
if 'login' not in st.session_state:
    st.session_state['login'] = False

if not st.session_state['login']:
    st.subheader("🔑 Login")
    aba = st.radio("Selecione:", ["Entrar", "Criar Conta"])

    if aba == "Entrar":
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if verificar_login(usuario, senha):
                st.session_state['login'] = True
                st.session_state['usuario'] = usuario
                st.success(f"Bem-vindo {usuario}")
                st.rerun()
            else:
                st.error("Login ou senha incorretos.")

    elif aba == "Criar Conta":
        novo_usuario = st.text_input("Novo Usuário")
        nova_senha = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar Usuário"):
            if criar_usuario(novo_usuario, nova_senha):
                st.success("Usuário criado com sucesso! Faça login.")
            else:
                st.error("Erro: Usuário já existe.")

# ---------------------------------
# Menu principal após login
# ---------------------------------
else:
    st.sidebar.success(f"Logado como {st.session_state['usuario']}")
    menu = st.sidebar.radio("Menu", ["Cadastrar", "Visualizar", "Relatórios", "Gráficos", "Sair"])

    if menu == "Cadastrar":
        st.subheader("📋 Cadastro de Pessoa")
        with st.form("form_cadastro"):
            nome = st.text_input("Nome Completo")
            cpf = st.text_input("CPF")
            nascimento = st.date_input("Data de Nascimento")
            email = st.text_input("Email")
            telefone = st.text_input("Telefone")
            tipo = st.selectbox("Tipo", ["Aluno", "Professor", "Outro"])
            matricula = st.text_input("Matrícula")
            classe = st.selectbox("Classe", ["A", "B", "C", "D"])
            sala = st.text_input("Sala")
            ano_ingresso = st.text_input("Ano de Ingresso")
            cep = st.text_input("CEP")
            rua = st.text_input("Rua")
            numero = st.text_input("Número")
            complemento = st.text_input("Complemento")
            bairro = st.text_input("Bairro")
            cidade = st.text_input("Cidade")
            estado = st.text_input("Estado")

            submit = st.form_submit_button("Salvar Cadastro")

            if submit:
                dados = (
                    nome, cpf, str(nascimento), email, telefone, tipo, matricula, classe,
                    sala, ano_ingresso, cep, rua, numero, complemento, bairro, cidade, estado
                )
                cadastrar_pessoa(dados)
                st.success("Cadastro realizado com sucesso!")

    elif menu == "Visualizar":
        st.subheader("📑 Dados Cadastrados")
        df = carregar_cadastros()
        st.dataframe(df)

    elif menu == "Relatórios":
        st.subheader("📊 Relatórios")
        df = carregar_cadastros()

        opcao = st.selectbox("Escolha o Relatório", ["Por Classe", "Por Ano de Ingresso", "Aniversariantes", "Geral"])

        if opcao == "Por Classe":
            classe = st.selectbox("Selecione a Classe", df['classe'].dropna().unique())
            st.dataframe(df[df['classe'] == classe])

        elif opcao == "Por Ano de Ingresso":
            ano = st.selectbox("Selecione o Ano", df['ano_ingresso'].dropna().unique())
            st.dataframe(df[df['ano_ingresso'] == ano])

        elif opcao == "Aniversariantes":
            mes = st.selectbox("Selecione o mês", list(range(1, 13)))
            df['nascimento'] = pd.to_datetime(df['nascimento'], errors='coerce')
            resultado = df[df['nascimento'].dt.month == mes]
            st.dataframe(resultado)

        elif opcao == "Geral":
            st.dataframe(df)

    elif menu == "Gráficos":
        st.subheader("📈 Gráficos de Cadastros")
        df = carregar_cadastros()

        if not df.empty:
            st.write("Distribuição por Classe")
            graf = df['classe'].value_counts()
            st.bar_chart(graf)

            st.write("Cadastros por Ano de Ingresso")
            graf2 = df['ano_ingresso'].value_counts().sort_index()
            st.bar_chart(graf2)

            st.write("Cadastros por Mês (Data de Cadastro)")
            df['data_cadastro'] = pd.to_datetime(df['data_cadastro'], errors='coerce')
            graf3 = df['data_cadastro'].dt.to_period("M").value_counts().sort_index()
            st.line_chart(graf3)

        else:
            st.warning("Não há dados suficientes para gerar gráficos.")

    elif menu == "Sair":
        st.session_state['login'] = False
        st.session_state.pop('usuario')
        st.success("Você saiu do sistema.")
        st.rerun()
