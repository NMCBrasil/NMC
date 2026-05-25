import streamlit as st
import pandas as pd
from supabase import create_client
from postgrest.exceptions import APIError

# ==========================
# 🔹 Conexão Supabase
# ==========================
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Dashboard Circuitos", layout="wide")

st.title("📊 Dashboard de Circuitos")

# ==========================
# 🔹 Buscar dados
# ==========================
try:
    response = supabase.table("incidentes").select("*").execute()
    data = response.data

except APIError as e:
    st.error("Erro ao acessar o Supabase (verifique RLS e permissões).")
    st.stop()

except Exception as e:
    st.error("Erro geral de conexão.")
    st.text(str(e))
    st.stop()

# ==========================
# 🔹 Verificar dados
# ==========================
if not data:
    st.warning("Tabela 'incidentes' está vazia ou sem acesso.")
    st.stop()

df = pd.DataFrame(data)

# ==========================
# 🔹 Converter datas
# ==========================
df["data_inicio_evento"] = pd.to_datetime(df["data_inicio_evento"])
df["data_fim_evento"] = pd.to_datetime(df["data_fim_evento"])

# ==========================
# 🔹 Calcular downtime
# ==========================
df["down_time"] = (
    df["data_fim_evento"] - df["data_inicio_evento"]
).dt.total_seconds() / 60

# ==========================
# 🔹 KPIs
# ==========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("⛔ Total Downtime (min)", round(df["down_time"].sum(), 2))

with col2:
    top_operadora = df.groupby("operadora")["down_time"].sum().idxmax()
    st.metric("🔥 Maior Ofensora", top_operadora)

with col3:
    st.metric("📉 Total Incidentes", len(df))

# ==========================
# 🔹 Ranking Operadoras
# ==========================
st.subheader("📡 Ranking de Operadoras")

operadoras = (
    df.groupby("operadora")["down_time"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(operadoras)

# ==========================
# 🔹 Circuitos mais problemáticos
# ==========================
st.subheader("🚨 Circuitos mais problemáticos")

circuitos = (
    df.groupby("id_circuito")["down_time"]
    .sum()
    .sort_values(ascending=False)
)

st.dataframe(circuitos, use_container_width=True)

# ==========================
# 🔹 Lista completa
# ==========================
st.subheader("📋 Lista de Incidentes")

st.dataframe(df, use_container_width=True)
``
