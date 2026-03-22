import streamlit as st
import math
import io
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, Optional, List, Any
import warnings
warnings.filterwarnings('ignore')

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ONEE Tech Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Constants ──────────────────────────────────────────────────────────────────
class Constants:
    RESISTIVITY = {
        "Cuivre (Cu)": 0.0225,
        "Aluminium (Al)": 0.036
    }
    
    REACTANCE = 0.08  # Ω/km
    COS_PHI = 0.9
    SIN_PHI = math.sqrt(1 - COS_PHI**2)
    
    CABLE_SECTIONS = [16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]
    
    NETWORK_VOLTAGES = {
        "Triphasé BT (400V)": 400.0,
        "Monophasé (230V)": 230.0,
        "MT (5500V)": 5500.0
    }
    
    CHARGE_WARNING = 80.0
    CHARGE_CRITICAL = 100.0
    VOLTAGE_DROP_WARNING = 3.0
    VOLTAGE_DROP_CRITICAL = 5.0
    UNBALANCE_WARNING = 20.0
    UNBALANCE_CRITICAL = 30.0

# ── Session state init ─────────────────────────────────────────────────────────
def init_session_state():
    defaults = {
        "res_t1": None,
        "res_t2": None,
        "calculation_history": []
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

init_session_state()

# ── Simple CSS with only 2 colors ──────────────────────────────────────────────
def load_simple_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main background */
    .stApp {
        background: #F5F5F5;
    }
    
    /* Header - DARK GREEN */
    .onee-header {
        background: #1B5E20;
        border-radius: 16px;
        padding: 32px 40px;
        margin-bottom: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .onee-logo {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 2px;
        color: #FFFFFF !important;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    
    .onee-title {
        font-size: 36px;
        font-weight: 800;
        color: #FFFFFF !important;
        line-height: 1.1;
        margin: 0;
    }
    
    .onee-subtitle {
        font-size: 14px;
        color: #E8F5E9 !important;
        margin-top: 8px;
    }
    
    /* Cards - WHITE background */
    .calc-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #E0E0E0;
    }
    
    .card-title {
        font-size: 22px;
        font-weight: 700;
        color: #1B5E20 !important;
        margin-bottom: 24px;
        padding-bottom: 12px;
        border-bottom: 2px solid #E8F5E9;
    }
    
    /* Phase cards - simple white with border */
    .phase-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid #E0E0E0;
    }
    
    .phase-title {
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 12px;
        padding-bottom: 6px;
        border-bottom: 2px solid;
    }
    
    /* Simple phase colors - only 2 colors */
    .phase-l1 {
        color: #D32F2F;
        border-bottom-color: #D32F2F;
    }
    
    .phase-l2, .phase-l3 {
        color: #1B5E20;
        border-bottom-color: #1B5E20;
    }
    
    /* Result boxes - only 2 colors */
    .result-box {
        border-radius: 12px;
        padding: 24px 28px;
        margin-top: 20px;
        border-left: 5px solid;
    }
    
    .result-ok {
        background: #E8F5E9;
        border-left-color: #1B5E20;
    }
    
    .result-warn {
        background: #FFF3E0;
        border-left-color: #FF9800;
    }
    
    .result-err {
        background: #FFEBEE;
        border-left-color: #D32F2F;
    }
    
    .result-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 8px;
        color: #5A6B5A !important;
    }
    
    .result-value {
        font-size: 48px;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 8px;
        color: #1A2A1A !important;
    }
    
    .result-msg {
        font-size: 13px;
        font-weight: 500;
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid rgba(0,0,0,0.08);
        color: #2C3E2C !important;
    }
    
    /* Metrics */
    [data-testid="metric-container"] {
        background: #F8F9F8;
        border-radius: 12px;
        padding: 16px !important;
        border: 1px solid #E0E0E0;
    }
    
    [data-testid="stMetricLabel"] {
        color: #1B5E20 !important;
        font-weight: 600 !important;
        font-size: 12px !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #1B5E20 !important;
        font-weight: 800 !important;
        font-size: 24px !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #E8F5E9;
        border-radius: 40px;
        padding: 4px;
        gap: 4px;
        margin-bottom: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 40px;
        font-weight: 600;
        font-size: 14px;
        padding: 10px 24px;
        color: #2C3E2C !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: #1B5E20 !important;
        color: white !important;
    }
    
    /* Inputs */
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > input {
        background: #FFFFFF !important;
        border: 1px solid #D0D0D0 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        color: #1A2A1A !important;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: #1B5E20 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: #1B5E20 !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 12px 24px !important;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: #0F4A13 !important;
    }
    
    /* Info/Warning boxes */
    .stInfo {
        background: #E3F2FD !important;
        border-left: 4px solid #2196F3 !important;
        border-radius: 10px !important;
    }
    
    .stWarning {
        background: #FFF3E0 !important;
        border-left: 4px solid #FF9800 !important;
        border-radius: 10px !important;
    }
    
    .stSuccess {
        background: #E8F5E9 !important;
        border-left: 4px solid #1B5E20 !important;
        border-radius: 10px !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }
    
    /* Footer */
    .onee-footer {
        text-align: center;
        padding: 24px;
        margin-top: 40px;
        border-top: 1px solid #E0E0E0;
        background: #FFFFFF;
        border-radius: 16px;
    }
    
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #E8F5E9;
        color: #1B5E20 !important;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        margin: 0 4px;
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
    
    /* Ensure all text is visible */
    p, div, span, label, .stMarkdown, .stText, .stAlert {
        color: #1A2A1A !important;
    }
    
    /* Streamlit specific fixes */
    .st-emotion-cache-1v0mbdj, .st-emotion-cache-1wivap2 {
        color: #1A2A1A !important;
    }
    
    @media (max-width: 768px) {
        .onee-title { font-size: 24px; }
        .result-value { font-size: 32px; }
        .calc-card { padding: 16px; }
    }
    
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# ── Calculation Functions ─────────────────────────────────────────────────────

