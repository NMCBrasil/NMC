import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# conexão segura
db_url = st.secrets["db_url"]
engine = create_engine(db_url)

# query
query = """
SELECT 
    *,
    EXTRACT(EPOCH FROM (data_fim_evento - data_inicio_evento))/60 AS down_time
FROM incidentes
"""

df = pd.read_sql(query, engine)

st.title("📊 Dashboard de Circuitos")

# 🔥 KPIs
col1, col2 = st.columns(2)

with col1:
    st.metric("Total Downtime (min)", round(df["down_time"].sum(), 2))

with col2:
    st.metric(
        "Maior Ofensora",
        df.groupby("operadora")["down_time"].sum().idxmax()
    )

# 🔥 Ranking
st.subheader("Ranking de Operadoras")
operadoras = df.groupby("operadora")["down_time"].sum().sort_values(ascending=False)
st.bar_chart(operadoras)

# 🔥 Circuitos
st.subheader("Top Circuitos Problemáticos")
circuitos = df.groupby("id_circuito")["down_time"].sum().sort_values(ascending=False)
st.dataframe(circuitos)

# 🔥 Tabela completa
st.subheader("Incidentes")
st.dataframe(df)
