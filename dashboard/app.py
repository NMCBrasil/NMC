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
    res = supabase.table("registros").select("*").execute()

    if res.data:
        df = pd.DataFrame(res.data)

        # padroniza tudo
        df.columns = df.columns.str.lower()

        # remove created_at se existir
        if "created_at" in df.columns:
            df = df.drop(columns=["created_at"])

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
# FORMULÁRIO
# ======================
st.subheader("➕ Adicionar Registro")

with st.form("form"):
    c1, c2, c3, c4 = st.columns(4)

    mes = c1.text_input("Mês")
    operadora = c2.text_input("Operadora")
    circuit = c3.text_input("Circuito")
    desconto = c4.number_input("Desconto", step=1.0)

    submit = st.form_submit_button("Adicionar")

if submit:
    if mes and operadora and circuit:
        insert_data(mes, operadora, circuit, float(desconto))
        st.success("Salvo com sucesso!")
        st.rerun()
    else:
        st.error("Preencha todos os campos")


# ======================
# CARREGAR DADOS
# ======================
df = get_data()

if not df.empty:

    # ======================
    # FILTROS
    # ======================
    st.sidebar.header("🔎 Filtros")

    mes_f = st.sidebar.selectbox("Mês", ["Todos"] + sorted(df["mes"].dropna().unique().tolist()))
    op_f = st.sidebar.selectbox("Operadora", ["Todas"] + sorted(df["operadora"].dropna().unique().tolist()))

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
    # TABELA + DELETE (BLINDADA)
    # ======================
    st.subheader("📋 Dados")

    cols = ["id", "mes", "operadora", "circuit", "desconto"]
    view = filtrado[[c for c in cols if c in filtrado.columns]]

    for i, row in view.iterrows():

        c1, c2, c3, c4, c5, c6 = st.columns([1,2,2,2,2,1])

        c1.write(row.get("id", ""))
        c2.write(row.get("mes", ""))
        c3.write(row.get("operadora", ""))
        c4.write(row.get("circuit", ""))
        c5.write(row.get("desconto", ""))

        if c6.button("🗑️", key=f"del_{row.get('id')}"):
            delete_data(row.get("id"))
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
