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
# DATA
# ======================
def get_data():
    res = supabase.table("registros").select("*").execute()
    if not res.data:
        return pd.DataFrame(columns=["id","mes","operadora","circuit","desconto"])

    df = pd.DataFrame(res.data)
    df.columns = df.columns.str.lower()

    if "created_at" in df.columns:
        df = df.drop(columns=["created_at"])

    if "circuito" in df.columns:
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
with st.container():
    st.subheader("➕ Adicionar")

    c1, c2, c3, c4 = st.columns(4)

    mes = c1.text_input("Mês")
    operadora = c2.text_input("Operadora")
    circuit = c3.text_input("Circuito")
    desconto = c4.number_input("Desconto", step=1.0)

    if st.button("Salvar"):
        if mes and operadora and circuit:
            insert_data(mes, operadora, circuit, float(desconto))
            st.success("Salvo!")
            st.rerun()

# ======================
# LOAD
# ======================
df = get_data()

if df.empty:
    st.warning("Sem dados ainda.")
    st.stop()

# ======================
# FILTROS LIMPOS (SIDEBAR)
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
# KPIs (CARDS LIMPOS)
# ======================
c1, c2, c3 = st.columns(3)

c1.metric("💰 Total", f"R$ {filtrado['desconto'].sum():,.2f}")
c2.metric("📄 Registros", len(filtrado))
c3.metric("🏢 Operadoras", filtrado["operadora"].nunique())

st.divider()

# ======================
# GRÁFICOS
# ======================
c1, c2 = st.columns(2)

c1.bar_chart(filtrado.groupby("operadora")["desconto"].sum())
c2.line_chart(filtrado.groupby("mes")["desconto"].sum())

st.divider()

# ======================
# TABELA LIMPA (SÓ UMA)
# ======================
st.subheader("📋 Dados")

show = filtrado[["id","mes","operadora","circuit","desconto"]]

st.dataframe(show, use_container_width=True, hide_index=True)

# ======================
# DELETE (SEM BAGUNÇA)
# ======================
st.subheader("🗑️ Remover")

for _, row in show.iterrows():
    col1, col2, col3 = st.columns([6,4,1])

    col1.write(f"{row['id']} - {row['mes']} - {row['operadora']} - {row['circuit']} - R$ {row['desconto']}")

    if col3.button("🗑️", key=row["id"]):
        delete_data(row["id"])
        st.rerun()
