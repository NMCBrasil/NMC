import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Dashboard Operadoras", layout="wide")

st.title("📊 Dashboard Operadoras")

# ======================
# SUPABASE CONEXÃO
# ======================
url = "https://whbwdmmgrylwehdarupk.supabase.co"
key = "sb_publishable_iU9EdbgP5pxbjxzTtxwmAg_6Vqw03uW"

supabase = create_client(url, key)

# ======================
# BUSCAR DADOS
# ======================
def get_data():
    response = supabase.table("registros").select("*").execute()
    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame(columns=["id", "mes", "operadora", "circuito", "desconto"])

# ======================
# INSERIR DADOS
# ======================
def insert_data(mes, operadora, circuito, desconto):
    supabase.table("registros").insert({
        "mes": mes,
        "operadora": operadora,
        "circuito": circuito,
        "desconto": desconto
    }).execute()

# ======================
# CARREGAR DF
# ======================
df = get_data()

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
        insert_data(mes, operadora, circuito, float(desconto))
        st.success("Salvo no banco com sucesso!")
        st.rerun()
    else:
        st.error("Preencha todos os campos!")

# ======================
# FILTROS + DASHBOARD
# ======================
if not df.empty:

    st.sidebar.header("🔎 Filtros")

    mes_f = st.sidebar.selectbox(
        "Mês",
        ["Todos"] + sorted(df["mes"].dropna().unique().tolist())
    )

    op_f = st.sidebar.selectbox(
        "Operadora",
        ["Todas"] + sorted(df["operadora"].dropna().unique().tolist())
    )

    filtrado = df.copy()

    if mes_f != "Todos":
        filtrado = filtrado[filtrado["mes"] == mes_f]

    if op_f != "Todas":
        filtrado = filtrado[filtrado["operadora"] == op_f]

    # ======================
    # KPIs
    # ======================
    st.subheader("📌 Resumo")

    c1, c2, c3 = st.columns(3)

    c1.metric("💰 Total Desconto", f"R$ {filtrado['desconto'].sum():,.2f}")
    c2.metric("📡 Circuitos", len(filtrado))
    c3.metric("🏢 Operadoras", filtrado["operadora"].nunique())

    st.divider()

    # ======================
    # GRÁFICOS
    # ======================
    st.subheader("📈 Gráficos")

    col1, col2 = st.columns(2)

    col1.bar_chart(filtrado.groupby("operadora")["desconto"].sum())
    col2.line_chart(filtrado.groupby("mes")["desconto"].sum())

    st.divider()

    # ======================
    # EXPORT EXCEL
    # ======================
    def to_excel(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="dados")
        return output.getvalue()

    st.download_button(
        "📥 Exportar Excel",
        data=to_excel(filtrado),
        file_name="dashboard_operadoras.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.divider()

    # ======================
    # TABELA
    # ======================
    st.subheader("📋 Dados")

    st.dataframe(filtrado, use_container_width=True, hide_index=True)

else:
    st.info("Nenhum dado ainda cadastrado.")
