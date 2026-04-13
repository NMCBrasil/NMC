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
    res = supabase.table("registros").select("*").execute()

    if not res.data:
        return pd.DataFrame(columns=["id", "mes", "operadora", "circuit", "desconto"])

    df = pd.DataFrame(res.data)
    df.columns = df.columns.str.lower()

    if "created_at" in df.columns:
        df = df.drop(columns=["created_at"])

    if "circuito" in df.columns and "circuit" not in df.columns:
        df["circuit"] = df["circuito"]

    return df


def delete_data(row_id):
    supabase.table("registros").delete().eq("id", row_id).execute()


def insert_data(mes, operadora, circuit, desconto):
    supabase.table("registros").insert({
        "mes": mes,
        "operadora": operadora,
        "circuit": circuit,
        "desconto": desconto
    }).execute()


# ======================
# FORM
# ======================
st.subheader("➕ Novo Registro")

with st.form("form"):
    c1, c2, c3, c4 = st.columns(4)

    mes = c1.text_input("Mês")
    operadora = c2.text_input("Operadora")
    circuit = c3.text_input("Circuito")
    desconto = c4.number_input("Desconto", step=1.0)

    submit = st.form_submit_button("Salvar")

if submit:
    if mes and operadora and circuit:
        insert_data(mes, operadora, circuit, float(desconto))
        st.success("Salvo com sucesso!")
        st.rerun()
    else:
        st.error("Preencha todos os campos")


# ======================
# LOAD
# ======================
df = get_data()

if not df.empty:

    st.subheader("📋 Dados")

    # filtros simples
    colf1, colf2 = st.columns(2)

    with colf1:
        mes_f = st.selectbox("Filtrar Mês", ["Todos"] + sorted(df["mes"].unique()))

    with colf2:
        op_f = st.selectbox("Filtrar Operadora", ["Todas"] + sorted(df["operadora"].unique()))

    filtrado = df.copy()

    if mes_f != "Todos":
        filtrado = filtrado[filtrado["mes"] == mes_f]

    if op_f != "Todas":
        filtrado = filtrado[filtrado["operadora"] == op_f]

    # ======================
    # TABELA BONITA (STREAMLIT STYLE)
    # ======================
    show = filtrado[["id", "mes", "operadora", "circuit", "desconto"]]

    st.dataframe(
        show,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### 🗑️ Remover registro")

    for _, row in show.iterrows():
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
    # EXPORT
    # ======================
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button(
        "📥 Exportar Excel",
        data=to_excel(show),
        file_name="dados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Nenhum dado cadastrado.")
