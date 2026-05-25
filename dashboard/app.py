import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ✅ conexão Supabase (via API)
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ buscar dados
response = supabase.table("incidentes").select("*").execute()
df = pd.DataFrame(response.data)

# ✅ garantir que tem dados antes de processar
if df.empty:
    st.warning("Sem dados na tabela 'incidentes'")
    st.stop()

# ✅ converter datas
df["data_inicio_evento"] = pd.to_datetime(df["data_inicio_evento"])
df["data_fim_evento"] = pd.to_datetime(df["data_fim_evento"])

# ✅ calcular downtime (em minutos)
df["down_time"] = (
    df["data_fim_evento"] - df["data_inicio_evento"]
).dt.total_seconds() / 60

# ✅ configuração da página
st.set_page_config(page_title="Dashboard Circuitos", layout="wide")

st.title("📊 Dashboard de Circuitos")

# =========================
# 🔹 KPIs
# =========================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("⛔ Total Downtime (min)", round(df["down_time"].sum(), 2))

with col2:
    top_operadora = df.groupby("operadora")["down_time"].sum().idxmax()
    st.metric("🔥 Maior Ofensora", top_operadora)

with col3:
    total_incidentes = len(df)
    st.metric("📉 Total Incidentes", total_incidentes)

# =========================
# 🔹 Ranking Operadoras
# =========================

st.subheader("📡 Ranking de Operadoras")

operadoras = (
    df.groupby("operadora")["down_time"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(operadoras)

# =========================
# 🔹 Top Circuitos
# =========================

st.subheader("🚨 Circuitos mais problemáticos")

circuitos = (
    df.groupby("id_circuito")["down_time"]
    .sum()
    .sort_values(ascending=False)
)

st.dataframe(circuitos, use_container_width=True)

# =========================
# 🔹 Tabela completa
# =========================

st.subheader("📋 Lista de Incidentes")

st.dataframe(df, use_container_width=True)
