import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Dashboard Operadoras", layout="wide")

st.title("📊 Dashboard de Operadoras")
st.caption("Controle de descontos por circuito")

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

    # Converter mês corretamente
    df["mes_dt"] = pd.to_datetime(df["mes"], format="%Y-%m", errors="coerce")

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
    supabase.table("registros").delete().eq("id", row_id).execute()


# ======================
# FORM
# ======================
st.subheader("➕ Novo Registro")

with st.form("form", clear_on_submit=True):

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    # 🔥 MÊS + ANO OBRIGATÓRIO
    col_mes, col_ano = c1.columns(2)

    today = date.today()

    mes_num = col_mes.selectbox(
        "Mês",
        list(range(1, 13)),
        index=today.month - 1,
        format_func=lambda x: f"{x:02d}"
    )

    anos = list(range(2024, 2031))
    ano = col_ano.selectbox(
        "Ano",
        anos,
        index=anos.index(today.year)
    )

    # formato correto pro banco
    mes = f"{ano}-{mes_num:02d}"

    operadora = c2.text_input("📡 Operadora")
    circuito = c3.text_input("🔌 Circuito")
    desconto = c4.number_input("💰 Desconto (R$)", min_value=0.0)

    submit = st.form_submit_button("Salvar")

    if submit:
        if operadora and circuito:
            ok = insert_row(mes, operadora, circuito, float(desconto))

            if ok:
                st.success(f"✅ Registro salvo ({mes_num:02d}/{ano})")
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
# KPIs
# ======================
st.subheader("📌 Indicadores")

c1, c2, c3 = st.columns(3)

c1.metric("💰 Total", f"R$ {df['desconto'].sum():,.2f}")
c2.metric("📄 Registros", len(df))
c3.metric("🏢 Operadoras", df["operadora"].nunique())

st.divider()

# ======================
# 📊 GRÁFICO CORRIGIDO
# ======================
st.subheader("📊 Evolução dos Descontos")

chart_data = (
    df.dropna(subset=["mes_dt"])
    .groupby("mes_dt")["desconto"]
    .sum()
    .sort_index()
)

st.line_chart(chart_data)

st.divider()

# ======================
# 📋 REGISTROS
# ======================
st.subheader("📋 Registros")

# 🔥 ordenar por data (mais recente primeiro)
df = df.sort_values("mes_dt", ascending=False)

# Cabeçalho
col1, col2, col3, col4, col5 = st.columns([2,2,3,2,1])

col1.markdown("**Mês/Ano**")
col2.markdown("**Operadora**")
col3.markdown("**Circuito**")
col4.markdown("**Valor (R$)**")
col5.markdown("")

st.divider()

# Linhas
for i, row in df.iterrows():
    col1, col2, col3, col4, col5 = st.columns([2,2,3,2,1])

    # Formatar mês bonito
    if pd.notna(row["mes_dt"]):
        mes_formatado = row["mes_dt"].strftime("%m/%Y")
    else:
        mes_formatado = row["mes"]

    col1.write(mes_formatado)
    col2.write(row["operadora"])
    col3.write(row["circuito"])
    col4.write(f"R$ {row['desconto']:.2f}")

    if col5.button("🗑️", key=f"del_{row['id']}"):
        delete_row(row["id"])
        st.rerun()
