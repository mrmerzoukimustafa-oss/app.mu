import streamlit as st
import math
from datetime import datetime
from typing import Dict, Tuple, Any

# ── Constants ──────────────────────────────────────────────────────────────────
class Constants:
    RESISTIVITY = {"Cuivre (Cu)": 0.0225, "Aluminium (Al)": 0.036}
    REACTANCE = 0.08  # Ω/km
    COS_PHI = 0.9
    SIN_PHI = math.sqrt(1 - COS_PHI**2)
    CABLE_SECTIONS = [16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]
    NETWORK_VOLTAGES = {"Triphasé BT (400V)": 400.0, "Monophasé (230V)": 230.0, "MT (5500V)": 5500.0}
    CHARGE_WARNING = 80.0
    CHARGE_CRITICAL = 100.0
    VOLTAGE_DROP_WARNING = 3.0
    VOLTAGE_DROP_CRITICAL = 5.0
    UNBALANCE_WARNING = 20.0
    UNBALANCE_CRITICAL = 30.0

# ── Session state init ─────────────────────────────────────────────────────────
def init_session_state():
    if "res_t1" not in st.session_state:
        st.session_state.res_t1 = None
    if "res_t2" not in st.session_state:
        st.session_state.res_t2 = None

init_session_state()

# ── CSS with visible select box text and horizontal current inputs ────────────
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #F5F5F5; }
    
    /* Header */
    .onee-header {
        background: #1B5E20;
        border-radius: 16px;
        padding: 32px 40px;
        margin-bottom: 24px;
    }
    .onee-logo { font-size: 12px; font-weight: 600; color: #FFFFFF; text-transform: uppercase; }
    .onee-title { font-size: 36px; font-weight: 800; color: #FFFFFF; margin: 0; }
    .onee-subtitle { font-size: 14px; color: #E8F5E9; }
    
    /* Cards */
    .calc-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 24px;
        border: 1px solid #E0E0E0;
    }
    .card-title {
        font-size: 22px;
        font-weight: 700;
        color: #1B5E20;
        margin-bottom: 24px;
        padding-bottom: 12px;
        border-bottom: 2px solid #E8F5E9;
    }
    
    /* Phase card horizontal layout */
    .phase-row {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .phase-label {
        font-weight: 700;
        font-size: 16px;
        min-width: 80px;
    }
    .phase-input {
        flex: 1;
        min-width: 120px;
    }
    
    /* Result boxes */
    .result-box {
        border-radius: 12px;
        padding: 24px 28px;
        margin-top: 20px;
        border-left: 5px solid;
    }
    .result-ok { background: #E8F5E9; border-left-color: #1B5E20; }
    .result-warn { background: #FFF3E0; border-left-color: #FF9800; }
    .result-err { background: #FFEBEE; border-left-color: #D32F2F; }
    .result-label { font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; color: #5A6B5A; }
    .result-value { font-size: 48px; font-weight: 800; line-height: 1; margin-bottom: 8px; color: #1A2A1A; }
    .result-msg { font-size: 13px; font-weight: 500; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(0,0,0,0.08); color: #2C3E2C; }
    
    /* Metrics */
    [data-testid="metric-container"] {
        background: #F8F9F8;
        border-radius: 12px;
        padding: 16px !important;
        border: 1px solid #E0E0E0;
    }
    [data-testid="stMetricLabel"] { color: #1B5E20 !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #1B5E20 !important; font-weight: 800 !important; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #E8F5E9;
        border-radius: 40px;
        padding: 4px;
        margin-bottom: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 40px;
        font-weight: 600;
        padding: 10px 24px;
        color: #2C3E2C !important;
    }
    .stTabs [aria-selected="true"] {
        background: #1B5E20 !important;
        color: white !important;
    }
    
    /* Inputs - general */
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > input {
        background: #FFFFFF !important;
        border: 1px solid #D0D0D0 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        color: #1A2A1A !important;
    }
    
    /* Selectbox (section & réseau) - make selected text GREEN */
    .stSelectbox > div > div > div[data-baseweb="select"] > div {
        color: #1B5E20 !important;
        font-weight: 600 !important;
        background-color: #FFFFFF !important;
    }
    .stSelectbox > div > div > div[data-baseweb="select"] svg {
        stroke: #1B5E20 !important;
        fill: #1B5E20 !important;
    }
    /* Dropdown options */
    div[role="listbox"] div {
        color: #1B5E20 !important;
        font-weight: 500 !important;
    }
    div[role="listbox"] div:hover {
        background-color: #E8F5E9 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: #1B5E20 !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        width: 100%;
    }
    .stButton > button:hover { background: #0F4A13 !important; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E0E0E0; }
    .onee-footer {
        text-align: center;
        padding: 24px;
        margin-top: 40px;
        border-top: 1px solid #E0E0E0;
        background: #FFFFFF;
        border-radius: 16px;
    }
    .badge {
        background: #E8F5E9;
        color: #1B5E20 !important;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        margin: 0 4px;
        display: inline-block;
    }
    .cos-badge {
        background: #E8F5E9;
        color: #1B5E20 !important;
        font-size: 16px;
        font-weight: 800;
        padding: 8px 20px;
        border-radius: 40px;
        text-align: center;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# ── Calculation functions (same as before) ────────────────────────────────────
def calculate_transformer_load(s_nom: float, p_reel: float) -> Dict[str, Any]:
    cos_phi = Constants.COS_PHI
    s_reel = p_reel / cos_phi
    charge = (s_reel / s_nom) * 100 if s_nom > 0 else 0
    q_reel = p_reel * math.tan(math.acos(cos_phi))
    if charge > Constants.CHARGE_CRITICAL:
        status, message = "err", "🚨 SURCHARGE CRITIQUE — Intervention immédiate"
    elif charge > Constants.CHARGE_WARNING:
        status, message = "warn", "⚡ Charge ÉLEVÉE — Surveillance recommandée"
    else:
        status, message = "ok", "✓ Charge NORMALE — Fonctionnement correct"
    return {"s_nom": s_nom, "p_reel": p_reel, "cos_phi": cos_phi, "s_reel": s_reel,
            "charge": charge, "q_reel": q_reel, "status": status, "message": message}

def calculate_voltage_drop_per_phase(i_phase, L, section, material, tension_ref):
    cos_phi, sin_phi = Constants.COS_PHI, Constants.SIN_PHI
    rho = Constants.RESISTIVITY[material]
    R = (rho * L) / section
    X = Constants.REACTANCE * L / 1000
    delta_u = math.sqrt(3) * i_phase * (R * cos_phi + X * sin_phi)
    delta_u_resistive = math.sqrt(3) * i_phase * R * cos_phi
    delta_u_reactive = math.sqrt(3) * i_phase * X * sin_phi
    perc_drop = (delta_u / tension_ref) * 100
    S = i_phase * tension_ref / math.sqrt(3) / 1000
    P, Q = S * cos_phi, S * sin_phi
    return {"delta_u": delta_u, "delta_u_resistive": delta_u_resistive, "delta_u_reactive": delta_u_reactive,
            "perc_drop": perc_drop, "R": R, "X": X, "S": S, "P": P, "Q": Q, "cos_phi": cos_phi}

def calculate_three_phase_unbalanced(currents, L, section, material, tension_ref):
    i_avg = sum(currents) / 3
    if i_avg > 0:
        deviations = [(abs(i - i_avg) / i_avg) * 100 for i in currents]
        max_dev = max(deviations)
        if max_dev > Constants.UNBALANCE_CRITICAL:
            imb_status, imb_msg = "err", f"⚠️ DÉSÉQUILIBRE CRITIQUE ({max_dev:.1f}%)"
        elif max_dev > Constants.UNBALANCE_WARNING:
            imb_status, imb_msg = "warn", f"⚡ Déséquilibre modéré ({max_dev:.1f}%)"
        else:
            imb_status, imb_msg = "ok", f"✓ Déséquilibre acceptable ({max_dev:.1f}%)"
    else:
        max_dev, deviations, imb_status, imb_msg = 0, [0,0,0], "ok", "Aucun courant"
    phases = []
    for i, cur in enumerate(currents):
        res = calculate_voltage_drop_per_phase(cur, L, section, material, tension_ref)
        res["phase"] = i+1
        res["current"] = cur
        phases.append(res)
    total_S = sum(p["S"] for p in phases)
    total_P = sum(p["P"] for p in phases)
    total_Q = sum(p["Q"] for p in phases)
    cos_phi_global = total_P / total_S if total_S > 0 else Constants.COS_PHI
    drops = [p["perc_drop"] for p in phases]
    avg_drop = sum(drops)/3
    max_drop = max(drops)
    min_drop = min(drops)
    max_phase = phases[drops.index(max_drop)]["phase"]
    if max_drop > Constants.VOLTAGE_DROP_CRITICAL:
        status, msg = "err", f"❌ Chute excessive sur phase {max_phase} ({max_drop:.2f}%)"
    elif max_drop > Constants.VOLTAGE_DROP_WARNING:
        status, msg = "warn", f"⚠️ Chute limite sur phase {max_phase} ({max_drop:.2f}%)"
    else:
        status, msg = "ok", "✓ Chutes conformes"
    recommendations = []
    if max_dev > Constants.UNBALANCE_WARNING:
        recommendations.append(f"Rééquilibrer les charges ({max_dev:.1f}%)")
    if max_drop > Constants.VOLTAGE_DROP_WARNING:
        worst_idx = drops.index(max_drop)
        worst_current = currents[worst_idx]
        s_min = (Constants.RESISTIVITY[material] * L * math.sqrt(3) * worst_current * Constants.COS_PHI) / (0.05 * tension_ref)
        rec_section = next((s for s in Constants.CABLE_SECTIONS if s >= s_min), Constants.CABLE_SECTIONS[-1])
        if rec_section > section:
            recommendations.append(f"Augmenter la section à {rec_section} mm²")
    return {
        "imbalance": {"max_deviation": max_dev, "status": imb_status, "message": imb_msg, "i_avg": i_avg, "deviations": deviations},
        "phases": phases,
        "total_current": sum(currents),
        "total_S": total_S, "total_P": total_P, "total_Q": total_Q,
        "cos_phi_global": cos_phi_global,
        "avg_drop": avg_drop, "max_drop": max_drop, "min_drop": min_drop, "max_drop_phase": max_phase,
        "status": status, "message": msg, "recommendations": recommendations
    }

# ── Main App ───────────────────────────────────────────────────────────────────
def main():
    load_css()
    st.markdown("""
    <div class="onee-header">
        <div class="onee-logo">ONEE</div>
        <div class="onee-title">Tech Assistant</div>
        <div class="onee-subtitle">Calculs électriques BT/MT</div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### ⚙️ Paramètres")
        st.markdown(f'<div class="cos-badge">cos φ = {Constants.COS_PHI}</div>', unsafe_allow_html=True)
        st.markdown("### 📐 Formule")
        st.latex(r"\Delta U = \sqrt{3} \times I \times (R \times \cos\phi + X \times \sin\phi)")
        st.caption(f"cos φ = {Constants.COS_PHI} (constant)")
        st.caption("X = 0.08 Ω/km")
        st.markdown("---")
        if st.session_state.res_t1:
            ch = st.session_state.res_t1['charge']
            if ch > 80: st.warning(f"Charge: {ch:.1f}%")
            else: st.success(f"Charge: {ch:.1f}%")
        if st.session_state.res_t2:
            md = st.session_state.res_t2['max_drop']
            if md > 5: st.error(f"Chute max: {md:.2f}%")
            elif md > 3: st.warning(f"Chute max: {md:.2f}%")
            else: st.success(f"Chute max: {md:.2f}%")
        st.markdown("---")
        st.markdown("### ℹ️ Normes")
        st.caption("NFC 11-201")
        st.caption("ΔU ≤ 3% (éclairage)")
        st.caption("ΔU ≤ 5% (force motrice)")

    tab1, tab2 = st.tabs(["🔌 Charge Transformateur", "📉 Chute de Tension"])

    # Tab 1: Transformer Load
    with tab1:
        with st.container():
            st.markdown('<div class="calc-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">🔌 Charge Transformateur</div>', unsafe_allow_html=True)
            st.info(f"📐 Facteur de puissance: cos φ = {Constants.COS_PHI}")
            col1, col2 = st.columns(2)
            with col1:
                s_nom = st.number_input("Puissance nominale (kVA)", min_value=1.0, value=100.0, step=10.0)
            with col2:
                p_reel = st.number_input("Puissance active (kW)", min_value=0.1, value=80.0, step=5.0)
            if st.button("Calculer la charge", key="btn_t1", use_container_width=True):
                st.session_state.res_t1 = calculate_transformer_load(s_nom, p_reel)
            if st.session_state.res_t1:
                r = st.session_state.res_t1
                st.markdown(f"""
                <div class="result-box result-{r['status']}">
                    <div class="result-label">TAUX DE CHARGE</div>
                    <div class="result-value">{r['charge']:.1f} %</div>
                    <div class="result-msg">{r['message']}</div>
                </div>
                """, unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                c1.metric("Puissance apparente", f"{r['s_reel']:.1f} kVA")
                c2.metric("Puissance réactive", f"{r['q_reel']:.1f} kVAR")
                c3.metric("cos φ", f"{r['cos_phi']:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

    # Tab 2: Voltage Drop with horizontal current inputs
    with tab2:
        with st.container():
            st.markdown('<div class="calc-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📉 Chute de Tension</div>', unsafe_allow_html=True)
            st.info(f"📐 Facteur de puissance constant: cos φ = {Constants.COS_PHI}")

            st.markdown("#### Courants par phase")
            # Horizontal layout for current inputs
            cols = st.columns(3)
            phase_labels = ["Phase 1", "Phase 2", "Phase 3"]
            default_currents = [65.0, 75.0, 45.0]
            currents = []
            for idx, (col, label, default) in enumerate(zip(cols, phase_labels, default_currents)):
                with col:
                    st.markdown(f'<div style="font-weight:700; margin-bottom:4px;">{label}</div>', unsafe_allow_html=True)
                    i_val = st.number_input("", min_value=0.0, value=default, step=5.0, key=f"i_{idx}", label_visibility="collapsed")
                    currents.append(i_val)

            st.markdown("---")
            st.markdown("#### Paramètres du câble")
            col1, col2 = st.columns(2)
            with col1:
                L = st.number_input("Longueur (m)", min_value=1.0, value=100.0, step=10.0)
                section = st.selectbox("Section (mm²)", Constants.CABLE_SECTIONS)
            with col2:
                material = st.radio("Matériau", list(Constants.RESISTIVITY.keys()), horizontal=True)
                network_type = st.selectbox("Réseau", ["Personnalisé"] + list(Constants.NETWORK_VOLTAGES.keys()))
                if network_type != "Personnalisé":
                    tension_ref = Constants.NETWORK_VOLTAGES[network_type]
                else:
                    tension_ref = st.number_input("Tension (V)", min_value=100.0, value=400.0, step=10.0)

            if st.button("Calculer la chute de tension", key="btn_t2", use_container_width=True):
                st.session_state.res_t2 = calculate_three_phase_unbalanced(
                    tuple(currents), L, section, material, tension_ref
                )

            if st.session_state.res_t2:
                r = st.session_state.res_t2
                # Imbalance
                st.markdown(f"""
                <div class="result-box result-{r['imbalance']['status']}">
                    <div class="result-label">DÉSÉQUILIBRE</div>
                    <div class="result-value">{r['imbalance']['max_deviation']:.1f} %</div>
                    <div class="result-msg">{r['imbalance']['message']}</div>
                </div>
                """, unsafe_allow_html=True)

                # Per phase drop
                st.markdown("#### Chutes par phase")
                cols = st.columns(3)
                for idx, col in enumerate(cols):
                    ph = r['phases'][idx]
                    color = "#D32F2F" if idx == 0 else "#1B5E20"
                    status_icon = "✅" if ph['perc_drop'] <= 3 else ("⚠️" if ph['perc_drop'] <= 5 else "❌")
                    with col:
                        st.markdown(f"""
                        <div style="background:#F8F9F8; border-radius:12px; padding:16px; margin:8px 0; border-left:4px solid {color};">
                            <div style="font-size:18px; font-weight:800; color:{color};">Phase {idx+1}</div>
                            <div><strong>Courant:</strong> {ph['current']:.1f} A</div>
                            <div><strong>Chute:</strong> <span style="font-size:24px; font-weight:800; color:{color};">{ph['perc_drop']:.2f}%</span> {status_icon}</div>
                            <div><strong>ΔU:</strong> {ph['delta_u']:.1f} V</div>
                            <div style="font-size:11px;">Résistif: {ph['delta_u_resistive']:.1f} V | Réactif: {ph['delta_u_reactive']:.1f} V</div>
                        </div>
                        """, unsafe_allow_html=True)

                # Global stats
                st.markdown("---")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Chute moyenne", f"{r['avg_drop']:.2f} %")
                c2.metric("Chute max", f"{r['max_drop']:.2f} %", delta=f"Phase {r['max_drop_phase']}")
                c3.metric("Chute min", f"{r['min_drop']:.2f} %")
                c4.metric("cos φ global", f"{r['cos_phi_global']:.3f}")

                # Power summary
                st.markdown("---")
                st.markdown("#### Bilan de puissance")
                c1, c2, c3 = st.columns(3)
                c1.metric("Puissance active", f"{r['total_P']:.1f} kW")
                c2.metric("Puissance réactive", f"{r['total_Q']:.1f} kVAR")
                c3.metric("Puissance apparente", f"{r['total_S']:.1f} kVA")

                if r['recommendations']:
                    st.warning("### 💡 Recommandations")
                    for rec in r['recommendations']:
                        st.write(f"• {rec}")
                else:
                    st.success("✓ Installation correcte")

                # Summary
                st.markdown(f"""
                <div class="result-box result-{r['status']}">
                    <div class="result-label">SYNTHÈSE</div>
                    <div class="result-msg">{r['message']}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div class="onee-footer">
        <span class="badge">ONEE Tech v2.1</span>
        <span class="badge">cos φ = {Constants.COS_PHI}</span>
        <span class="badge">NFC 11-201</span>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
