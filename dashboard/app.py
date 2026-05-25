import streamlit as st
import pandas as pd
from supabase import create_client

# ==========================
# 🔹 Config
# ==========================
st.set_page_config(page_title="Dashboard Circuitos", layout="wide")
st.title("📊 Dashboard de Circuitos")

# ==========================
# 🔹 Conexão
# ==========================
supabase_url = st.secrets["supabase_url"]
supabase_key = st.secrets["supabase_key"]

supabase = create_client(supabase_url, supabase_key)

# ==========================
# 🔹 Buscar dados (FORMA CORRETA)
# ==========================
try:
    response = supabase.table("incidentes").select("*").execute()

    if not response.data:
        st.warning("Sem dados retornados ou acesso negado.")
        st.stop()

    df = pd.DataFrame(response.data)

except Exception as e:
    st.error("Erro ao acessar o Supabase")
    st.write(e)
    st.stop()

# ==========================
# 🔹 Conversão de dados
# ==========================
df["data_inicio_evento"] = pd.to_datetime(df["data_inicio_evento"])
df["data_fim_evento"] = pd.to_datetime(df["data_fim_evento"])

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

operadoras = df.groupby("operadora")["down_time"].sum().sort_values(ascending=False)
st.bar_chart(operadoras)

# ==========================
# 🔹 Circuitos problemáticos
# ==========================
st.subheader("🚨 Circuitos mais problemáticos")

circuitos = df.groupby("id_circuito")["down_time"].sum().sort_values(ascending=False)
st.dataframe(circuitos, use_container_width=True)

# ==========================
# 🔹 Tabela completa
# ==========================
st.subheader("📋 Lista de Incidentes")
st.dataframe(df, use_container_width=True)
