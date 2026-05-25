import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(
    page_title="Dashboard Circuitos",
    layout="wide"
)

st.title("📊 Dashboard de Circuitos")

# ==================================================
# CONEXÃO SUPABASE
# ==================================================
supabase_url = st.secrets["supabase_url"]
supabase_key = st.secrets["supabase_key"]

supabase = create_client(supabase_url, supabase_key)

# ==================================================
# CACHE
# ==================================================
@st.cache_data(ttl=300)
def carregar_dados():

    response = (
        supabase
        .table("incidentes")
        .select("*")
        .execute()
    )

    return pd.DataFrame(response.data)

# ==================================================
# FORMULÁRIO NOVO INCIDENTE
# ==================================================
st.subheader("➕ Adicionar Incidente")

with st.form("novo_incidente"):

    col1, col2 = st.columns(2)

    with col1:
        id_circuito = st.text_input("Circuito")

        operadora = st.selectbox(
            "Operadora",
            [
                "Claro",
                "Vivo",
                "TIM",
                "Oi",
                "Algar",
                "Hughes",
                "Outros"
            ]
        )

        data_inicio = st.datetime_input("Início da Falha")

    with col2:
        data_fim = st.datetime_input("Fim da Falha")

        status = st.selectbox(
            "Status",
            [
                "Aberto",
                "Encerrado"
            ]
        )

        observacao = st.text_area("Observação")

    enviar = st.form_submit_button("Salvar Incidente")

    if enviar:

        try:

            dados = {
                "id_circuito": id_circuito,
                "operadora": operadora,
                "data_inicio_evento": str(data_inicio),
                "data_fim_evento": (
                    str(data_fim)
                    if status == "Encerrado"
                    else None
                ),
                "status": status,
                "observacao": observacao
            }

            (
                supabase
                .table("incidentes")
                .insert(dados)
                .execute()
            )

            st.success("✅ Incidente cadastrado com sucesso!")

            st.cache_data.clear()

        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# ==================================================
# CARREGAR DADOS
# ==================================================
try:

    df = carregar_dados()

    if df.empty:
        st.warning("Sem dados cadastrados.")
        st.stop()

except Exception as e:

    st.error("Erro ao acessar Supabase")
    st.write(e)
    st.stop()

# ==================================================
# TRATAMENTO DE DATAS
# ==================================================
df["data_inicio_evento"] = pd.to_datetime(
    df["data_inicio_evento"],
    errors="coerce"
)

df["data_fim_evento"] = pd.to_datetime(
    df["data_fim_evento"],
    errors="coerce"
)

# ==================================================
# DOWNTIME
# ==================================================
df["down_time"] = (
    df["data_fim_evento"].fillna(pd.Timestamp.now())
    - df["data_inicio_evento"]
).dt.total_seconds() / 60

# ==================================================
# SIDEBAR FILTROS
# ==================================================
st.sidebar.header("🔍 Filtros")

operadora_filtro = st.sidebar.multiselect(
    "Operadora",
    options=df["operadora"].dropna().unique(),
    default=df["operadora"].dropna().unique()
)

status_filtro = st.sidebar.multiselect(
    "Status",
    options=df["status"].dropna().unique(),
    default=df["status"].dropna().unique()
)

df = df[
    (df["operadora"].isin(operadora_filtro))
    &
    (df["status"].isin(status_filtro))
]

# ==================================================
# KPIs
# ==================================================
st.subheader("📈 Indicadores")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "⛔ Downtime Total (min)",
        round(df["down_time"].sum(), 2)
    )

with col2:

    if not df.empty:
        top_operadora = (
            df.groupby("operadora")["down_time"]
            .sum()
            .idxmax()
        )

        st.metric(
            "🔥 Maior Ofensora",
            top_operadora
        )

with col3:
    st.metric(
        "📉 Total Incidentes",
        len(df)
    )

with col4:

    abertos = df[
        df["status"] == "Aberto"
    ]

    st.metric(
        "🟢 Incidentes Abertos",
        len(abertos)
    )

# ==================================================
# RANKING OPERADORAS
# ==================================================
st.subheader("📡 Ranking de Operadoras")

operadoras = (
    df.groupby("operadora")["down_time"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

fig = px.bar(
    operadoras,
    x="operadora",
    y="down_time",
    title="Downtime por Operadora",
    labels={
        "operadora": "Operadora",
        "down_time": "Downtime (min)"
    }
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==================================================
# CIRCUITOS MAIS PROBLEMÁTICOS
# ==================================================
st.subheader("🚨 Circuitos Mais Problemáticos")

circuitos = (
    df.groupby("id_circuito")["down_time"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

st.dataframe(
    circuitos,
    use_container_width=True
)

# ==================================================
# LISTA COMPLETA
# ==================================================
st.subheader("📋 Lista de Incidentes")

st.dataframe(
    df.sort_values(
        by="data_inicio_evento",
        ascending=False
    ),
    use_container_width=True
)