def calculate_transformer_load(s_nom: float, p_reel: float) -> Dict[str, Any]:
    """Calculate transformer load with fixed cos φ = 0.9"""
    cos_phi = Constants.COS_PHI
    s_reel = p_reel / cos_phi
    charge = (s_reel / s_nom) * 100 if s_nom > 0 else 0
    q_reel = p_reel * math.tan(math.acos(cos_phi))
    
    if charge > Constants.CHARGE_CRITICAL:
        status = "err"
        message = "🚨 SURCHARGE CRITIQUE — Intervention immédiate requise"
    elif charge > Constants.CHARGE_WARNING:
        status = "warn"
        message = "⚡ Charge ÉLEVÉE — Surveillance recommandée"
    else:
        status = "ok"
        message = "✓ Charge NORMALE — Fonctionnement correct"
    
    return {
        "s_nom": s_nom,
        "p_reel": p_reel,
        "cos_phi": cos_phi,
        "s_reel": s_reel,
        "charge": charge,
        "q_reel": q_reel,
        "status": status,
        "message": message
    }

def calculate_voltage_drop_per_phase(
    i_phase: float,
    L: float,
    section: float,
    material: str,
    tension_ref: float
) -> Dict[str, Any]:
    """Calculate voltage drop with fixed cos φ = 0.9"""
    cos_phi = Constants.COS_PHI
    sin_phi = Constants.SIN_PHI
    
    rho = Constants.RESISTIVITY[material]
    R = (rho * L) / section
    X = Constants.REACTANCE * L / 1000
    
    delta_u = math.sqrt(3) * i_phase * (R * cos_phi + X * sin_phi)
    delta_u_resistive = math.sqrt(3) * i_phase * R * cos_phi
    delta_u_reactive = math.sqrt(3) * i_phase * X * sin_phi
    perc_drop = (delta_u / tension_ref) * 100
    
    S = i_phase * tension_ref / math.sqrt(3) / 1000
    P = S * cos_phi
    Q = S * sin_phi
    
    return {
        "delta_u": delta_u,
        "delta_u_resistive": delta_u_resistive,
        "delta_u_reactive": delta_u_reactive,
        "perc_drop": perc_drop,
        "R": R,
        "X": X,
        "S": S,
        "P": P,
        "Q": Q,
        "cos_phi": cos_phi
    }

