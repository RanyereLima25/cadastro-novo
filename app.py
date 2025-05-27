import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# -------------------------------
# Conexão com o banco
# -------------------------------
conn = sqlite3.connect('cadastro.db', check_same_thread=False)
cursor = conn.cursor()

# -------------------------------
# Criação das tabelas
# -------------------------------
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS cadastro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        classe TEXT,
        data_nascimento DATE,
        data_cadastro DATE
    );
""")
conn.commit()

# -------------------------------
# Funções auxiliares
# -------------------------------
def cadastrar_usuario(usuario, senha):
    try:
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", (usuario, senha))
        conn.commit()
        return True
    except:
        return False

def validar_login(usuario, senha):
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
    return cursor.fetchone()

def cadastrar_pessoa(nome, classe, data_nascimento):
    data_cadastro = datetime.now().date()
    cursor.execute("INSERT INTO cadastro (nome, classe, data_nascimento, data_cadastro) VALUES (?, ?, ?, ?)", 
                   (nome, classe, data_nascimento, data_cadastro))
    conn.commit()

def carregar_cadastros():
    return pd.read_sql_query("SELECT * FROM cadastro", conn)

# -------------------------------
# Login
# -------------------------------
st.set_page_config(page_title="Sistema de Cadastro", layout="wide")
st.title("🔐 Sistema de Cadastro com Streamlit")

menu = ["Login", "Cadastrar Usuário"]
escolha = st.sidebar.selectbox("Menu", menu)

if escolha == "Cadastrar Usuário":
    st.subheader("Criar Conta")
    novo_usuario = st.text_input("Usuário")
    nova_senha = st.text_input("Senha", type="password")
    if st.button("Cadastrar"):
        sucesso = cadastrar_usuario(novo_usuario, nova_senha)
        if sucesso:
            st.success("Usuário cadastrado com sucesso!")
        else:
            st.error("Erro: Usuário já existe.")

elif escolha == "Login":
    st.subheader("Fazer Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        resultado = validar_login(usuario, senha)
        if resultado:
            st.success(f"Bem-vindo {usuario}!")

            # -------------------------------
            # Menu após login
            # -------------------------------
            menu2 = ["Cadastrar", "Visualizar", "Relatórios", "Gráficos"]
            escolha2 = st.sidebar.selectbox("Menu Principal", menu2)

            if escolha2 == "Cadastrar":
                st.subheader("📋 Cadastrar Pessoa")
                nome = st.text_input("Nome Completo")
                classe = st.selectbox("Classe", ["A", "B", "C", "D"])
                data_nascimento = st.date_input("Data de Nascimento")

                if st.button("Salvar Cadastro"):
                    cadastrar_pessoa(nome, classe, data_nascimento)
                    st.success("Cadastro realizado com sucesso!")

            elif escolha2 == "Visualizar":
                st.subheader("📑 Dados Cadastrados")
                df = carregar_cadastros()
                st.dataframe(df)

            elif escolha2 == "Relatórios":
                st.subheader("📊 Relatórios")
                df = carregar_cadastros()

                opcao = st.selectbox("Escolha o Relatório", ["Por Classe", "Por Período", "Aniversariantes", "Geral"])

                if opcao == "Por Classe":
                    classe = st.selectbox("Selecione a Classe", df['classe'].unique())
                    st.dataframe(df[df['classe'] == classe])

                elif opcao == "Por Período":
                    inicio = st.date_input("Data Inicial")
                    fim = st.date_input("Data Final")
                    df['data_cadastro'] = pd.to_datetime(df['data_cadastro'])
                    resultado = df[(df['data_cadastro'] >= pd.to_datetime(inicio)) & 
                                   (df['data_cadastro'] <= pd.to_datetime(fim))]
                    st.dataframe(resultado)

                elif opcao == "Aniversariantes":
                    mes = st.selectbox("Selecione o mês", list(range(1, 13)))
                    df['data_nascimento'] = pd.to_datetime(df['data_nascimento'])
                    resultado = df[df['data_nascimento'].dt.month == mes]
                    st.dataframe(resultado)

                elif opcao == "Geral":
                    st.dataframe(df)

            elif escolha2 == "Gráficos":
                st.subheader("📈 Gráficos de Cadastros")
                df = carregar_cadastros()

                st.write("Distribuição por Classe")
                graf = df['classe'].value_counts()
                st.bar_chart(graf)

                st.write("Cadastros por Mês")
                df['data_cadastro'] = pd.to_datetime(df['data_cadastro'])
                graf2 = df['data_cadastro'].dt.to_period("M").value_counts().sort_index()
                st.line_chart(graf2)

        else:
            st.error("Usuário ou senha incorretos.")
