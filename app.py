import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt
import tempfile
from io import BytesIO
from fpdf import FPDF
import base64

# --- Configuração da página ---
st.set_page_config(page_title="Sistema Completo de Cadastro", layout="wide")
st.title("🔐 Sistema de Cadastro - Streamlit")

# --- Conexão com banco ---
conn = sqlite3.connect('cadastro.db', check_same_thread=False)
cursor = conn.cursor()

# --- Criar tabelas se não existem ---
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

# --- Funções Auxiliares ---

def criar_usuario(login, senha):
    try:
        senha_hash = generate_password_hash(senha)
        cursor.execute("INSERT INTO usuarios (login, senha_hash) VALUES (?, ?)", (login, senha_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
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

def atualizar_pessoa(id, dados):
    cursor.execute("""
        UPDATE pessoas SET
        nome=?, cpf=?, nascimento=?, email=?, telefone=?, tipo=?, matricula=?, classe=?,
        sala=?, ano_ingresso=?, cep=?, rua=?, numero=?, complemento=?, bairro=?, cidade=?, estado=?
        WHERE id=?
    """, (*dados, id))
    conn.commit()

def excluir_pessoa(id):
    cursor.execute("DELETE FROM pessoas WHERE id=?", (id,))
    conn.commit()

def carregar_cadastros():
    return pd.read_sql_query("SELECT * FROM pessoas", conn)

# --- Função para gerar PDF com cabeçalho, tabela e gráfico ---
def gerar_pdf(df, titulo="Relatório", grafico_path=None):
    pdf = FPDF()
    pdf.add_page()

    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, titulo, ln=True, align='C')
    pdf.ln(10)

    # Tabela (limitar colunas para visualização no PDF)
    pdf.set_font("Arial", 'B', 10)
    colunas = ['id', 'nome', 'cpf', 'email', 'tipo', 'classe', 'ano_ingresso', 'data_cadastro']
    espacamento = [10, 45, 25, 50, 15, 15, 20, 30]

    # Cabeçalho tabela
    for i, col in enumerate(colunas):
        pdf.cell(espacamento[i], 8, col.upper(), border=1, align='C')
    pdf.ln()

    # Linhas da tabela (limitar até 30 linhas para o PDF não ficar gigante)
    pdf.set_font("Arial", '', 9)
    for i, row in df[colunas].head(30).iterrows():
        for j, col in enumerate(colunas):
            texto = str(row[col]) if pd.notna(row[col]) else ""
            pdf.cell(espacamento[j], 7, texto, border=1)
        pdf.ln()

    pdf.ln(10)

    # Inserir gráfico (se houver)
    if grafico_path:
        pdf.image(grafico_path, x=30, w=150)

    # Salvar em buffer
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# --- Função para limpar campos do formulário ---
def limpar_form(form_vars):
    for key in form_vars:
        form_vars[key] = None

# --- Sistema de Navegação ---

if 'login' not in st.session_state:
    st.session_state['login'] = False

if not st.session_state['login']:
    st.subheader("🔑 Login")
    aba = st.radio("Selecione:", ["Entrar", "Criar Conta"])

    if aba == "Entrar":
        usuario = st.text_input("Usuário", key="login_usuario")
        senha = st.text_input("Senha", type="password", key="login_senha")
        if st.button("Entrar"):
            if verificar_login(usuario, senha):
                st.session_state['login'] = True
                st.session_state['usuario'] = usuario
                st.success(f"Bem-vindo {usuario}")
                st.experimental_rerun()
            else:
                st.error("Login ou senha incorretos.")

    elif aba == "Criar Conta":
        novo_usuario = st.text_input("Novo Usuário", key="novo_usuario")
        nova_senha = st.text_input("Nova Senha", type="password", key="nova_senha")
        if st.button("Cadastrar Usuário"):
            if criar_usuario(novo_usuario, nova_senha):
                st.success("Usuário criado com sucesso! Faça login.")
            else:
                st.error("Erro: Usuário já existe.")

else:
    st.sidebar.success(f"Logado como {st.session_state['usuario']}")
    menu = st.sidebar.radio("Menu", ["Cadastrar", "Visualizar", "Relatórios", "Gráficos", "Sair"])

    if menu == "Cadastrar":
        st.subheader("📋 Cadastro de Pessoa")

        # Variáveis para controle do formulário (para limpar e atualizar)
        form_vars = {
            'id': None,
            'nome': None,
            'cpf': None,
            'nascimento': None,
            'email': None,
            'telefone': None,
            'tipo': None,
            'matricula': None,
            'classe': None,
            'sala': None,
            'ano_ingresso': None,
            'cep': None,
            'rua': None,
            'numero': None,
            'complemento': None,
            'bairro': None,
            'cidade': None,
            'estado': None
        }

        # Se quiser atualizar, primeiro escolher registro para edição
        with st.expander("Selecionar Pessoa para Atualizar ou Excluir"):
            df = carregar_cadastros()
            if not df.empty:
                pessoa_selecionada = st.selectbox(
                    "Selecione a pessoa (pelo ID e nome):",
                    options=df.apply(lambda x: f"{x['id']} - {x['nome']}", axis=1)
                )
                id_selecionado = int(pessoa_selecionada.split(" - ")[0])
                dados_pessoa = df[df['id'] == id_selecionado].iloc[0]

                # Mostrar dados preenchidos para edição
                form_vars.update({
                    'id': dados_pessoa['id'],
                    'nome': dados_pessoa['nome'],
                    'cpf': dados_pessoa['cpf'],
                    'nascimento': pd.to_datetime(dados_pessoa['nascimento']) if dados_pessoa['nascimento'] else None,
                    'email': dados_pessoa['email'],
                    'telefone': dados_pessoa['telefone'],
                    'tipo': dados_pessoa['tipo'],
                    'matricula': dados_pessoa['matricula'],
                    'classe': dados_pessoa['classe'],
                    'sala': dados_pessoa['sala'],
                    'ano_ingresso': dados_pessoa['ano_ingresso'],
                    'cep': dados_pessoa['cep'],
                    'rua': dados_pessoa['rua'],
                    'numero': dados_pessoa['numero'],
                    'complemento': dados_pessoa['complemento'],
                    'bairro': dados_pessoa['bairro'],
                    'cidade': dados_pessoa['cidade'],
                    'estado': dados_pessoa['estado'],
                })

                if st.button("Excluir Cadastro"):
                    excluir_pessoa(id_selecionado)
                    st.success("Cadastro excluído com sucesso!")
                    st.experimental_rerun()

        with st.form("form_cadastro", clear_on_submit=False):
            nome = st.text_input("Nome Completo", value=form_vars['nome'])
            cpf = st.text_input("CPF", value=form_vars['cpf'])
            nascimento = st.date_input("Data de Nascimento", value=form_vars['nascimento'] if form_vars['nascimento'] else datetime(2000,1,1))
            email = st.text_input("Email", value=form_vars['email'])
            telefone = st.text_input("Telefone", value=form_vars['telefone'])
            tipo = st.selectbox("Tipo", ["Aluno", "Professor", "Outro"], index=["Aluno", "Professor", "Outro"].index(form_vars['tipo']) if form_vars['tipo'] in ["Aluno", "Professor", "Outro"] else 0)
            matricula = st.text_input("Matrícula", value=form_vars['matricula'])
            classe = st.selectbox("Classe", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(form_vars['classe']) if form_vars['classe'] in ["A", "B", "C", "D"] else 0)
            sala = st.text_input("Sala", value=form_vars['sala'])
            ano_ingresso = st.text_input("Ano de Ingresso", value=form_vars['ano_ingresso'])
            cep = st.text_input("CEP", value=form_vars['cep'])
            rua = st.text_input("Rua", value=form_vars['rua'])
            numero = st.text_input("Número", value=form_vars['numero'])
            complemento = st.text_input("Complemento", value=form_vars['complemento'])
            bairro = st.text_input("Bairro", value=form_vars['bairro'])
            cidade = st.text_input("Cidade", value=form_vars['cidade'])
            estado = st.text_input("Estado", value=form_vars['estado'])

            submit = st.form_submit_button("Salvar Cadastro")

            if submit:
                dados = (
                    nome, cpf, nascimento.strftime('%Y-%m-%d'), email, telefone, tipo, matricula, classe,
                    sala, ano_ingresso, cep, rua, numero, complemento, bairro, cidade, estado
                )
                if form_vars['id'] is None:
                    # Novo cadastro
                    try:
                        cadastrar_pessoa(dados)
                        st.success("Cadastro realizado com sucesso!")
                        st.experimental_rerun()
                    except sqlite3.IntegrityError as e:
                        st.error(f"Erro no cadastro: {e}")
                else:
                    # Atualizar cadastro existente
                    try:
                        atualizar_pessoa(form_vars['id'], dados)
                        st.success("Cadastro atualizado com sucesso!")
                        st.experimental_rerun()
                    except sqlite3.IntegrityError as e:
                        st.error(f"Erro na atualização: {e}")

    elif menu == "Visualizar":
        st.subheader("📑 Dados Cadastrados")
        df = carregar_cadastros()
        st.dataframe(df)

    elif menu == "Relatórios":
        st.subheader("📊 Relatórios")
        df = carregar_cadastros()
        opcao = st.selectbox("Escolha o Relatório", ["Por Classe", "Por Ano de Ingresso", "Aniversariantes", "Geral"])

        if opcao == "Por Classe":
            classes = df['classe'].dropna().unique()
            classe = st.selectbox("Selecione a Classe", classes)
            df_filtro = df[df['classe'] == classe]
        elif opcao == "Por Ano de Ingresso":
            anos = df['ano_ingresso'].dropna().unique()
            ano = st.selectbox("Selecione o Ano", anos)
            df_filtro = df[df['ano_ingresso'] == ano]
        elif opcao == "Aniversariantes":
            mes = st.slider("Selecione o Mês", 1, 12)
            df['mes_nasc'] = pd.to_datetime(df['nascimento'], errors='coerce').dt.month
            df_filtro = df[df['mes_nasc'] == mes]
        else:
            df_filtro = df

        st.dataframe(df_filtro)

        if st.button("Gerar PDF"):
            # Criar gráfico simples para relatório
            fig, ax = plt.subplots(figsize=(6,4))
            contagem = df_filtro['tipo'].value_counts()
            contagem.plot(kind='bar', ax=ax, color=['skyblue', 'orange', 'green'])
            ax.set_title("Contagem por Tipo")
            ax.set_ylabel("Quantidade")
            ax.set_xlabel("Tipo")

            # Salvar gráfico temporariamente
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            plt.savefig(temp_file.name)
            plt.close(fig)

            pdf_buffer = gerar_pdf(df_filtro, titulo=f"Relatório: {opcao}", grafico_path=temp_file.name)

            b64 = base64.b64encode(pdf_buffer.read()).decode()
            href = f'<a href="data:file/pdf;base64,{b64}" download="relatorio.pdf">⬇️ Baixar Relatório PDF</a>'
            st.markdown(href, unsafe_allow_html=True)

    elif menu == "Gráficos":
        st.subheader("📈 Gráficos")
        df = carregar_cadastros()

        if df.empty:
            st.info("Nenhum dado cadastrado para gerar gráficos.")
        else:
            tipo_grafico = st.selectbox("Tipo de Gráfico", ["Barra por Tipo", "Pizza por Classe"])

            if tipo_grafico == "Barra por Tipo":
                contagem = df['tipo'].value_counts()
                fig, ax = plt.subplots()
                contagem.plot(kind='bar', ax=ax, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
                ax.set_title("Contagem por Tipo")
                ax.set_ylabel("Quantidade")
                st.pyplot(fig)

            elif tipo_grafico == "Pizza por Classe":
                contagem = df['classe'].value_counts()
                fig, ax = plt.subplots()
                contagem.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
                ax.set_ylabel("")
                ax.set_title("Distribuição por Classe")
                st.pyplot(fig)

    elif menu == "Sair":
        st.session_state['login'] = False
        st.experimental_rerun()
