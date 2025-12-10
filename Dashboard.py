import streamlit as st
import pandas as pd
import plotly.express as px
import io
from datetime import datetime
import tempfile
import pdfkit
import numpy as np

# ---------------- CONFIGURAÇÃO ----------------
st.set_page_config(
    page_title="Dashboard Chamados",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- ESTILO ----------------
st.markdown("""
<style>
.stMetricLabel, .stMetricValue { color: #000 !important; }
div.stDataFrame div.row_widget.stDataFrame {
    background-color: #f7f7f7 !important;
    color: #000 !important;
    font-size: 14px;
}
.plotly-graph-div { background-color: #f7f7f7 !important; }
.stDownloadButton button {
    color: #000 !important;
    background-color: #d9e4f5 !important;
    border: 1px solid #000 !important;
    padding: 6px 12px !important;
    border-radius: 5px !important;
    font-weight: bold !important;
}
section[data-testid="stSidebar"] {
    background-color: #e8e8e8 !important;
    color: #000 !important;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] select {
    color: #000 !important;
    background-color: #f0f0f0 !important;
}
input[type="file"] {
    background-color: #d9e4f5 !important;
    color: #000 !important;
    font-weight: bold !important;
    border: 1px solid #000;
    border-radius: 5px;
    padding: 5px;
}
.sidebar-multiselect .stMultiSelect {
    max-height: 120px !important;
    overflow-y: auto !important;
}
.initial-message {
    background-color: #d9e4f5;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    font-size: 18px;
    font-weight: bold;
    color: #000;
}
</style>
""", unsafe_allow_html=True)

# ---------------- UPLOAD ----------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

# ---------------- TELA INICIAL ----------------
if uploaded_file is None:
    st.title("📊 Dashboard Chamados")
    st.markdown('<div class="initial-message">Envie um arquivo CSV separado por vírgula para visualizar o dashboard.<br>O sistema detecta automaticamente colunas de datas, usuários, causas e tipos.</div>', unsafe_allow_html=True)

else:
    # ---------------- LEITURA DO CSV ----------------
    df = pd.read_csv(uploaded_file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    df = df.fillna("")
    df = df.applymap(lambda x: str(x).strip())

    # ---------------- DETECTAR TIPO ----------------
    colunas_consumer = [
        "Situação", "Assunto", "Data/Hora de abertura", "Criado por",
        "Causa raiz", "Tipo de registro do caso", "Caso modificado pela última vez por"
    ]
    relatorio_tipo = "consumer" if all(col in df.columns for col in colunas_consumer) else "enterprise"
    titulo_dashboard = "📊 Chamados Consumer" if relatorio_tipo == "consumer" else "📊 Chamados Enterprise"

    st.title(titulo_dashboard)

    # ---------------- NORMALIZAÇÃO CONSUMER ----------------
    if relatorio_tipo == "consumer":
        def normaliza_satelite(valor):
            texto = str(valor).upper()
            if "E65" in texto:
                return "E65"
            if "63W" in texto or "T19" in texto:
                return "63W/T19"
            if "J3" in texto:
                return "J3"
            return "Não informado"
        df["Satélite"] = df.get("Assunto", "").apply(normaliza_satelite)

    # ---------------- FLAG DE FECHADO ----------------
    if relatorio_tipo == "enterprise":
        df['Fechado'] = df.get('Status', '').str.lower() == "fechado"
    else:
        col_modificado_por = 'Caso modificado pela última vez por'
        if col_modificado_por in df.columns:
            df['Fechado'] = df[col_modificado_por].apply(lambda x: str(x).strip() != "")
        else:
            df['Fechado'] = False

    # ---------------- CONVERSÃO DE DATAS ----------------
    for col in df.columns:
        if "data" in col.lower() or "hora" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
            except:
                continue

    # ---------------- FILTROS ----------------
    st.sidebar.header("🔎 Filtros")
    if relatorio_tipo == "enterprise":
        filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df.get('Criado por', pd.Series()).unique())
        filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df.get('Fechado por', pd.Series()).unique())
        filtro_categoria = st.sidebar.multiselect("Reclamação", df.get('Reclamação', pd.Series()).unique())
        filtro_diag = st.sidebar.multiselect("Diagnóstico", df.get('Diagnóstico', pd.Series()).unique())
    else:
        filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df.get('Criado por', pd.Series()).unique())
        filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df.get('Caso modificado pela última vez por', pd.Series()).unique())
        filtro_diag = st.sidebar.multiselect("Causa Raiz", df.get('Causa raiz', pd.Series()).unique())
        filtro_satelite = st.sidebar.multiselect("Satélite", df.get("Satélite", pd.Series()).unique())

    # ---------------- APLICAR FILTROS ----------------
    df_filtrado = df.copy()
    if filtro_aberto:
        df_filtrado = df_filtrado[df_filtrado['Criado por'].isin(filtro_aberto)]
    if filtro_fechado:
        col_fechado = "Fechado por" if relatorio_tipo == "enterprise" else "Caso modificado pela última vez por"
        df_filtrado = df_filtrado[df_filtrado[col_fechado].isin(filtro_fechado)]
    if relatorio_tipo == "enterprise" and filtro_categoria:
        df_filtrado = df_filtrado[df_filtrado["Reclamação"].isin(filtro_categoria)]
    if filtro_diag:
        col_diag = "Diagnóstico" if relatorio_tipo == "enterprise" else "Causa raiz"
        df_filtrado = df_filtrado[df_filtrado[col_diag].isin(filtro_diag)]
    if relatorio_tipo == "consumer" and filtro_satelite:
        df_filtrado = df_filtrado[df_filtrado["Satélite"].isin(filtro_satelite)]
    df_filtrado = df_filtrado.replace("", "Não informado")

    # ---------------- MÉTRICAS ----------------
    total_chamados = len(df_filtrado)
    total_abertos = len(df_filtrado[~df_filtrado['Fechado']])
    total_fechados = len(df_filtrado[df_filtrado['Fechado']])

    col1, col2, col3 = st.columns(3)
    # Tempo médio corrigido (Enterprise)
    tempo_total = 0
    if relatorio_tipo == "enterprise":
        if "Data/Hora de abertura" in df_filtrado.columns and "Data/Hora de fechamento" in df_filtrado.columns:
            df_valid = df_filtrado.dropna(subset=["Data/Hora de abertura", "Data/Hora de fechamento"])
            if not df_valid.empty:
                # Garantir tipos corretos e valores válidos
                abertura = pd.to_datetime(df_valid["Data/Hora de abertura"], errors="coerce")
                fechamento = pd.to_datetime(df_valid["Data/Hora de fechamento"], errors="coerce")
                delta = (fechamento - abertura).dt.total_seconds() / 60
                delta = delta.replace([np.inf, -np.inf], np.nan).dropna()
                if not delta.empty:
                    tempo_total = delta.mean()
    col1.metric("⏱ Tempo médio total (min)", f"{tempo_total:.2f}" if tempo_total else "0.00")

    # Maior ofensor
    coluna_ofensor = "Diagnóstico" if relatorio_tipo == "enterprise" else "Causa raiz"
    df_valid_ofensor = df_filtrado[df_filtrado[coluna_ofensor] != "Não informado"]
    if not df_valid_ofensor.empty:
        contagem = df_valid_ofensor[coluna_ofensor].value_counts()
        maior_ofensor = contagem.index[0]
        qtd_maior = contagem.iloc[0]
        pct_maior = (qtd_maior / total_chamados * 100) if total_chamados else 0
    else:
        maior_ofensor, pct_maior = "-", 0
    col2.metric("📌 Maior ofensor", maior_ofensor)
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_maior:.2f}%")

    # ---------------- TOTAL ----------------
    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    if relatorio_tipo == "consumer":
        qtd_evento = (df_filtrado.get("Tipo de registro do caso", pd.Series()) == "Operações - Evento").sum()
        qtd_cm = (df_filtrado.get("Tipo de registro do caso", pd.Series()) == "Operações - CM").sum()
        st.write(f"🟦 Operações - Evento: **{qtd_evento}**")
        st.write(f"🟪 Operações - CM: **{qtd_cm}**")
    st.write(f"🔵 Chamados abertos: {total_abertos} ({(total_abertos/total_chamados*100):.1f}%)" if total_chamados else "🔵 Chamados abertos: 0 (0.0%)")
    st.write(f"🔴 Chamados fechados: {total_fechados} ({(total_fechados/total_chamados*100):.1f}%)" if total_chamados else "🔴 Chamados fechados: 0 (0.0%)")

    # ---------------- FUNÇÕES ----------------
    def tabela_limpa(df_in):
        df_out = df_in.replace("", "Não informado")
        df_out = df_out.dropna(how="all")
        return df_out

    def grafico_com_tabela(df_graf, coluna, titulo, icone="📁"):
        df_graf = df_graf[df_graf[coluna] != "Não informado"]
        if df_graf.empty:
            return None, None
        tabela = df_graf.groupby(coluna).size().reset_index(name="Qtd")
        tabela = tabela[tabela["Qtd"] > 0]
        tabela["%"] = (tabela["Qtd"] / tabela["Qtd"].sum() * 100).round(2)
        tabela = tabela_limpa(tabela)
        if tabela.empty:
            return None, None
        st.subheader(f"{icone} {titulo}")
        col_t, col_g = st.columns([1.4, 3])
        tabela_height = min(350, 50 + len(tabela) * 35)
        with col_t:
            st.dataframe(tabela, height=tabela_height)
        fig = px.bar(
            tabela, x=coluna, y="Qtd", text="Qtd",
            color="Qtd", color_continuous_scale="Blues", template="plotly_white"
        )
        fig.update_traces(textposition="outside")
        with col_g:
            st.plotly_chart(fig, use_container_width=True)
        return fig, tabela

    # ---------------- GRÁFICOS ----------------
    figs = []

    # Abertos por usuário
    fig_abertos, tabela_abertos = grafico_com_tabela(df_filtrado, "Criado por", "Chamados abertos por usuário", "🔵")
    figs.append(fig_abertos)

    # Fechados por usuário
    col_fechado = "Fechado por" if relatorio_tipo == "enterprise" else "Caso modificado pela última vez por"
    df_fechados = df_filtrado[df_filtrado['Fechado'] & (df_filtrado[col_fechado] != "Não informado")]
    fig_fechados, tabela_fechados = grafico_com_tabela(df_fechados, col_fechado, "Chamados fechados por usuário", "🔴")
    figs.append(fig_fechados)

    # Reclamação (enterprise)
    if relatorio_tipo == "enterprise":
        fig_reclamacao, tabela_reclamacao = grafico_com_tabela(df_filtrado, "Reclamação", "Reclamação", "📌")
        figs.append(fig_reclamacao)

    # Diagnóstico / Causa raiz
    col_diag = "Diagnóstico" if relatorio_tipo == "enterprise" else "Causa raiz"
    fig_diag, tabela_diag = grafico_com_tabela(df_filtrado, col_diag, col_diag, "📌")
    figs.append(fig_diag)

    # Satélite (consumer)
    if relatorio_tipo == "consumer":
        st.subheader("🛰 Satélite")
        tabela_sat = df_filtrado["Satélite"].value_counts().reset_index()
        tabela_sat.columns = ["Satélite", "Qtd"]
        tabela_sat["%"] = (tabela_sat["Qtd"] / tabela_sat["Qtd"].sum() * 100).round(2)
        tabela_sat = tabela_limpa(tabela_sat)
        col_t, col_g = st.columns([1.4, 3])
        tabela_height = min(350, 50 + len(tabela_sat) * 35)
        with col_t:
            st.dataframe(tabela_sat, height=tabela_height)
        fig_sat = px.bar(
            tabela_sat, x="Satélite", y="Qtd", text="Qtd",
            color="Qtd", color_continuous_scale="Blues", template="plotly_white"
        )
        fig_sat.update_traces(textposition="outside")
        with col_g:
            st.plotly_chart(fig_sat, use_container_width=True)
        figs.append(fig_sat)

    # ---------------- PDF: GERAÇÃO ----------------
    def gerar_pdf_dashboard(df_filtrado, titulo_dashboard, figs,
                            total_chamados, total_abertos, total_fechados,
                            tempo_total, maior_ofensor, pct_maior,
                            relatorio_tipo,
                            tabela_abertos=None, tabela_fechados=None,
                            tabela_reclamacao=None, tabela_diag=None, tabela_sat=None):

        # Cabeçalho e métricas
        conteudo = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1 {{ margin-bottom: 4px; }}
                .metricas {{ display: flex; gap: 24px; margin: 12px 0 24px; }}
                .metrica {{ background: #d9e4f5; padding: 10px 14px; border: 1px solid #000; border-radius: 6px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
                th, td {{ border: 1px solid #ccc; padding: 6px 8px; font-size: 12px; }}
                th {{ background: #f0f0f0; }}
                .secao {{ margin-top: 24px; }}
            </style>
        </head>
        <body>
            <h1>{titulo_dashboard}</h1>
            <div class="metricas">
                <div class="metrica"><b>Total de chamados:</b> {total_chamados}</div>
                <div class="metrica"><b>Abertos:</b> {total_abertos}</div>
                <div class="metrica"><b>Fechados:</b> {total_fechados}</div>
                <div class="metrica"><b>Tempo médio (min):</b> {tempo_total:.2f if tempo_total else 0.00}</div>
                <div class="metrica"><b>Maior ofensor:</b> {maior_ofensor}</div>
                <div class="metrica"><b>% maior ofensor:</b> {pct_maior:.2f}%</div>
            </div>
        """

        # Tabelas resumidas das seções (iguais às do dashboard)
        def tabela_html_if_exists(tabela, titulo):
            if tabela is not None and isinstance(tabela, pd.DataFrame) and not tabela.empty:
                return f"<div class='secao'><h3>{titulo}</h3>{tabela.to_html(index=False)}</div>"
            return ""

        conteudo += tabela_html_if_exists(tabela_abertos, "🔵 Chamados abertos por usuário")
        conteudo += tabela_html_if_exists(tabela_fechados, "🔴 Chamados fechados por usuário")
        if relatorio_tipo == "enterprise":
            conteudo += tabela_html_if_exists(tabela_reclamacao, "📌 Reclamação")
        conteudo += tabela_html_if_exists(tabela_diag, f"📌 {('Diagnóstico' if relatorio_tipo=='enterprise' else 'Causa raiz')}")
        if relatorio_tipo == "consumer":
            conteudo += tabela_html_if_exists(tabela_sat, "🛰 Satélite")

        # Gráficos
        for fig in figs:
            if fig is not None:
                conteudo += "<div class='secao'>"
                conteudo += fig.to_html(full_html=False, include_plotlyjs='cdn')
                conteudo += "</div>"

        conteudo += "</body></html>"

        # Converter para PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdfkit.from_string(conteudo, tmpfile.name)
            return tmpfile.read()

    # ---------------- PDF: BOTÃO ----------------
    pdf_bytes = gerar_pdf_dashboard(
        df_filtrado=df_filtrado,
        titulo_dashboard=titulo_dashboard,
        figs=[f for f in figs if f is not None],
        total_chamados=total_chamados,
        total_abertos=total_abertos,
        total_fechados=total_fechados,
        tempo_total=tempo_total if tempo_total else 0.0,
        maior_ofensor=maior_ofensor,
        pct_maior=pct_maior,
        relatorio_tipo=relatorio_tipo,
        tabela_abertos=tabela_abertos,
        tabela_fechados=tabela_fechados,
        tabela_reclamacao=(tabela_reclamacao if relatorio_tipo == "enterprise" else None),
        tabela_diag=tabela_diag,
        tabela_sat=(tabela_sat if relatorio_tipo == "consumer" else None)
    )

    st.download_button(
        "📥 Baixar Dashboard em PDF",
        data=pdf_bytes,
        file_name="dashboard.pdf",
        mime="application/pdf"
    )
