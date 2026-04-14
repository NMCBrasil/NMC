import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date
from pathlib import Path

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Dashboard Operadoras", layout="wide")

# ======================
# 🎨 TEMA (AJUSTADO FINAL)
# ======================
st.markdown("""
    <style>
        .stApp {
            background-color: #9fc5f8;
            color: black;
        }

        * {
            color: black !important;
        }

        h1, h2, h3 {
            color: black !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #8dbaf5;
        }

        /* BOTÕES */
        .stButton > button {
            background-color: #ff6a00 !important;
            color: white !important;
            border-radius: 8px;
            border: none;
        }

        .stButton > button:hover {
            background-color: #e65c00 !important;
        }

        /* INPUTS */
        .stTextInput input, .stNumberInput input {
            background-color: #9fc5f8 !important;
            color: black !important;
        }

        /* SELECT */
        div[data-baseweb="select"] > div {
            background-color: #9fc5f8 !important;
            color: black !important;
        }

        /* SETAS DO NUMBER INPUT */
        button[title="Increment"], 
        button[title="Decrement"] {
            background-color: #9fc5f8 !important;
            color: black !important;
        }

        /* GRÁFICOS */
        canvas {
            background-color: #9fc5f8 !important;
        }

        /* KPI */
        div[data-testid="metric-container"] {
            background-color: #9fc5f8;
            border-radius: 10px;
            padding: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# ======================
# HEADER
# ======================
col_logo, col_title = st.columns([1,6])

with col_logo:
    logo_path = Path(__file__).parent / "logo.png"
    st.image(str(logo_path), width=120)

with col_title:
    st.title("Dashboard de Operadoras")
    st.markdown("<h3>Controle de descontos por circuito</h3>", unsafe_allow_html=True)

st.divider()

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
        return pd.DataFrame(columns=["id","mes","operadora","circuito","desconto"])

    df = pd.DataFrame(res.data)
    df.columns = df.columns.str.lower()
    df["mes_dt"] = pd.to_datetime(df["mes"], format="%Y-%m", errors="coerce")
    return df

# ======================
# INSERT
# ======================
def insert_row(mes, operadora, circuito, desconto):
    res = supabase.table("registros").insert({
        "mes": mes,
        "operadora": operadora,
        "circuito": circuito,
        "desconto": desconto
    }).execute()
    return bool(res.data)

# ======================
# DELETE
# ======================
def delete_row(row_id):
    supabase.table("registros").delete().eq("id", row_id).execute()

# ======================
# FORM
# ======================
st.subheader("➕ Novo Registro")

with st.form("form", clear_on_submit=True):

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    col_mes, col_ano = c1.columns(2)

    today = date.today()

    mes_num = col_mes.selectbox("Mês", list(range(1, 13)), index=today.month - 1, format_func=lambda x: f"{x:02d}")
    anos = list(range(2024, 2031))
    ano = col_ano.selectbox("Ano", anos, index=anos.index(today.year))

    mes = f"{ano}-{mes_num:02d}"

    operadora = c2.text_input("Operadora")
    circuito = c3.text_input("Circuito")
    desconto = c4.number_input("Desconto (R$)", min_value=0.0)

    submit = st.form_submit_button("Salvar")

    if submit:
        if operadora and circuito:
            if insert_row(mes, operadora, circuito, float(desconto)):
                st.success("Registro salvo")
                st.rerun()
        else:
            st.error("Preencha todos os campos")

st.divider()

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
st.subheader("📊 Indicadores")

c1, c2, c3 = st.columns(3)

c1.metric("Total (R$)", f"{filtered['desconto'].sum():,.2f}")
c2.metric("Registros", len(filtered))
c3.metric("Operadoras", filtered["operadora"].nunique())

st.divider()

# ======================
# GRÁFICOS
# ======================
st.subheader("📈 Análise")

g1, g2 = st.columns(2)

with g1:
    st.markdown("**Por Operadora**")
    st.bar_chart(filtered.groupby("operadora")["desconto"].sum())

with g2:
    st.markdown("**Evolução Mensal**")
    evolucao = (
        filtered.dropna(subset=["mes_dt"])
        .groupby("mes_dt")["desconto"]
        .sum()
        .sort_index()
    )
    st.line_chart(evolucao)

st.divider()

# ======================
# REGISTROS
# ======================
st.subheader("📋 Registros")

filtered = filtered.sort_values("mes_dt", ascending=False)

h1, h2, h3, h4, h5 = st.columns([2,2,3,2,1])

h1.markdown("**Mês/Ano**")
h2.markdown("**Operadora**")
h3.markdown("**Circuito**")
h4.markdown("**Valor (R$)**")
h5.markdown("")

st.divider()

for _, row in filtered.iterrows():
    c1, c2, c3, c4, c5 = st.columns([2,2,3,2,1])

    mes_formatado = row["mes_dt"].strftime("%m/%Y") if pd.notna(row["mes_dt"]) else row["mes"]

    c1.write(mes_formatado)
    c2.write(row["operadora"])
    c3.write(row["circuito"])
    c4.write(f"R$ {row['desconto']:.2f}")

    if c5.button("🗑️", key=f"del_{row['id']}"):
        delete_row(row["id"])
        st.rerun()
