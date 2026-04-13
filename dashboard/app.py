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
# SUPABASE
# ======================
url = "https://whbwdmmgrylwehdarupk.supabase.co"
key = "sb_publishable_iU9EdbgP5pxbjxzTtxwmAg_6Vqw03uW"

supabase = create_client(url, key)

# ======================
# FUNÇÕES
# ======================
def get_data():
    response = supabase.table("registros").select("*").execute()
    if response.data:
        df = pd.DataFrame(response.data)

        # padroniza visual
        df.columns = [c.lower() for c in df.columns]

        return df

    return pd.DataFrame(columns=["id", "mes", "operadora", "circuit", "desconto"])


def insert_data(mes, operadora, circuit, desconto):
    supabase.table("registros").insert({
        "mes": mes,
        "operadora": operadora,
        "circuit": circuit,
        "desconto": desconto
    }).execute()


def delete_data(row_id):
    supabase.table("registros").delete().eq("id", row_id).execute()


# ======================
# INSERÇÃO
# ======================
st.subheader("➕ Novo Registro")

with st.form("form"):
    col1, col2, col3, col4 = st.columns(4)

    mes = col1.text_input("Mês")
    operadora = col2.text_input("Operadora")
    circuit = col3.text_input("Circuito")
    desconto = col4.number_input("Desconto", step=1.0)

    enviar = st.form_submit_button("Adicionar")

if enviar:
    if mes and operadora and circuit:
        insert_data(mes, operadora, circuit, float(desconto))
        st.success("Registro salvo!")
        st.rerun()
    else:
        st.error("Preencha todos os campos!")

# ======================
# CARREGA DADOS
# ======================
df = get_data()

if not df.empty:

    # ======================
    # FILTRO LIMPO
    # ======================
    st.sidebar.header("🔎 Filtros")

    mes_f = st.sidebar.selectbox("Mês", ["Todos"] + sorted(df["mes"].dropna().unique()))
    op_f = st.sidebar.selectbox("Operadora", ["Todas"] + sorted(df["operadora"].dropna().unique()))

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

    c1.metric("💰 Total", f"R$ {filtrado['desconto'].sum():,.2f}")
    c2.metric("📡 Registros", len(filtrado))
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
    # TABELA BONITA (SEM created_at)
    # ======================
    st.subheader("📋 Dados")

    view = filtrado[["id", "mes", "operadora", "circuit", "desconto"]]

    for i, row in view.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([1,2,2,2,2,1])

        col1.write(row["id"])
        col2.write(row["mes"])
        col3.write(row["operadora"])
        col4.write(row["circuit"])
        col5.write(row["desconto"])

        if col6.button("🗑️", key=f"del_{row['id']}"):
            delete_data(row["id"])
            st.rerun()

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

else:
    st.info("Nenhum dado cadastrado ainda.")
