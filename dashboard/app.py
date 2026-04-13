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
# DADOS
# ======================
def get_data():
    response = supabase.table("registros").select("*").execute()

    if response.data:
        df = pd.DataFrame(response.data)

        # remove created_at se existir
        if "created_at" in df.columns:
            df = df.drop(columns=["created_at"])

        return df

    return pd.DataFrame(columns=["id", "mes", "operadora", "circuit", "desconto"])


# ======================
# INSERT
# ======================
def insert_data(mes, operadora, circuit, desconto):
    supabase.table("registros").insert({
        "mes": mes,
        "operadora": operadora,
        "circuit": circuit,
        "desconto": desconto
    }).execute()


# ======================
# DELETE
# ======================
def delete_data(row_id):
    supabase.table("registros").delete().eq("id", row_id).execute()


# ======================
# FORM
# ======================
st.subheader("➕ Adicionar Registro")

with st.form("form"):
    col1, col2, col3, col4 = st.columns(4)

    mes = col1.text_input("Mês")
    operadora = col2.text_input("Operadora")
    circuit = col3.text_input("Circuito")
    desconto = col4.number_input("Desconto", step=1.0)

    submit = st.form_submit_button("Adicionar")

if submit:
    if mes and operadora and circuit:
        insert_data(mes, operadora, circuit, float(desconto))
        st.success("Registro adicionado!")
        st.rerun()
    else:
        st.error("Preencha todos os campos!")

# ======================
# LOAD
# ======================
df = get_data()

if not df.empty:

    # ======================
    # FILTROS
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
    # TABELA + DELETE
    # ======================
    st.subheader("📋 Dados")

    for i, row in filtrado.iterrows():
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
