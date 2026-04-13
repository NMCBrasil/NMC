import streamlit as st
import pandas as pd
import os
from io import BytesIO

st.set_page_config(
    page_title="Dashboard Operadoras",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("📊 Dashboard Operadoras")

ARQUIVO = "dados.csv"

# ======================
# CARREGAR DADOS
# ======================
def carregar():
    if os.path.exists(ARQUIVO):
        return pd.read_csv(ARQUIVO)
    return pd.DataFrame(columns=["Mês", "Operadora", "Circuito", "Desconto"])

def salvar(df):
    df.to_csv(ARQUIVO, index=False)

df = carregar()

# ======================
# FORMULÁRIO
# ======================
st.header("➕ Adicionar Registro")

with st.form("form"):
    col1, col2, col3, col4 = st.columns(4)

    mes = col1.text_input("Mês")
    operadora = col2.text_input("Operadora")
    circuito = col3.text_input("Circuito")
    desconto = col4.number_input("Desconto", step=1.0)

    enviar = st.form_submit_button("Adicionar")

if enviar:
    if mes and operadora and circuito:
        novo = pd.DataFrame([{
            "Mês": mes,
            "Operadora": operadora,
            "Circuito": circuito,
            "Desconto": float(desconto)
        }])

        df = pd.concat([df, novo], ignore_index=True)
        salvar(df)

        st.success("Registro salvo com sucesso!")
        st.rerun()
    else:
        st.error("Preencha todos os campos!")

# ======================
# SIDEBAR
# ======================
if not df.empty:

    with st.sidebar:
        st.header("🔎 Filtros")

        mes_f = st.selectbox(
            "Mês",
            ["Todos"] + sorted(df["Mês"].dropna().unique().tolist())
        )

        op_f = st.selectbox(
            "Operadora",
            ["Todas"] + sorted(df["Operadora"].dropna().unique().tolist())
        )

    filtrado = df.copy()

    if mes_f != "Todos":
        filtrado = filtrado[filtrado["Mês"] == mes_f]

    if op_f != "Todas":
        filtrado = filtrado[filtrado["Operadora"] == op_f]

    # ======================
    # KPIs
    # ======================
    st.subheader("📌 Resumo")

    c1, c2, c3 = st.columns(3)

    c1.metric("💰 Total", f"R$ {filtrado['Desconto'].sum():,.2f}")
    c2.metric("📡 Circuitos", len(filtrado))
    c3.metric("🏢 Operadoras", filtrado["Operadora"].nunique())

    st.divider()

    # ======================
    # GRÁFICOS
    # ======================
    st.subheader("📈 Gráficos")

    col1, col2 = st.columns(2)

    col1.bar_chart(filtrado.groupby("Operadora")["Desconto"].sum())
    col2.line_chart(filtrado.groupby("Mês")["Desconto"].sum())

    st.divider()

    # ======================
    # EXPORT EXCEL
    # ======================
    def to_excel(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button(
        "📥 Exportar Excel",
        data=to_excel(filtrado),
        file_name="dashboard.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.divider()

    # ======================
    # TABELA
    # ======================
    st.subheader("📋 Dados")

    st.dataframe(filtrado, use_container_width=True, hide_index=True)

else:
    st.info("Nenhum dado cadastrado ainda.")
