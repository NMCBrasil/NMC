import streamlit as st
import difflib
import os
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Comparador de Configurações", layout="wide")
st.title("🔎 Comparador de Configurações de Rede")

CONFIG_DIR = "configs"
os.makedirs(CONFIG_DIR, exist_ok=True)

# Upload de arquivos
uploaded_files = st.file_uploader("Carregar arquivos .txt", type=["txt"], accept_multiple_files=True)
if uploaded_files:
    for file in uploaded_files:
        with open(os.path.join(CONFIG_DIR, file.name), "wb") as f:
            f.write(file.getbuffer())
    st.success("Arquivos salvos em 'configs/'")

# Lista arquivos disponíveis
files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".txt")]
if len(files) >= 2:
    col1, col2 = st.columns(2)
    with col1:
        file1 = st.selectbox("Configuração 1", files)
    with col2:
        file2 = st.selectbox("Configuração 2", files)

    if st.button("Comparar"):
        with open(os.path.join(CONFIG_DIR, file1)) as f1, open(os.path.join(CONFIG_DIR, file2)) as f2:
            diff = difflib.unified_diff(
                f1.readlines(), f2.readlines(),
                fromfile=file1, tofile=file2
            )
            diff_text = "".join(diff)

        st.subheader("📄 Diferenças encontradas")
        st.code(diff_text if diff_text else "Nenhuma diferença linha a linha detectada.", language="diff")

        # Relatório inteligente
        resumo = []
        c1 = open(os.path.join(CONFIG_DIR, file1)).read().splitlines()
        c2 = open(os.path.join(CONFIG_DIR, file2)).read().splitlines()
        max_len = max(len(c1), len(c2))

        for i in range(max_len):
            line1 = c1[i] if i < len(c1) else ""
            line2 = c2[i] if i < len(c2) else ""
            if line1 != line2:
                if line1 and line2:
                    resumo.append({"linha": i+1, "tipo": "alterada", "de": line1, "para": line2})
                elif line1 and not line2:
                    resumo.append({"linha": i+1, "tipo": "removida", "de": line1, "para": ""})
                elif not line1 and line2:
                    resumo.append({"linha": i+1, "tipo": "adicionada", "de": "", "para": line2})

        st.subheader("🤖 Relatório Inteligente")
        if resumo:
            df = pd.DataFrame(resumo)
            st.dataframe(df)

            # Gráfico resumo
            fig = px.histogram(df, x="tipo", title="Resumo das Alterações")
            st.plotly_chart(fig)
        else:
            # Mesmo sem diferenças linha a linha, sempre mostrar pontos de atenção
            st.info("As configurações são muito semelhantes, mas verifique:")
            st.write("- Hostname e IP de Loopback")
            st.write("- VLANs atribuídas em interfaces críticas")
            st.write("- Configuração de NTP (presente em um, ausente em outro)")
            st.write("- Senha de console e AAA")
            st.write("Sugestão: alinhar esses pontos para evitar falhas em backup/comutação.")
else:
    st.warning("⚠️ É necessário pelo menos dois arquivos .txt para comparar.")
