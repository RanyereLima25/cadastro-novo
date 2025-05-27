import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import tempfile
import matplotlib.pyplot as plt
import io
import os


# Arquivos CSV
USUARIOS_CSV = "usuarios.csv"
CADASTROS_CSV = "cadastros.csv"


# Funções de Usuários
def carregar_usuarios():
    try:
        return pd.read_csv(USUARIOS_CSV)
    except FileNotFoundError:
        return pd.DataFrame(columns=["usuario", "senha"])


def salvar_usuarios(df):
    df.to_csv(USUARIOS_CSV, index=False)


def verificar_login(usuario, senha):
    df = carregar_usuarios()
    user = df[(df['usuario'] == usuario) & (df['senha'] == senha)]
    return not user.empty


def criar_usuario(usuario, senha):
    df = carregar_usuarios()

    if usuario in df["usuario"].values:
        st.error("Usuário já cadastrado!")
        return False

    novo_registro = pd.DataFrame([{"usuario": usuario, "senha": senha}])
    df = pd.concat([df, novo_registro], ignore_index=True)

    salvar_usuarios(df)
    st.success("Usuário criado com sucesso!")
    return True


# Funções de Cadastro de Pessoas
def carregar_cadastros():
    try:
        return pd.read_csv(CADASTROS_CSV)
    except FileNotFoundError:
        cols = ['id', 'nome', 'cpf', 'nascimento', 'email', 'telefone', 'tipo', 'matricula',
                'classe', 'sala', 'ano_ingresso', 'cep', 'rua', 'numero', 'complemento',
                'bairro', 'cidade', 'estado']
        return pd.DataFrame(columns=cols)


def salvar_cadastros(df):
    df.to_csv(CADASTROS_CSV, index=False)


def cadastrar_pessoa(dados):
    df = carregar_cadastros()
    novo_id = 1 if df.empty else df['id'].astype(int).max() + 1
    nova_linha = dict(zip(df.columns.drop('id'), dados))
    nova_linha['id'] = novo_id

    df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
    salvar_cadastros(df)


def atualizar_pessoa(id_pessoa, dados):
    df = carregar_cadastros()
    if id_pessoa in df['id'].astype(int).values:
        for i, col in enumerate(df.columns.drop('id')):
            df.loc[df['id'].astype(int) == id_pessoa, col] = dados[i]
        salvar_cadastros(df)


def excluir_pessoa(id_pessoa):
    df = carregar_cadastros()
    df = df[df['id'].astype(int) != id_pessoa]
    salvar_cadastros(df)


# Geração de PDF
def gerar_pdf(df, titulo, path_imagem):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - 50, titulo)

    if os.path.exists(path_imagem):
        c.drawImage(path_imagem, 50, height - 250, width=500, height=150)

    data = [list(df.columns)]
    for idx, row in df.head(20).iterrows():
        data.append(list(row.astype(str)))

    table = Table(data, colWidths=[50] + [80]*(len(df.columns)-1))
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0),(-1,0), 10),
        ('BOTTOMPADDING', (0,0),(-1,0), 6),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    table.wrapOn(c, width, height)
    table.drawOn(c, 30, height - 500)

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer
