import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import xlsxwriter
import re

# ============================
#     CONFIGURAÇÃO GLOBAL
# ============================

st.set_page_config(
    page_title="Dashboard NMC",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema claro total
st.markdown("""
<style>
/* Remove fundos escuros */
body, .stApp, .css-1v0mbdj, .stFileUploader, .stSelectbox, .stTextInput, .stButton {
    background-color: #f7f7f7 !important;
    color: #000 !important;
}

/* Caixa do File Upload clara */
.css-1u6vki7 {
    background-color: #e8e8e8 !important;
    color: #000 !important;
    border-radius: 8px !important;
    padding: 12px !important;
}

/* Texto "Browse files" */
.stFileUploader label div {
    color: #000 !important;
    font-weight: 600 !important;
}

/* Botão de download estilizado */
.stDownloadButton > button {
    background-color: #4a90e2 !important;
    color: white !important;
    border-radius: 6px !important;
    padding: 10px 18px !important;
    font-size: 16px !important;
    font-weight: bold !important;
}

/* Ícone no botão */
.stDownloadButton > button:before {
    content: "⬇️ ";
}

/* Tabelas compactas */
table.dataframe {
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)


# ============================
# FUNÇÕES
# ============================

def extrair_usuario_do_historico(historico):
    """
    Extrai o nome após "Usuário efetuando abertura:" no histórico.
    """
    if pd.isna(historico):
        return None
    
    padrao = r"Usuário efetuando abertura:\s*([A-Za-zÀ-ÿ ]+)"
    match = re.search(padrao, historico)
    if match:
        return match.group(1).strip()
    return None


def corrigir_fechado_por(df):
    """
    Substitui "NMC.auto" pelo nome encontrado no histórico.
    Só altera nos chamados fechados por NMC.auto.
    """
    df["usuario_historico"] = df["Historico"].apply(extrair_usuario_do_historico)

    df["Fechado por"] = df.apply(
        lambda x: x["usuario_historico"] if x["Fechado por"] == "NMC.auto" and pd.notna(x["usuario_historico"]) else x["Fechado por"],
        axis=1
    )

    return df.drop(columns=["usuario_historico"])


def adicionar_percentual(df, coluna="Quantidade"):
    total = df[coluna].sum()
    if total == 0:
        df["%"] = "0%"
    else:
        df["%"] = (df[coluna] / total * 100).round(2).astype(str) + "%"
    return df


def gerar_excel(df, tabelas):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Base", index=False)

        for nome, tabela in tabelas.items():
            tabela.to_excel(writer, sheet_name=nome[:31], index=False)

    return output.getvalue()


# ============================
#       INTERFACE
# ============================

st.title("📊 Dashboard NMC — Tema Claro")

uploaded = st.file_uploader("Carregar CSV", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)

    # Corrigir fechado por NMC.auto
    df = corrigir_fechado_por(df)

    # Corrigir campos undefined
    df.fillna("(não informado)", inplace=True)

    # -------------------------
    # Cálculos das tabelas
    # -------------------------

    tabelas = {}

    # Abertos por
    t_abertos = df.groupby("Abertos por").size().reset_index(name="Quantidade")
    t_abertos = adicionar_percentual(t_abertos)
    tabelas["Abertos_por"] = t_abertos

    # Reclamação
    t_reclamacao = df.groupby("Reclamação").size().reset_index(name="Quantidade")
    t_reclamacao = adicionar_percentual(t_reclamacao)
    tabelas["Reclamacao"] = t_reclamacao

    # Diagnóstico (maior ofensor)
    t_diag = df.groupby("Diagnóstico").size().reset_index(name="Quantidade")
    t_diag = adicionar_percentual(t_diag)
    tabelas["Diagnostico"] = t_diag

    maior_ofensor = t_diag.sort_values("Quantidade", ascending=False).iloc[0]["Diagnóstico"]

    # Fechado por
    t_fechado = df.groupby("Fechado por").size().reset_index(name="Quantidade")
    t_fechado = adicionar_percentual(t_fechado)
    tabelas["Fechado_por"] = t_fechado

    # -------------------------
    # VISUALIZAÇÃO
    # -------------------------
    st.subheader("📌 Maior Ofensor (Diagnóstico)")
    st.info(f"🔎 **{maior_ofensor}**")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Abertos por")
        st.dataframe(t_abertos)

        fig = px.bar(t_abertos, x="Abertos por", y="Quantidade", text="Quantidade")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Diagnóstico")
        st.dataframe(t_diag)

        fig2 = px.pie(t_diag, values="Quantidade", names="Diagnóstico")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Reclamação")
    st.dataframe(t_reclamacao)

    st.subheader("Fechado por")
    st.dataframe(t_fechado)

    # -------------------------
    # DOWNLOAD DO DASHBOARD
    # -------------------------

    excel_bytes = gerar_excel(df, tabelas)

    st.download_button(
        label="Baixar Dashboard",
        data=excel_bytes,
        file_name="Dashboard_NMC.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