def calculate_three_phase_unbalanced(
    currents: Tuple[float, float, float],
    L: float,
    section: float,
    material: str,
    tension_ref: float
) -> Dict[str, Any]:
    """Calculate unbalanced three-phase analysis"""
    
    # Phase imbalance
    i_avg = sum(currents) / 3
    if i_avg > 0:
        deviations = [(abs(i - i_avg) / i_avg) * 100 for i in currents]
        max_deviation = max(deviations)
        
        if max_deviation > Constants.UNBALANCE_CRITICAL:
            imbalance_status = "err"
            imbalance_msg = f"⚠️ DÉSÉQUILIBRE CRITIQUE ({max_deviation:.1f}%)"
        elif max_deviation > Constants.UNBALANCE_WARNING:
            imbalance_status = "warn"
            imbalance_msg = f"⚡ Déséquilibre modéré ({max_deviation:.1f}%)"
        else:
            imbalance_status = "ok"
            imbalance_msg = f"✓ Déséquilibre acceptable ({max_deviation:.1f}%)"
    else:
        max_deviation = 0
        imbalance_status = "ok"
        imbalance_msg = "Aucun courant mesuré"
        deviations = [0, 0, 0]
    
    # Per phase voltage drop
    phase_results = []
    for i, current in enumerate(currents):
        result = calculate_voltage_drop_per_phase(current, L, section, material, tension_ref)
        result["phase"] = i + 1
        result["current"] = current
        phase_results.append(result)
    
    # Global stats
    total_current = sum(currents)
    total_S = sum([r["S"] for r in phase_results])
    total_P = sum([r["P"] for r in phase_results])
    total_Q = sum([r["Q"] for r in phase_results])
    cos_phi_global = total_P / total_S if total_S > 0 else Constants.COS_PHI
    
    avg_drop = sum([r["perc_drop"] for r in phase_results]) / 3
    max_drop = max([r["perc_drop"] for r in phase_results])
    min_drop = min([r["perc_drop"] for r in phase_results])
    max_drop_phase = phase_results[[r["perc_drop"] for r in phase_results].index(max_drop)]["phase"]
    
    # Overall status
    if max_drop > Constants.VOLTAGE_DROP_CRITICAL:
        status = "err"
        message = f"❌ Chute excessive sur phase {max_drop_phase} ({max_drop:.2f}%)"
    elif max_drop > Constants.VOLTAGE_DROP_WARNING:
        status = "warn"
        message = f"⚠️ Chute limite sur phase {max_drop_phase} ({max_drop:.2f}%)"
    else:
        status = "ok"
        message = f"✓ Chutes conformes"
    
    # Recommendations
    recommendations = []
    if max_deviation > Constants.UNBALANCE_WARNING:
        recommendations.append(f"Rééquilibrer les charges (déséquilibre: {max_deviation:.1f}%)")
    if max_drop > Constants.VOLTAGE_DROP_WARNING:
        worst_idx = [r["perc_drop"] for r in phase_results].index(max_drop)
        worst_current = currents[worst_idx]
        s_min = (Constants.RESISTIVITY[material] * L * math.sqrt(3) * worst_current * Constants.COS_PHI) / (0.05 * tension_ref)
        recommended_section = next((s for s in Constants.CABLE_SECTIONS if s >= s_min), Constants.CABLE_SECTIONS[-1])
        if recommended_section > section:
            recommendations.append(f"Augmenter la section à {recommended_section} mm²")
    
    return {
        "imbalance": {
            "max_deviation": max_deviation,
            "status": imbalance_status,
            "message": imbalance_msg,
            "i_avg": i_avg,
            "deviations": deviations
        },
        "phases": phase_results,
        "total_current": total_current,
        "total_S": total_S,
        "total_P": total_P,
        "total_Q": total_Q,
        "cos_phi_global": cos_phi_global,
        "avg_drop": avg_drop,
        "max_drop": max_drop,
        "min_drop": min_drop,
        "max_drop_phase": max_drop_phase,
        "status": status,
        "message": message,
        "recommendations": recommendations
    }

