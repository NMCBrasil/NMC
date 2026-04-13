import streamlit as st
import pandas as pd
from supabase import create_client

# ======================
# CONFIG GERAL
# ======================
st.set_page_config(
    page_title="Dashboard Operadoras",
    layout="wide"
)

st.title("📊 Dashboard de Operadoras")
st.caption("Visualização de circuitos, descontos e operadoras cadastradas no sistema.")

# ======================
# SUPABASE
# ======================
url = "https://whbwdmmgrylwehdarupk.supabase.co"
key = "sb_publishable_iU9EdbgP5pxbjxzTtxwmAg_6Vqw03uW"

supabase = create_client(url, key)

# ======================
# FUNÇÕES
# ======================
def load_data():
    res = supabase.table("registros").select("*").execute()

    if not res.data:
        return pd.DataFrame(columns=["id","mes","operadora","circuit","desconto"])

    df = pd.DataFrame(res.data)
    df.columns = df.columns.str.lower()

    if "created_at" in df.columns:
        df = df.drop(columns=["created_at"])

    if "circuito" in df.columns and "circuit" not in df.columns:
        df["circuit"] = df["circuito"]

    return df


def delete_row(row_id):
    supabase.table("registros").delete().eq("id", row_id).execute()


def insert_row(mes, operadora, circuit, desconto):
    supabase.table("registros").insert({
        "mes": mes,
        "operadora": operadora,
        "circuit": circuit,
        "desconto": desconto
    }).execute()

# ======================
# CADASTRO
# ======================
st.header("➕ Cadastro de novos registros")
st.write("Preencha os campos abaixo para adicionar um novo circuito ao sistema.")

with st.container():
    c1, c2, c3, c4 = st.columns(4)

    mes = c1.text_input("📅 Mês (ex: Janeiro)")
    operadora = c2.text_input("📡 Operadora")
    circuit = c3.text_input("🔌 Circuito")
    desconto = c4.number_input("💰 Desconto", step=1.0)

    if st.button("Salvar registro"):
        if mes and operadora and circuit:
            insert_row(mes, operadora, circuit, float(desconto))
            st.success("Registro salvo com sucesso!")
            st.rerun()
        else:
            st.error("Preencha todos os campos")

st.divider()

# ======================
# DADOS
# ======================
df = load_data()

if df.empty:
    st.warning("Nenhum dado cadastrado ainda.")
    st.stop()

# ======================
# FILTROS
# ======================
st.sidebar.header("🔎 Filtros do Dashboard")
st.sidebar.write("Use os filtros abaixo para refinar a visualização.")

mes_f = st.sidebar.selectbox("Filtrar por mês", ["Todos"] + sorted(df["mes"].dropna().unique()))
op_f = st.sidebar.selectbox("Filtrar por operadora", ["Todas"] + sorted(df["operadora"].dropna().unique()))

filtered = df.copy()

if mes_f != "Todos":
    filtered = filtered[filtered["mes"] == mes_f]

if op_f != "Todas":
    filtered = filtered[filtered["operadora"] == op_f]

# ======================
# KPIs
# ======================
st.header("📌 Indicadores gerais")

c1, c2, c3 = st.columns(3)

c1.metric("💰 Total em descontos", f"R$ {filtered['desconto'].sum():,.2f}")
c2.metric("📄 Total de registros", len(filtered))
c3.metric("🏢 Operadoras ativas", filtered["operadora"].nunique())

st.caption("Esses indicadores mostram o resumo geral dos dados filtrados.")

st.divider()

# ======================
# GRÁFICOS
# ======================
st.header("📊 Análise visual")

c1, c2 = st.columns(2)

with c1:
    st.subheader("Desconto por operadora")
    st.bar_chart(filtered.groupby("operadora")["desconto"].sum())

with c2:
    st.subheader("Desconto por mês")
    st.line_chart(filtered.groupby("mes")["desconto"].sum())

st.divider()

# ======================
# TABELA
# ======================
st.header("📋 Dados detalhados")
st.write("Lista completa dos registros filtrados. Você pode excluir qualquer item.")

for _, row in filtered.iterrows():

    c1, c2, c3, c4, c5 = st.columns([1,2,2,2,1])

    c1.write(f"🆔 {row.get('id','')}")
    c2.write(f"📅 {row.get('mes','')}")
    c3.write(f"📡 {row.get('operadora','')}")
    c4.write(f"🔌 {row.get('circuit', row.get('circuito','N/A'))}")
    c5.write(f"💰 {row.get('desconto',0)}")

    if c5.button("🗑️", key=f"del_{row.get('id')}"):
        delete_row(row["id"])
        st.rerun()
