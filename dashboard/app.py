import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Operadoras", layout="wide")

st.title("📊 Dashboard Operadoras")

# ======================
# ESTADO
# ======================
if "dados" not in st.session_state:
    st.session_state.dados = []

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
        st.session_state.dados.append({
            "mes": mes,
            "operadora": operadora,
            "circuito": circuito,
            "desconto": float(desconto)
        })
        st.success("Registro adicionado!")
    else:
        st.error("Preencha todos os campos!")

df = pd.DataFrame(st.session_state.dados)

# ======================
# FILTROS
# ======================
if not df.empty:
    st.sidebar.header("🔎 Filtros")

    mes_f = st.sidebar.selectbox("Mês", ["Todos"] + sorted(df["mes"].unique()))
    op_f = st.sidebar.selectbox("Operadora", ["Todas"] + sorted(df["operadora"].unique()))

    filtrado = df.copy()

    if mes_f != "Todos":
        filtrado = filtrado[filtrado["mes"] == mes_f]

    if op_f != "Todas":
        filtrado = filtrado[filtrado["operadora"] == op_f]

    # ======================
    # KPIs (BONITO)
    # ======================
    st.subheader("📌 Resumo")

    c1, c2, c3 = st.columns(3)

    c1.metric("💰 Total Desconto", f"R$ {filtrado['desconto'].sum():,.2f}")
    c2.metric("📡 Circuitos", len(filtrado))
    c3.metric("🏢 Operadoras", filtrado["operadora"].nunique())

    st.divider()

    # ======================
    # TABELA COM DELETE
    # ======================
    st.subheader("📋 Dados")

    for i, row in filtrado.reset_index().iterrows():
        col1, col2, col3, col4, col5 = st.columns([2,2,2,2,1])

        col1.write(row["mes"])
        col2.write(row["operadora"])
        col3.write(row["circuito"])
        col4.write(f"R$ {row['desconto']:.2f}")

        if col5.button("🗑️", key=f"del_{i}"):
            st.session_state.dados.pop(row["index"])
            st.rerun()

    st.divider()

    # ======================
    # GRÁFICOS MELHORADOS
    # ======================
    st.subheader("📈 Gráficos")

    g1, g2 = st.columns(2)

    with g1:
        st.markdown("### Desconto por Operadora")
        st.bar_chart(filtrado.groupby("operadora")["desconto"].sum())

    with g2:
        st.markdown("### Desconto por Mês")
        st.line_chart(filtrado.groupby("mes")["desconto"].sum())

else:
    st.info("Nenhum dado cadastrado ainda.")
