import streamlit as st
import pandas as pd
from supabase import create_client

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

    # GARANTE COMPATIBILIDADE
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
with st.expander("➕ Adicionar registro"):
    c1, c2, c3, c4 = st.columns(4)

    mes = c1.text_input("Mês")
    operadora = c2.text_input("Operadora")
    circuit = c3.text_input("Circuito")
    desconto = c4.number_input("Desconto", step=1.0)

    if st.button("Salvar"):
        insert_data(mes, operadora, circuit, float(desconto))
        st.rerun()


# ======================
# LOAD DATA
# ======================
df = get_data()

if df.empty:
    st.warning("Sem dados cadastrados.")
    st.stop()

# ======================
# FILTROS
# ======================
st.sidebar.header("🔎 Filtros")

mes_f = st.sidebar.selectbox("Mês", ["Todos"] + sorted(df["mes"].dropna().unique()))
op_f = st.sidebar.selectbox("Operadora", ["Todas"] + sorted(df["operadora"].dropna().unique()))

filtered = df.copy()

if mes_f != "Todos":
    filtered = filtered[filtered["mes"] == mes_f]

if op_f != "Todas":
    filtered = filtered[filtered["operadora"] == op_f]

# ======================
# KPIs
# ======================
c1, c2, c3 = st.columns(3)

c1.metric("💰 Total", f"R$ {filtered['desconto'].sum():,.2f}")
c2.metric("📄 Registros", len(filtered))
c3.metric("🏢 Operadoras", filtered["operadora"].nunique())

st.divider()

# ======================
# GRÁFICOS
# ======================
c1, c2 = st.columns(2)

c1.bar_chart(filtered.groupby("operadora")["desconto"].sum())
c2.line_chart(filtered.groupby("mes")["desconto"].sum())

st.divider()

# ======================
# TABELA LIMPA (SEM ERRO)
# ======================
st.subheader("📋 Dados")

for _, row in filtered.iterrows():

    c1, c2, c3, c4, c5 = st.columns([1.5,2,2,2,1])

    c1.write(row.get("id", ""))
    c2.write(row.get("mes", ""))
    c3.write(row.get("operadora", ""))

    # 🔥 AQUI ESTÁ O FIX REAL
    c4.write(row.get("circuit", row.get("circuito", "N/A")))

    c5.write(f"R$ {row.get('desconto', 0)}")

    if c5.button("🗑️", key=f"del_{row.get('id')}"):
        delete_data(row["id"])
        st.rerun()
