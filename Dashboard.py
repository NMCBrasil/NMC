import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# ======= Carregar arquivo =======
st.title("Dashboard NMC – Análises Operacionais")

uploaded_file = st.file_uploader("Envie o arquivo Excel", type=["xlsx"])

if uploaded_file:
    # Lê todas as abas
    xls = pd.ExcelFile(uploaded_file)
    abas = xls.sheet_names

    st.sidebar.title("Abas do Arquivo")
    aba_selecionada = st.sidebar.selectbox("Selecione uma aba", abas)

    df = pd.read_excel(xls, aba_selecionada)

    st.header(f"Tabela: {aba_selecionada}")

    # ======= Adicionar coluna de porcentagem (somente nas tabelas que devem mostrar % em cada item) =======
    if aba_selecionada.lower() in ["reclamação", "reclamacao", "diagnóstico", "diagnostico"]:
        df["%"] = (df.iloc[:, 1] / df.iloc[:, 1].sum()) * 100
        df["%"] = df["%"].round(2)

    # ======= Mostrar tabela normalmente (todas as abas) =======
    # MAS Reclamação e Diagnóstico ganham tamanho maior
    if aba_selecionada.lower() in ["reclamação", "reclamacao", "diagnóstico", "diagnostico"]:
        # Expande largura por CSS
        st.markdown("""
            <style>
                .big-table .stDataFrame {width: 100% !important;}
                .big-table table {font-size: 16px;}
            </style>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="big-table">', unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, height=600)
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Todas as outras tabelas normais
        st.dataframe(df, use_container_width=True)
