import streamlit as st
import os
import pandas as pd

st.set_page_config(page_title="Comparador de Configurações", layout="wide")
st.title("🔎 Comparador de Configurações de Equipamentos")

CONFIG_DIR = "configs"
os.makedirs(CONFIG_DIR, exist_ok=True)

# Upload de arquivos
uploaded_files = st.file_uploader("Carregar arquivos .txt", type=["txt"], accept_multiple_files=True)
if uploaded_files:
    for file in uploaded_files:
        with open(os.path.join(CONFIG_DIR, file.name), "wb") as f:
            f.write(file.getbuffer())
    st.success("Arquivos salvos em 'configs/'")

# Função para classificar linhas por categoria
def classificar_linha(line):
    if line.startswith("hostname"):
        return "Hostname"
    elif line.startswith("interface"):
        return "Interface"
    elif "ip address" in line:
        return "IP Address"
    elif "ntp server" in line:
        return "NTP"
    elif "access-list" in line:
        return "ACL"
    elif "crypto" in line:
        return "Crypto"
    elif "ip route" in line:
        return "Rotas"
    elif "line con" in line or "line vty" in line:
        return "Console/VTY"
    elif "vlan" in line:
        return "VLAN"
    else:
        return "Outros"

# Regras confiáveis com impacto crítico
rules = {
    "Hostname": ("Hostname divergente", "🟡 Pode afetar SNMP/logs", "Padronizar nomenclatura"),
    "IP Address": ("Endereço IP diferente", "🔴 Pode quebrar conectividade de gestão/roteamento", "Alinhar IPs de Loopback/WAN"),
    "NTP": ("Configuração NTP divergente", "🟡 Logs fora de sincronismo", "Configurar NTP em ambos"),
    "VLAN": ("Configuração de VLAN diferente", "🔴 Pode causar queda de tráfego entre redes", "Uniformizar VLANs críticas"),
    "ACL": ("ACL diferente", "🔴 Pode bloquear tráfego inesperadamente", "Revisar políticas de segurança"),
    "Crypto": ("Configuração de criptografia diferente", "🔴 Pode impedir VPN/segurança", "Padronizar certificados/chaves"),
    "Rotas": ("Rotas diferentes", "🔴 Pode causar perda de tráfego", "Alinhar tabela de rotas"),
    "Console/VTY": ("Configuração de console diferente", "🟡 Acesso administrativo pode variar", "Padronizar senha e AAA"),
    "Interface": ("Configuração de interface diferente", "🔴 Diferença de VLAN/status pode derrubar tráfego", "Padronizar VLAN/descrição"),
    "Outros": ("Configuração diferente", "🟢 Sem impacto crítico", "Verificar se necessário"),
}

# Lista arquivos disponíveis
files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".txt")]
if len(files) >= 2:
    col1, col2 = st.columns(2)
    with col1:
        file1 = st.selectbox("Device 1", files)
    with col2:
        file2 = st.selectbox("Device 2", files)

    if st.button("Comparar"):
        c1 = open(os.path.join(CONFIG_DIR, file1)).read().splitlines()
        c2 = open(os.path.join(CONFIG_DIR, file2)).read().splitlines()

        # Agrupamento por categoria
        grupos_device1 = {}
        for line in c1:
            categoria = classificar_linha(line)
            grupos_device1.setdefault(categoria, []).append(line)

        grupos_device2 = {}
        for line in c2:
            categoria = classificar_linha(line)
            grupos_device2.setdefault(categoria, []).append(line)

        resumo = []
        # Comparação por categoria
        todas_categorias = set(grupos_device1.keys()) | set(grupos_device2.keys())
        for categoria in todas_categorias:
            linhas1 = grupos_device1.get(categoria, [])
            linhas2 = grupos_device2.get(categoria, [])
            if linhas1 != linhas2:
                obs, impacto, sugestao = rules.get(categoria, ("Configuração diferente", "🟡 Atenção", "Revisar"))
                resumo.append({
                    "Categoria": categoria,
                    "Device 1": "\n".join(linhas1) if linhas1 else "—",
                    "Device 2": "\n".join(linhas2) if linhas2 else "—",
                    "Observação": obs,
                    "Impacto": impacto,
                    "Sugestão": sugestao
                })
            else:
                # Mostrar também categorias iguais para confiança
                resumo.append({
                    "Categoria": categoria,
                    "Device 1": "\n".join(linhas1) if linhas1 else "—",
                    "Device 2": "\n".join(linhas2) if linhas2 else "—",
                    "Observação": "Sem diferenças",
                    "Impacto": "🟢 Ok",
                    "Sugestão": "—"
                })

        st.subheader("🤖 Relatório Inteligente")
        df = pd.DataFrame(resumo)
        st.dataframe(df, use_container_width=True)
else:
    st.warning("⚠️ É necessário pelo menos dois arquivos .txt para comparar.")
