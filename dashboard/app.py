import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Operadoras", layout="wide")

st.title("Dashboard Operadoras 🚀")

# ======================
# DADOS (sessão)
# ======================
if "dados" not in st.session_state:
    st.session_state.dados = []

# ======================
# ADICIONAR REGISTRO
# ======================
st.header("Adicionar Registro")

with st.form("form"):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mes = st.text_input("Mês")
    with col2:
        operadora = st.text_input("Operadora")
    with col3:
        circuito = st.text_input("Circuito")
    with col4:
        desconto = st.number_input("Desconto", step=1.0)

    enviar = st.form_submit_button("Adicionar")

if enviar:
    if mes and operadora and circuito:
        st.session_state.dados.append({
            "mes": mes,
            "operadora": operadora,
            "circuito": circuito,
            "desconto": float(desconto)
        })
        st.success("Registro adicionado!")
    else:
        st.error("Preencha todos os campos!")

# ======================
# DATAFRAME
# ======================
df = pd.DataFrame(st.session_state.dados)

# ======================
# FILTROS
# ======================
if not df.empty:
    st.sidebar.header("Filtros")

    mes_f = st.sidebar.selectbox("Mês", ["Todos"] + sorted(df["mes"].unique().tolist()))
    op_f = st.sidebar.selectbox("Operadora", ["Todas"] + sorted(df["operadora"].unique().tolist()))

    filtrado = df.copy()

    if mes_f != "Todos":
        filtrado = filtrado[filtrado["mes"] == mes_f]

    if op_f != "Todas":
        filtrado = filtrado[filtrado["operadora"] == op_f]

    # ======================
    # KPIs
    # ======================
    st.subheader("Resumo")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Desconto", f"R$ {filtrado['desconto'].sum():,.2f}")
    col2.metric("Circuitos", len(filtrado))
    col3.metric("Operadoras", filtrado["operadora"].nunique())

    # ======================
    # TABELA
    # ======================
    st.subheader("Tabela")

    st.dataframe(filtrado, use_container_width=True)

    # ======================
    # GRÁFICOS
    # ======================
    st.subheader("Gráficos")

    st.bar_chart(filtrado.groupby("operadora")["desconto"].sum())

    st.line_chart(filtrado.groupby("mes")["desconto"].sum())

else:
    st.info("Nenhum dado cadastrado ainda.")
