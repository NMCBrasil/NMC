import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Dashboard Operadoras", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

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
        df.columns = df.columns.str.lower()

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
# FORM
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
        st.success("Registro adicionado!")
        st.rerun()
    else:
        st.error("Preencha todos os campos!")


# ======================
# DADOS
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

    c1, c2 = st.columns(2)

    c1.bar_chart(filtrado.groupby("operadora")["desconto"].sum())
    c2.line_chart(filtrado.groupby("mes")["desconto"].sum())

    st.divider()

    # ======================
    # TABELA PROFISSIONAL
    # ======================
    st.subheader("📋 Dados")

    view = filtrado[["id", "mes", "operadora", "circuit", "desconto"]]

    st.dataframe(
        view,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### 🗑️ Deletar registros")

    header = st.columns([1,2,2,2,2,1])
    header[0].write("ID")
    header[1].write("Mês")
    header[2].write("Operadora")
    header[3].write("Circuito")
    header[4].write("Desconto")
    header[5].write("Ação")

    for _, row in view.iterrows():

        c1, c2, c3, c4, c5, c6 = st.columns([1,2,2,2,2,1])

        c1.write(row["id"])
        c2.write(row["mes"])
        c3.write(row["operadora"])
        c4.write(row["circuit"])
        c5.write(row["desconto"])

        if c6.button("🗑️", key=f"del_{row['id']}"):
            delete_data(row["id"])
            st.rerun()

    # ======================
    # EXPORT
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
