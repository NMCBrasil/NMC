import streamlit as st
import pandas as pd
from io import BytesIO

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
            "Mês": mes,
            "Operadora": operadora,
            "Circuito": circuito,
            "Desconto": float(desconto)
        })
        st.success("Registro adicionado!")
    else:
        st.error("Preencha todos os campos!")

# ======================
# DATAFRAME (CORRIGIDO)
# ======================
df = pd.DataFrame(
    st.session_state.dados,
    columns=["Mês", "Operadora", "Circuito", "Desconto"]
)

# ======================
# FILTROS + DASHBOARD
# ======================
if not df.empty:

    st.sidebar.header("🔎 Filtros")

    mes_f = st.sidebar.selectbox(
        "Mês",
        ["Todos"] + sorted(df["Mês"].dropna().unique().tolist())
    )

    op_f = st.sidebar.selectbox(
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

    c1.metric("💰 Total Desconto", f"R$ {filtrado['Desconto'].sum():,.2f}")
    c2.metric("📡 Circuitos", len(filtrado))
    c3.metric("🏢 Operadoras", filtrado["Operadora"].nunique())

    st.divider()

    # ======================
    # GRÁFICOS
    # ======================
    st.subheader("📈 Gráficos")

    g1, g2 = st.columns(2)

    with g1:
        st.markdown("### Desconto por Operadora")
        st.bar_chart(filtrado.groupby("Operadora")["Desconto"].sum())

    with g2:
        st.markdown("### Desconto por Mês")
        st.line_chart(filtrado.groupby("Mês")["Desconto"].sum())

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
    # TABELA (ABAIXO DOS GRÁFICOS)
    # ======================
    st.subheader("📋 Dados Detalhados")

    st.dataframe(
        filtrado,
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("Nenhum dado cadastrado ainda.")
