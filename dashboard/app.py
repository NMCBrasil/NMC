import streamlit as st
import pandas as pd
from supabase import create_client

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Dashboard Operadoras", layout="wide")

st.title("📊 Dashboard de Operadoras")

st.markdown("""
Sistema para controle de descontos por circuito e operadora.

Use os filtros na lateral para refinar a análise.
""")

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

    # Converter mês para data (resolve ordem errada)
    df["mes_dt"] = pd.to_datetime(df["mes"], errors="coerce")

    if "created_at" in df.columns:
        df = df.drop(columns=["created_at"])

    return df


# ======================
# INSERT (VALIDADO)
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

    mes = c1.text_input("📅 Mês", placeholder="Ex: 2026-02")
    operadora = c2.text_input("📡 Operadora", placeholder="Ex: Vivo")

    circuito = c3.text_input("🔌 Circuito", placeholder="Ex: Link SP-01")
    desconto = c4.number_input("💰 Desconto (R$)", min_value=0.0)

    submit = st.form_submit_button("💾 Salvar Registro")

    if submit:
        if mes and operadora and circuito:
            ok = insert_row(mes, operadora, circuito, float(desconto))

            if ok:
                st.success("✅ Registro salvo com sucesso!")
                st.rerun()
            else:
                st.error("❌ Falha ao salvar no banco")
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
# SIDEBAR FILTROS
# ======================
with st.sidebar:
    st.markdown("### 🔎 Filtros")
    st.caption("Clique abaixo para visualizar os filtros")

    with st.expander("Abrir filtros", expanded=False):
        mes_f = st.selectbox("Mês", ["Todos"] + sorted(df["mes"].dropna().unique()))
        op_f = st.selectbox("Operadora", ["Todas"] + sorted(df["operadora"].dropna().unique()))

# Aplicar filtros
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

c1.metric("💰 Total de Descontos", f"R$ {filtered['desconto'].sum():,.2f}")
c2.metric("📄 Total de Registros", len(filtered))
c3.metric("🏢 Operadoras Únicas", filtered["operadora"].nunique())

st.divider()

# ======================
# GRÁFICOS (ORDENADOS)
# ======================
st.subheader("📊 Análise de Dados")

c1, c2 = st.columns(2)

c1.markdown("**Descontos por Operadora**")
c1.bar_chart(filtered.groupby("operadora")["desconto"].sum())

c2.markdown("**Evolução por Mês")

chart_data = (
    filtered
    .sort_values("mes_dt")
    .groupby("mes_dt", as_index=False)["desconto"].sum()
)

chart_data = chart_data.set_index("mes_dt")

c2.line_chart(chart_data)

st.divider()

# ======================
# TABELA MELHORADA
# ======================
st.subheader("📋 Dados cadastrados")

display_df = filtered.copy()

display_df = display_df.rename(columns={
    "id": "ID",
    "mes": "Mês",
    "operadora": "Operadora",
    "circuito": "Circuito",
    "desconto": "Desconto (R$)"
})

display_df = display_df.sort_values("mes_dt")

st.dataframe(
    display_df[["ID", "Mês", "Operadora", "Circuito", "Desconto (R$)"]],
    use_container_width=True
)

# ======================
# DELETE COM CONFIRMAÇÃO
# ======================
st.markdown("### 🗑️ Remover registro")

ids = display_df["ID"].tolist()

selected_id = st.selectbox("Selecione o ID para excluir", ids)

if st.button("Excluir registro"):
    st.warning(f"Confirma exclusão do ID {selected_id}?")

    c1, c2 = st.columns(2)

    if c1.button("✅ Confirmar exclusão"):
        delete_row(selected_id)
        st.success("Registro excluído")
        st.rerun()

    if c2.button("❌ Cancelar"):
        st.info("Exclusão cancelada")
