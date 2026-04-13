import streamlit as st
import pandas as pd
from supabase import create_client

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Dashboard Operadoras", layout="wide")

st.title("📊 Dashboard Operadoras")
st.caption("Gestão de circuitos, operadoras e descontos")

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
        return pd.DataFrame(columns=["id", "mes", "operadora", "circuito", "desconto"])

    df = pd.DataFrame(res.data)
    df.columns = df.columns.str.lower()

    if "created_at" in df.columns:
        df = df.drop(columns=["created_at"])

    return df


# ======================
# INSERT
# ======================
def insert_row(mes, operadora, circuito, desconto):
    try:
        supabase.table("registros").insert({
            "mes": mes,
            "operadora": operadora,
            "circuito": circuito,  # ✅ CORRETO
            "desconto": desconto
        }).execute()

    except Exception as e:
        st.error(f"Erro ao inserir: {e}")


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
st.header("➕ Adicionar registro")

with st.form("form"):
    c1, c2, c3, c4 = st.columns(4)

    mes = c1.text_input("Mês")
    operadora = c2.text_input("Operadora")
    circuito = c3.text_input("Circuito")  # nome alinhado com banco
    desconto = c4.number_input("Desconto", step=1.0, value=0.0)

    submit = st.form_submit_button("Salvar")

    if submit:
        if mes and operadora and circuito:
            insert_row(mes, operadora, circuito, float(desconto))
            st.success("Registro salvo!")
            st.rerun()
        else:
            st.error("Preencha todos os campos obrigatórios")


# ======================
# DATA
# ======================
df = load_data()

if df.empty:
    st.warning("Nenhum dado cadastrado.")
    st.stop()

# ======================
# FILTERS
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
st.subheader("📌 Resumo")

c1, c2, c3 = st.columns(3)

c1.metric("💰 Total", f"R$ {filtered['desconto'].sum():,.2f}")
c2.metric("📄 Registros", len(filtered))
c3.metric("🏢 Operadoras", filtered["operadora"].nunique())

st.divider()

# ======================
# GRÁFICOS
# ======================
st.subheader("📊 Visualização")

c1, c2 = st.columns(2)

c1.bar_chart(filtered.groupby("operadora")["desconto"].sum())

chart_data = filtered.groupby("mes", as_index=False)["desconto"].sum()
c2.line_chart(chart_data.set_index("mes"))

st.divider()

# ======================
# TABELA COM DELETE
# ======================
st.subheader("📋 Dados cadastrados")

for _, row in filtered.iterrows():

    row_id = row.get("id")

    if pd.isna(row_id):
        continue

    c_del, c1, c2, c3, c4 = st.columns([0.6, 1.5, 2, 2, 2])

    if c_del.button("🗑️", key=f"del_{row_id}"):
        delete_row(row_id)
        st.rerun()

    c1.write(f"🆔 {row_id}")
    c2.write(f"📅 {row.get('mes','')}")
    c3.write(f"📡 {row.get('operadora','')}")
    c4.write(f"🔌 {row.get('circuito','N/A')}")
