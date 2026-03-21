import streamlit as st
import math
import io
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="ONEE Tech Assistant", page_icon="⚡", layout="centered")

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root { --onee-green: #00793B; --onee-dark: #00501F; --bg: #F4F6F0; }
    .onee-header { background: linear-gradient(135deg, var(--onee-dark), var(--onee-green)); border-radius: 15px; padding: 25px; color: white; margin-bottom: 20px; }
    .calc-card { background: white; border: 1px solid #C8DCC8; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .result-box { border-radius: 10px; padding: 15px; margin-top: 10px; border-left: 5px solid; }
    .result-ok { background:#E8F5EE; border-color:var(--onee-green); }
    .result-warn { background:#FFF8E1; border-color:#F4A800; }
    .result-err { background:#FFEBEE; border-color:#D32F2F; }
    .stButton > button { background: linear-gradient(135deg, var(--onee-green), var(--onee-dark)) !important; color: white !important; width: 100%; border-radius: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="onee-header">
    <div style="font-family:'Barlow Condensed'; font-size:28px; font-weight:800">ONEE Tech Assistant</div>
    <div style="font-size:14px; opacity:0.8">Étude d'impact : Chute de tension PCC & Bout de ligne</div>
</div>
""", unsafe_allow_html=True)

# ── Calculateur ────────────────────────────────────────────────────────────────
st.markdown('<div class="calc-card">', unsafe_allow_html=True)

# 1. DONNÉES DE CHARGE
st.subheader("1. Puissances et Courants")
col_p1, col_p2 = st.columns(2)
with col_p1:
    p_kva = st.number_input("Puissance demandée nouveau client (kVA)", min_value=1.0, value=18.0)
    tension_ref = st.number_input("Tension Nominale (V)", value=400.0)
with col_p2:
    i_existant = st.number_input("Courant existant sur la ligne (A)", min_value=0.0, value=20.0)
    cos_phi = st.slider("Facteur de puissance (cos φ)", 0.50, 1.0, 0.85, 0.01)

# Calcul du courant du nouveau client
i_nouveau = (p_kva * 1000) / (tension_ref * math.sqrt(3))
i_total_amont = i_existant + i_nouveau

st.info(f"⚡ Nouveau client : **{i_nouveau:.1f} A** | Courant cumulé sur Segment A : **{i_total_amont:.1f} A**")

st.markdown("---")

# 2. CONFIGURATION PHYSIQUE (DISTANCES)
st.subheader("2. Distances et Réseau")
col_d1, col_d2 = st.columns(2)
with col_d1:
    dist_poste_pcc = st.number_input("Distance : Poste → PCC (m)", min_value=1.0, value=150.0)
with col_d2:
    dist_poste_bout = st.number_input("Distance : Poste → Bout de ligne (m)", min_value=dist_poste_pcc, value=250.0)

# Calcul de la longueur réelle du tronçon d'extension
dist_segment_b = dist_poste_bout - dist_poste_pcc
st.caption(f"📏 Longueur réelle de l'extension (Segment B) : **{dist_segment_b} mètres**")

col_s1, col_s2 = st.columns(2)
with col_s1:
    s_a = st.selectbox("Section Poste → PCC (mm²)", [35, 50, 70, 95, 120, 150], index=1)
with col_s2:
    s_b = st.selectbox("Section PCC → Bout (mm²)", [16, 25, 35, 50, 70, 95], index=1)

mat = st.radio("Matériau des conducteurs", ["Cuivre", "Alu"], horizontal=True)

# 3. CALCULS TECHNIQUES (Suggestion 1 & 3 incluses)
if st.button("⚡ CALCULER L'IMPACT TENSION"):
    rho = 0.0225 if mat == "Cuivre" else 0.036
    sin_phi = math.sqrt(1 - cos_phi**2)
    reactance_lin = 0.00008 # 0.08 ohm/km

    # --- SEGMENT A (Poste -> PCC) ---
    # Courant = Existant + Nouveau
    R_a = (rho * dist_poste_pcc) / s_a
    X_a = reactance_lin * dist_poste_pcc
    dU_a = math.sqrt(3) * i_total_amont * (R_a * cos_phi + X_a * sin_phi)
    
    # --- SEGMENT B (PCC -> Bout) ---
    # Courant = Nouveau client seulement
    R_b = (rho * dist_segment_b) / s_b
    X_b = reactance_lin * dist_segment_b
    dU_b = math.sqrt(3) * i_nouveau * (R_b * cos_phi + X_b * sin_phi)

    # --- SYNTHÈSE ---
    dU_total = dU_a + dU_b
    perc_pcc = (dU_a / tension_ref) * 100
    perc_total = (dU_total / tension_ref) * 100
    u_finale = tension_ref - dU_total

    st.markdown("### Synthèse des résultats")
    
    # Résultat au PCC
    st.markdown(f"""
    <div class="result-box result-ok">
        <small>AU POINT DE RACCORDEMENT (PCC)</small><br>
        <b>Chute de tension : {dU_a:.2f} V ({perc_pcc:.2f} %)</b>
    </div>
    """, unsafe_allow_html=True)
    
    # Résultat au Bout de ligne
    color = "result-err" if perc_total > 5 else "result-warn" if perc_total > 3 else "result-ok"
    st.markdown(f"""
    <div class="result-box {color}">
        <small>AU BOUT DE LIGNE (NOUVEAU CLIENT)</small><br>
        <b style="font-size:20px">Chute Totale : {dU_total:.2f} V ({perc_total:.2f} %)</b><br>
        Tension résiduelle : <b>{u_finale:.1f} V</b>
    </div>
    """, unsafe_allow_html=True)

    if perc_total > 5:
        st.error("❌ Attention : Chute de tension > 5%. La section des câbles est insuffisante.")
    else:
        st.success("✅ La chute de tension est dans les limites admissibles.")

st.markdown('</div>', unsafe_allow_html=True)
