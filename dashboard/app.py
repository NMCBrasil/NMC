import streamlit as st
import difflib
import os

st.set_page_config(page_title="Comparador de Configurações", layout="wide")

st.title("🔎 Comparador de Configurações de Rede")

# Pasta onde ficam os arquivos de configuração
CONFIG_DIR = "configs"
os.makedirs(CONFIG_DIR, exist_ok=True)

st.sidebar.header("Upload de Configurações")
uploaded_files = st.sidebar.file_uploader(
    "Carregar arquivos .txt de configuração",
    type=["txt"],
    accept_multiple_files=True
)

# Salva os arquivos enviados
if uploaded_files:
    for file in uploaded_files:
        with open(os.path.join(CONFIG_DIR, file.name), "wb") as f:
            f.write(file.getbuffer())
    st.sidebar.success("Arquivos salvos em 'configs/'")

# Lista arquivos disponíveis
files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".txt")]
if len(files) < 2:
    st.warning("⚠️ É necessário pelo menos dois arquivos .txt na pasta 'configs' para comparar.")
else:
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
        st.code(diff_text if diff_text else "Nenhuma diferença encontrada.", language="diff")

        # Relatório inteligente simples
        resumo = []
        c1 = open(os.path.join(CONFIG_DIR, file1)).read().splitlines()
        c2 = open(os.path.join(CONFIG_DIR, file2)).read().splitlines()
        max_len = max(len(c1), len(c2))

        for i in range(max_len):
            line1 = c1[i] if i < len(c1) else ""
            line2 = c2[i] if i < len(c2) else ""
            if line1 != line2:
                if line1 and line2:
                    resumo.append(f"Linha {i+1}: alterada de '{line1}' → '{line2}'")
                elif line1 and not line2:
                    resumo.append(f"Linha {i+1}: removida na segunda config ('{line1}')")
                elif not line1 and line2:
                    resumo.append(f"Linha {i+1}: adicionada na segunda config ('{line2}')")

        st.subheader("🤖 Relatório Inteligente")
        if resumo:
            for r in resumo:
                st.write("- " + r)
            st.info("Sugestão: revisar alterações críticas (AAA, VLANs, SNMP, NTP, senhas) para evitar falhas em backup/comutação.")
        else:
            st.success("Configs idênticas — nenhuma alteração necessária.")
