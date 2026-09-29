import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Configuração da página para ocupar a tela inteira
st.set_page_config(layout="wide", page_title="Extrapolador ITTC-1957")

def calcular_extrapolacao_excel(scale, L_m, S_m, S_s_input, k_factor, rho_m, nu_m, rho_s, nu_s, df_input):
    df_clean = df_input.dropna(subset=["Vm [m/s]", "Rtm [N]"]).copy()
    if df_clean.empty:
        return pd.DataFrame(), None, None

    L_s = L_m * scale
    S_s = S_s_input  
    g = 9.81
    one_plus_k = 1 + k_factor  

    v_m = df_clean["Vm [m/s]"].astype(float).values
    r_tm = df_clean["Rtm [N]"].astype(float).values

    # Conversões e Froude
    v_s_ms = v_m * np.sqrt(scale)
    v_s_knots = v_s_ms / 0.51444
    fn = v_m / np.sqrt(g * L_m)

    # Reynolds
    re_m = (v_m * L_m) / nu_m
    re_s = (v_s_ms * L_s) / nu_s

    # Coeficientes ITTC-1957
    c_fm = 0.075 / ((np.log10(re_m) - 2) ** 2)
    c_fs = 0.075 / ((np.log10(re_s) - 2) ** 2)

    # Coeficiente Total do Modelo (Ctm)
    c_tm = r_tm / (0.5 * rho_m * S_m * (v_m ** 2))

    # --- MÉTODO DE FROUDE ---
    c_rm = c_tm - c_fm
    c_ts_froude = c_fs + c_rm
    r_ts_froude_n = c_ts_froude * 0.5 * rho_s * S_s * (v_s_ms ** 2)
    r_ts_froude_kn = r_ts_froude_n / 1000.0
    p_e_froude_kw = r_ts_froude_kn * v_s_ms
    p_e_froude_hp = p_e_froude_kw * 1.34102

    # --- MÉTODO DE HUGHES ---
    c_w = c_tm - (one_plus_k * c_fm)
    c_ts_hughes = (one_plus_k * c_fs) + c_w
    r_ts_hughes_n = c_ts_hughes * 0.5 * rho_s * S_s * (v_s_ms ** 2)
    r_ts_hughes_kn = r_ts_hughes_n / 1000.0
    p_e_hughes_kw = r_ts_hughes_kn * v_s_ms
    p_e_hughes_hp = p_e_hughes_kw * 1.34102

    # Tabela Completa de Resultados
    df_res = pd.DataFrame({
        "Ponto": np.arange(1, len(v_m) + 1),
        "Fn": np.round(fn, 4),
        "Vm [m/s]": np.round(v_m, 3),
        "Vs [knots]": np.round(v_s_knots, 2),
        "Rt Froude [kN]": np.round(r_ts_froude_kn, 2),
        "PE Froude [kW]": np.round(p_e_froude_kw, 2),
        "PE Froude [hp]": np.round(p_e_froude_hp, 2),
        "Rt Hughes [kN]": np.round(r_ts_hughes_kn, 2),
        "PE Hughes [kW]": np.round(p_e_hughes_kw, 2),
        "PE Hughes [hp]": np.round(p_e_hughes_hp, 2),
    })

    # Gráfico 1: Resistência vs Fn
    fig_r = go.Figure()
    fig_r.add_trace(go.Scatter(x=df_res["Fn"], y=df_res["Rt Froude [kN]"], mode='lines+markers', name='Froude (2D)', line=dict(color='gold')))
    fig_r.add_trace(go.Scatter(x=df_res["Fn"], y=df_res["Rt Hughes [kN]"], mode='lines+markers', name='Hughes (3D)', line=dict(color='red')))
    fig_r.update_layout(title="Resistência Total (Rt) vs Número de Froude (Fn)", xaxis_title="Número de Froude (Fn)", yaxis_title="Rt [kN]")

    # Gráfico 2: Potência vs Vs
    fig_p = go.Figure()
    fig_p.add_trace(go.Scatter(x=df_res["Vs [knots]"], y=df_res["PE Froude [hp]"], mode='lines+markers', name='Froude (2D)', line=dict(color='gold')))
    fig_p.add_trace(go.Scatter(x=df_res["Vs [knots]"], y=df_res["PE Hughes [hp]"], mode='lines+markers', name='Hughes (3D)', line=dict(color='red')))
    fig_p.update_layout(title="Potência Efetiva (PE em hp) vs Velocidade (Vs)", xaxis_title="Velocidade [knots]", yaxis_title="PE [hp]")

    return df_res, fig_r, fig_p

# Dados Iniciais da Planilha Corrigidos
dados_ensaio = pd.DataFrame({
    "Ponto":,
    "Vm [m/s]": [0.776, 0.846, 0.917, 0.987, 1.058, 1.128, 1.199],
    "Rtm [N]": [11.5, 13.5, 15.5, 18.0, 20.5, 23.0, 26.5]
})

st.markdown("# 🛳️ Calculadora de Extrapolação ITTC-1957")

# Organizando os inputs em colunas
col1, col2, col3, col4, col5 = st.columns(5)
scale = col1.number_input("Escala (λ)", value=53.215, format="%.3f")
L_m = col2.number_input("Comprimento Modelo Lm [m]", value=5.912, format="%.3f")
S_m = col3.number_input("Área Molhada Modelo Sm [m²]", value=8.638, format="%.3f")
S_s_input = col4.number_input("Área Molhada Navio Ss [m²]", value=24461.4, format="%.1f")
k_factor = col5.number_input("Fator de Forma (k)", value=0.2039, format="%.4f")

col6, col7, col8, col9 = st.columns(4)
rho_m = col6.number_input("ρ Modelo [kg/m³]", value=1000.0)
nu_m = col7.number_input("ν Modelo [m²/s]", value=1.14e-6, format="%.2e")
rho_s = col8.number_input("ρ Navio [kg/m³]", value=1025.0)
nu_s = col9.number_input("ν Navio [m²/s]", value=1.19e-6, format="%.2e")

st.markdown("### Dados do Ensaio (Tabela Editável)")
input_table = st.data_editor(dados_ensaio, num_rows="dynamic", use_container_width=True)

if st.button("⚡ Processar Extrapolação e Gerar Gráficos", type="primary"):
    df_res, fig_r, fig_p = calcular_extrapolacao_excel(
        scale, L_m, S_m, S_s_input, k_factor, rho_m, nu_m, rho_s, nu_s, input_table
    )
    
    if not df_res.empty:
        st.markdown("### Resultados Extrapolados (Com PE em hp)")
        st.dataframe(df_res, use_container_width=True)
        
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(fig_r, use_container_width=True)
        with g2:
            st.plotly_chart(fig_p, use_container_width=True)
    else:
        st.error("Por favor, preencha a tabela de dados corretamente.")

