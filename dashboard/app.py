import streamlit as st
import pandas as pd
from supabase import create_client

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Dashboard Operadoras", layout="wide")

st.title("📊 Dashboard de Operadoras")
st.caption("Controle de descontos por circuito e operadora")

# ======================
# SUPABASE
# ======================
url = "https://whbwdmmgrylwehdarupk.supabase.co"
key = "sb_publishable_iU9EdbgP5pxbjxzTtxwmAg_6Vqw03uW"

supabase = create_client(url, key)

# ======================
# LOAD DATA
# ======================
def load_data():
    res = supabase.table("registros").select("*").execute()

    if not res.data:
        return pd.DataFrame(columns=["id", "mes", "operadora", "circuito", "desconto", "created_at"])

    df = pd.DataFrame(res.data)
    df.columns = df.columns.str.lower()

    # Converter mês
    df["mes_dt"] = pd.to_datetime(df["mes"], format="%Y-%m", errors="coerce")

    # Converter created_at
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    return df


# ======================
# INSERT
# ======================
def insert_row(mes, operadora, circuito, desconto):
    try:
        res = supabase.table("registros").insert({
            "mes": mes,
            "operadora": operadora,
            "circuito": circuito,
            "desconto": desconto
        }).execute()

        return bool(res.data)

    except Exception as e:
        st.error(f"Erro ao inserir: {e}")
        return False


# ======================
# DELETE
# ======================
def delete_row(row_id):
    try:
        supabase.table("registros").delete().eq("id", row_id).execute()
        st.toast("Registro excluído com sucesso")
    except Exception as e:
        st.error(f"Erro ao excluir: {e}")


# ======================
# FORM
# ======================
st.subheader("➕ Novo Registro")

with st.form("form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    mes = c1.text_input("📅 Mês (YYYY-MM)", placeholder="Ex: 2026-02")
    operadora = c2.text_input("📡 Operadora")

    circuito = c3.text_input("🔌 Circuito")
    desconto = c4.number_input("💰 Desconto (R$)", min_value=0.0)

    submit = st.form_submit_button("💾 Salvar")

    if submit:
        if mes and operadora and circuito:
            ok = insert_row(mes, operadora, circuito, float(desconto))

            if ok:
                st.success("✅ Registro salvo!")
                st.rerun()
        else:
            st.error("Preencha todos os campos")


# ======================
# DATA
# ======================
df = load_data()

if df.empty:
    st.warning("Nenhum dado cadastrado.")
    st.stop()

# ======================
# FILTROS
# ======================
with st.sidebar:
    st.markdown("### 🔎 Filtros")

    mes_f = st.selectbox("Mês", ["Todos"] + sorted(df["mes"].dropna().unique()))
    op_f = st.selectbox("Operadora", ["Todas"] + sorted(df["operadora"].dropna().unique()))

filtered = df.copy()

if mes_f != "Todos":
    filtered = filtered[filtered["mes"] == mes_f]

if op_f != "Todas":
    filtered = filtered[filtered["operadora"] == op_f]

# ======================
# KPIs
# ======================
st.subheader("📌 Indicadores")

c1, c2, c3 = st.columns(3)

c1.metric("💰 Total", f"R$ {filtered['desconto'].sum():,.2f}")
c2.metric("📄 Registros", len(filtered))
c3.metric("🏢 Operadoras", filtered["operadora"].nunique())

st.divider()

# ======================
# GRÁFICOS
# ======================
st.subheader("📊 Análise")

c1, c2 = st.columns(2)

c1.markdown("**Descontos por Operadora**")
c1.bar_chart(filtered.groupby("operadora")["desconto"].sum())

c2.markdown("**Evolução por Mês**")

chart_data = (
    filtered.dropna(subset=["mes_dt"])
    .sort_values("mes_dt")
    .groupby("mes_dt")["desconto"]
    .sum()
)

c2.line_chart(chart_data)

st.divider()

# ======================
# TABELA ORDENADA + DATA + DELETE
# ======================
st.subheader("📋 Registros")

# 🔥 Ordenar por operadora (A-Z)
filtered = filtered.sort_values("operadora")

for i, row in filtered.iterrows():
    col1, col2, col3, col4, col5, col6 = st.columns([2,2,3,2,3,1])

    col1.write(row["mes"])
    col2.write(row["operadora"])
    col3.write(row["circuito"])
    col4.write(f"R$ {row['desconto']:.2f}")

    # Mostrar data/hora formatada
    if pd.notna(row.get("created_at")):
        data_formatada = row["created_at"].strftime("%d/%m/%Y %H:%M")
        col5.write(data_formatada)
    else:
        col5.write("-")

    if col6.button("🗑️", key=f"del_{row['id']}"):
        delete_row(row["id"])
        st.rerun()