# ── Main App ───────────────────────────────────────────────────────────────────
def main():
    load_simple_css()
    
    # Header
    st.markdown("""
    <div class="onee-header">
        <div class="onee-logo">ONEE</div>
        <div class="onee-title">Tech Assistant</div>
        <div class="onee-subtitle">Calculs électriques BT/MT</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Paramètres")
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <div class="cos-badge">cos φ = {Constants.COS_PHI}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📐 Formule")
        st.latex(r"\Delta U = \sqrt{3} \times I \times (R \times \cos\phi + X \times \sin\phi)")
        st.caption(f"cos φ = {Constants.COS_PHI} (constant)")
        st.caption("X = 0.08 Ω/km")
        
        st.markdown("---")
        st.markdown("### 📊 État")
        
        if st.session_state.res_t1:
            charge = st.session_state.res_t1['charge']
            if charge > 80:
                st.warning(f"Charge: {charge:.1f}%")
            else:
                st.success(f"Charge: {charge:.1f}%")
        
        if st.session_state.res_t2:
            max_drop = st.session_state.res_t2['max_drop']
            if max_drop > 5:
                st.error(f"Chute max: {max_drop:.2f}%")
            elif max_drop > 3:
                st.warning(f"Chute max: {max_drop:.2f}%")
            else:
                st.success(f"Chute max: {max_drop:.2f}%")
        
        st.markdown("---")
        st.markdown("### ℹ️ Normes")
        st.caption("NFC 11-201")
        st.caption("ΔU ≤ 3% (éclairage)")
        st.caption("ΔU ≤ 5% (force motrice)")
    
    # Tabs
    tab1, tab2 = st.tabs(["🔌 Charge Transformateur", "📉 Chute de Tension"])
    
    # Tab 1: Transformer Load
    with tab1:
        st.markdown('<div class="calc-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🔌 Charge Transformateur</div>', unsafe_allow_html=True)
        
        st.info(f"📐 Facteur de puissance: cos φ = {Constants.COS_PHI}")
        
        col1, col2 = st.columns(2)
        with col1:
            s_nom = st.number_input("Puissance nominale (kVA)", min_value=1.0, value=100.0, step=10.0)
        with col2:
            p_reel = st.number_input("Puissance active (kW)", min_value=0.1, value=80.0, step=5.0)
        
        if st.button("Calculer la charge", key="btn_t1", use_container_width=True):
            result = calculate_transformer_load(s_nom, p_reel)
            st.session_state.res_t1 = result
        
        if st.session_state.res_t1:
            result = st.session_state.res_t1
            box_class = f"result-{result['status']}"
            
            st.markdown(f"""
            <div class="result-box {box_class}">
                <div class="result-label">TAUX DE CHARGE</div>
                <div class="result-value">{result['charge']:.1f} %</div>
                <div class="result-msg">{result['message']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Puissance apparente", f"{result['s_reel']:.1f} kVA")
            col2.metric("Puissance réactive", f"{result['q_reel']:.1f} kVAR")
            col3.metric("cos φ", f"{result['cos_phi']:.2f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 2: Voltage Drop
    with tab2:
        st.markdown('<div class="calc-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📉 Chute de Tension</div>', unsafe_allow_html=True)
        
        st.info(f"📐 Facteur de puissance constant: cos φ = {Constants.COS_PHI}")
        
        st.markdown("#### Courants par phase")
        cols = st.columns(3)
        
        phase_names = ["Phase L1", "Phase L2", "Phase L3"]
        phase_colors = ["#D32F2F", "#1B5E20", "#1B5E20"]
        default_currents = [65.0, 75.0, 45.0]
        
        currents = []
        for idx, (col, name, color, default) in enumerate(zip(cols, phase_names, phase_colors, default_currents)):
            with col:
                st.markdown(f"""
                <div class="phase-card">
                    <div class="phase-title phase-l{idx+1}" style="color: {color}; border-bottom-color: {color}">
                        {name}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                i_val = st.number_input(f"Courant (A)", min_value=0.0, value=default, step=5.0, key=f"i_{idx}")
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
            result = calculate_three_phase_unbalanced(tuple(currents), L, section, material, tension_ref)
            st.session_state.res_t2 = result
        
        if st.session_state.res_t2:
            result = st.session_state.res_t2
            
            # Imbalance
            imbalance_class = f"result-{result['imbalance']['status']}"
            st.markdown(f"""
            <div class="result-box {imbalance_class}">
                <div class="result-label">DÉSÉQUILIBRE</div>
                <div class="result-value">{result['imbalance']['max_deviation']:.1f} %</div>
                <div class="result-msg">{result['imbalance']['message']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Per phase voltage drop
            st.markdown("#### Chutes par phase")
            cols = st.columns(3)
            
            for idx, (col, phase) in enumerate(zip(cols, result['phases'])):
                color = "#D32F2F" if idx == 0 else "#1B5E20"
                if phase['perc_drop'] <= 3:
                    status_icon = "✅"
                elif phase['perc_drop'] <= 5:
                    status_icon = "⚠️"
                else:
                    status_icon = "❌"
                
                with col:
                    st.markdown(f"""
                    <div style="background: #F8F9F8; border-radius: 12px; padding: 16px; margin: 8px 0; border-left: 4px solid {color};">
                        <div style="font-size: 18px; font-weight: 800; color: {color}; margin-bottom: 12px;">
                            Phase L{idx+1}
                        </div>
                        <div><strong>Courant:</strong> {phase['current']:.1f} A</div>
                        <div><strong>Chute:</strong> <span style="font-size: 24px; font-weight: 800; color: {color};">{phase['perc_drop']:.2f}%</span> {status_icon}</div>
                        <div><strong>ΔU:</strong> {phase['delta_u']:.1f} V</div>
                        <div style="font-size: 11px; margin-top: 8px;">Résistif: {phase['delta_u_resistive']:.1f} V | Réactif: {phase['delta_u_reactive']:.1f} V</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Global stats
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Chute moyenne", f"{result['avg_drop']:.2f} %")
            col2.metric("Chute max", f"{result['max_drop']:.2f} %", delta=f"Phase {result['max_drop_phase']}")
            col3.metric("Chute min", f"{result['min_drop']:.2f} %")
            col4.metric("cos φ global", f"{result['cos_phi_global']:.3f}")
            
            # Power summary
            st.markdown("---")
            st.markdown("#### Bilan de puissance")
            col1, col2, col3 = st.columns(3)
            col1.metric("Puissance active", f"{result['total_P']:.1f} kW")
            col2.metric("Puissance réactive", f"{result['total_Q']:.1f} kVAR")
            col3.metric("Puissance apparente", f"{result['total_S']:.1f} kVA")
            
            # Recommendations
            if result['recommendations']:
                st.warning("### 💡 Recommandations")
                for rec in result['recommendations']:
                    st.write(f"• {rec}")
            else:
                st.success("✓ Installation correcte")
            
            # Summary
            summary_class = f"result-{result['status']}"
            st.markdown(f"""
            <div class="result-box {summary_class}">
                <div class="result-label">SYNTHÈSE</div>
                <div class="result-msg">{result['message']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown(f"""
    <div class="onee-footer">
        <span class="badge">ONEE Tech v2.0</span>
        <span class="badge">cos φ = {Constants.COS_PHI}</span>
        <span class="badge">NFC 11-201</span>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
