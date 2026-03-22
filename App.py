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
    page_title="ONEE Tech Assistant - Réseaux Triphasés",
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
    
    # Réactance approximative des câbles (Ω/km)
    REACTANCE = 0.08
    
    # Facteur de puissance constant pour tous les calculs
    COS_PHI = 0.9
    SIN_PHI = math.sqrt(1 - COS_PHI**2)  # sin(arccos(0.9)) = 0.4359
    
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

# ── Enhanced CSS with HIGH VISIBILITY colors ───────────────────────────────────
def load_enhanced_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #F5F7FA 0%, #E8EDF2 100%);
    }
    
    /* Header with STRONG GREEN */
    .onee-header {
        background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);
        border-radius: 24px;
        padding: 40px 48px;
        margin-bottom: 32px;
        box-shadow: 0 20px 40px -12px rgba(0,0,0,0.25);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .onee-header::before {
        content: '⚡';
        position: absolute;
        right: 40px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 120px;
        opacity: 0.1;
    }
    
    .onee-logo {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 3px;
        color: #FFFFFF;
        text-transform: uppercase;
        margin-bottom: 12px;
        opacity: 0.9;
    }
    
    .onee-title {
        font-size: 42px;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1.1;
        margin: 0;
    }
    
    .onee-subtitle {
        font-size: 15px;
        color: #FFFFFF;
        margin-top: 12px;
        opacity: 0.9;
    }
    
    /* Cards */
    .calc-card {
        background: #FFFFFF;
        border-radius: 24px;
        padding: 32px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border: 1px solid #E0E7E0;
    }
    
    .card-title {
        font-size: 24px;
        font-weight: 700;
        color: #1B5E20;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 2px solid #C8E6C9;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .card-title::before {
        content: '';
        width: 4px;
        height: 28px;
        background: #FFA000;
        border-radius: 2px;
    }
    
    /* Phase cards with VIVID colors */
    .phase-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        border: 2px solid #E0E7E0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .phase-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    
    .phase-title {
        font-size: 20px;
        font-weight: 800;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 3px solid;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* VIVID PHASE COLORS */
    .phase-l1 {
        color: #D32F2F;
        border-bottom-color: #D32F2F;
    }
    
    .phase-l2 {
        color: #388E3C;
        border-bottom-color: #388E3C;
    }
    
    .phase-l3 {
        color: #F57C00;
        border-bottom-color: #F57C00;
    }
    
    .phase-value {
        font-size: 24px;
        font-weight: 700;
        margin: 8px 0;
        color: #1F2A1F;
    }
    
    .phase-label {
        font-size: 11px;
        color: #6B7C6B;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Result boxes with CLEAR colors */
    .result-box {
        border-radius: 20px;
        padding: 28px 32px;
        margin-top: 24px;
        animation: slideInUp 0.5s ease;
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .result-ok {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-left: 6px solid #2E7D32;
    }
    
    .result-warn {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        border-left: 6px solid #FFA000;
    }
    
    .result-err {
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        border-left: 6px solid #D32F2F;
    }
    
    .result-label {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 8px;
        color: #374D37;
    }
    
    .result-value {
        font-size: 56px;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 12px;
        color: #1F2A1F;
    }
    
    .result-msg {
        font-size: 14px;
        font-weight: 500;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid rgba(0,0,0,0.1);
        color: #374D37;
    }
    
    /* Metrics with CLEAR styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #F8F9F8 0%, #FFFFFF 100%);
        border-radius: 16px;
        padding: 20px !important;
        border: 1px solid #C8E6C9;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    [data-testid="stMetricLabel"] {
        color: #2E7D32 !important;
        font-weight: 700 !important;
        font-size: 13px !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #1B5E20 !important;
        font-weight: 800 !important;
        font-size: 28px !important;
    }
    
    /* Tabs with VIBRANT colors */
    .stTabs [data-baseweb="tab-list"] {
        background: #E8F0E8;
        border-radius: 60px;
        padding: 6px;
        gap: 8px;
        margin-bottom: 32px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 50px;
        font-weight: 600;
        font-size: 15px;
        padding: 12px 28px;
        color: #4A5B4A;
    }
    
    .stTabs [aria-selected="true"] {
        background: #2E7D32 !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(46,125,50,0.3);
    }
    
    /* Inputs */
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > input {
        background: #FFFFFF !important;
        border: 2px solid #C8E6C9 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: #2E7D32 !important;
        box-shadow: 0 0 0 3px rgba(46,125,50,0.1) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: #2E7D32 !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        padding: 14px 32px !important;
        width: 100%;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: #1B5E20 !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(46,125,50,0.4) !important;
    }
    
    /* Info boxes */
    .stInfo {
        background: #E3F2FD !important;
        border-left: 4px solid #1976D2 !important;
        border-radius: 12px !important;
    }
    
    .stWarning {
        background: #FFF3E0 !important;
        border-left: 4px solid #FFA000 !important;
        border-radius: 12px !important;
    }
    
    .stSuccess {
        background: #E8F5E9 !important;
        border-left: 4px solid #2E7D32 !important;
        border-radius: 12px !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E0E7E0;
    }
    
    /* Footer */
    .onee-footer {
        text-align: center;
        padding: 32px;
        margin-top: 48px;
        border-top: 1px solid #E0E7E0;
        background: #FFFFFF;
        border-radius: 24px;
    }
    
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #E8F5E9;
        color: #2E7D32;
        font-size: 11px;
        font-weight: 700;
        padding: 6px 12px;
        border-radius: 30px;
        margin: 0 4px;
    }
    
    .cos-badge {
        background: #FFE0B2;
        color: #F57C00;
        font-size: 14px;
        font-weight: 800;
        padding: 8px 16px;
        border-radius: 40px;
        display: inline-block;
    }
    
    @media (max-width: 768px) {
        .onee-title { font-size: 28px; }
        .result-value { font-size: 36px; }
        .calc-card { padding: 20px; }
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
        message = "🚨 SURCHARGE CRITIQUE — Risque de détérioration du transformateur"
    elif charge > Constants.CHARGE_WARNING:
        status = "warn"
        message = "⚡ Charge ÉLEVÉE — Prévoir renforcement"
    else:
        status = "ok"
        message = "✓ Charge NORMALE — Fonctionnement optimal"
    
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
    """
    Calculate voltage drop for a single phase with fixed cos φ = 0.9
    Formule: ΔU = √3 × I × (R × cosφ + X × sinφ)
    """
    cos_phi = Constants.COS_PHI
    sin_phi = Constants.SIN_PHI
    
    rho = Constants.RESISTIVITY[material]
    R = (rho * L) / section  # Résistance en ohms
    X = Constants.REACTANCE * L / 1000  # Réactance en ohms
    
    # Chute de tension complète avec cos φ
    delta_u = math.sqrt(3) * i_phase * (R * cos_phi + X * sin_phi)
    
    # Composantes séparées
    delta_u_resistive = math.sqrt(3) * i_phase * R * cos_phi
    delta_u_reactive = math.sqrt(3) * i_phase * X * sin_phi
    
    perc_drop = (delta_u / tension_ref) * 100
    
    # Puissances par phase
    S = i_phase * tension_ref / math.sqrt(3) / 1000  # kVA
    P = S * cos_phi  # kW
    Q = S * sin_phi  # kVAR
    
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
        "cos_phi": cos_phi,
        "sin_phi": sin_phi
    }

def calculate_three_phase_unbalanced(
    currents: Tuple[float, float, float],
    L: float,
    section: float,
    material: str,
    tension_ref: float
) -> Dict[str, Any]:
    """Calculate complete unbalanced three-phase system analysis"""
    
    # Phase imbalance calculation
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
    
    # Per phase voltage drop
    phase_results = []
    for i, current in enumerate(currents):
        result = calculate_voltage_drop_per_phase(
            current, L, section, material, tension_ref
        )
        result["phase"] = i + 1
        result["current"] = current
        phase_results.append(result)
    
    # Global parameters
    total_current = sum(currents)
    total_S = sum([r["S"] for r in phase_results])
    total_P = sum([r["P"] for r in phase_results])
    total_Q = sum([r["Q"] for r in phase_results])
    
    # Global power factor
    cos_phi_global = total_P / total_S if total_S > 0 else Constants.COS_PHI
    
    # Voltage drop statistics
    avg_drop = sum([r["perc_drop"] for r in phase_results]) / 3
    max_drop = max([r["perc_drop"] for r in phase_results])
    min_drop = min([r["perc_drop"] for r in phase_results])
    max_drop_phase = phase_results[[r["perc_drop"] for r in phase_results].index(max_drop)]["phase"]
    
    # Overall status
    if max_drop > Constants.VOLTAGE_DROP_CRITICAL:
        status = "err"
        message = f"❌ Chute excessive sur phase {max_drop_phase} ({max_drop:.2f}%) — Non conforme"
    elif max_drop > Constants.VOLTAGE_DROP_WARNING:
        status = "warn"
        message = f"⚠️ Chute limite sur phase {max_drop_phase} ({max_drop:.2f}%) — Vérifier dimensionnement"
    else:
        status = "ok"
        message = f"✓ Chutes conformes — Installation correcte"
    
    # Recommendations
    recommendations = []
    if max_deviation > Constants.UNBALANCE_WARNING:
        recommendations.append(f"Rééquilibrer les charges (déséquilibre: {max_deviation:.1f}%)")
    if max_drop > Constants.VOLTAGE_DROP_WARNING:
        worst_idx = [r["perc_drop"] for r in phase_results].index(max_drop)
        worst_current = currents[worst_idx]
        s_min = (Constants.RESISTIVITY[material] * L * math.sqrt(3) * worst_current * Constants.COS_PHI) / (0.05 * tension_ref)
        recommended_section = next((s for s in Constants.CABLE_SECTIONS if s >= s_min), 
                                   Constants.CABLE_SECTIONS[-1])
        if recommended_section > section:
            recommendations.append(f"Augmenter la section du câble à {recommended_section} mm² (actuel: {section} mm²)")
    
    return {
        "imbalance": {
            "max_deviation": max_deviation,
            "status": imbalance_status,
            "message": imbalance_msg,
            "i_avg": i_avg,
            "deviations": deviations if i_avg > 0 else [0, 0, 0]
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
    load_enhanced_css()
    
    # Header
    st.markdown("""
    <div class="onee-header">
        <div class="onee-logo">Office National de l'Electricité et de l'Eau Potable</div>
        <div class="onee-title">ONEE Tech Assistant</div>
        <div class="onee-subtitle">Calculs électriques pour réseaux de distribution BT/MT</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Paramètres constants")
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <div class="cos-badge" style="background: #FFE0B2; color: #F57C00; font-size: 18px; padding: 12px 24px;">
                cos φ = {Constants.COS_PHI}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📐 Formule utilisée")
        st.latex(r"\Delta U = \sqrt{3} \times I \times (R \times \cos\phi + X \times \sin\phi)")
        st.caption(f"Avec cos φ = {Constants.COS_PHI} (constant)")
        st.caption("X = 0.08 Ω/km (réactance du câble)")
        
        st.markdown("---")
        st.markdown("### 📊 Tableau de bord")
        
        if st.session_state.res_t1:
            charge = st.session_state.res_t1['charge']
            if charge > 80:
                st.warning(f"Charge: {charge:.1f}%")
            else:
                st.success(f"Charge: {charge:.1f}%")
        
        if st.session_state.res_t2:
            imbalance = st.session_state.res_t2['imbalance']['max_deviation']
            max_drop = st.session_state.res_t2['max_drop']
            st.info(f"Déséquilibre: {imbalance:.1f}%")
            if max_drop > 5:
                st.error(f"Chute max: {max_drop:.2f}%")
            elif max_drop > 3:
                st.warning(f"Chute max: {max_drop:.2f}%")
            else:
                st.success(f"Chute max: {max_drop:.2f}%")
        
        st.markdown("---")
        st.markdown("### ℹ️ Normes")
        st.caption("NFC 11-201: ΔU ≤ 3% (éclairage), ≤ 5% (force motrice)")
        st.caption("Déséquilibre recommandé < 20%")
    
    # Tabs
    tab1, tab2 = st.tabs(["🔌 Charge Transformateur", "📉 Chute de Tension Triphasée"])
    
    # Tab 1: Transformer Load
    with tab1:
        with st.container():
            st.markdown('<div class="calc-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">🔌 Calcul de charge du transformateur</div>', unsafe_allow_html=True)
            
            st.info(f"📐 Facteur de puissance constant: **cos φ = {Constants.COS_PHI}**")
            
            col1, col2 = st.columns(2)
            with col1:
                s_nom = st.number_input(
                    "Puissance nominale (kVA)",
                    min_value=1.0, value=100.0, step=10.0,
                    help="Puissance apparente nominale du transformateur"
                )
            with col2:
                p_reel = st.number_input(
                    "Puissance active réelle (kW)",
                    min_value=0.1, value=80.0, step=5.0,
                    help="Puissance active mesurée en service"
                )
            
            if st.button("⚡ Calculer la charge", key="btn_t1", use_container_width=True):
                with st.spinner("Calcul en cours..."):
                    result = calculate_transformer_load(s_nom, p_reel)
                    st.session_state.res_t1 = result
            
            if st.session_state.res_t1:
                result = st.session_state.res_t1
                
                box_class = f"result-{result['status']}"
                st.markdown(f"""
                <div class="result-box {box_class}">
                    <div class="result-label">📊 TAUX DE CHARGE</div>
                    <div class="result-value">{result['charge']:.1f} %</div>
                    <div class="result-msg">{result['message']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                col1.metric("Puissance apparente", f"{result['s_reel']:.2f} kVA")
                col2.metric("Puissance réactive", f"{result['q_reel']:.2f} kVAR")
                col3.metric("cos φ", f"{result['cos_phi']:.2f}")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 2: Voltage Drop
    with tab2:
        with st.container():
            st.markdown('<div class="calc-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📉 Chute de tension en régime triphasé</div>', unsafe_allow_html=True)
            
            st.info(f"📐 Facteur de puissance constant: **cos φ = {Constants.COS_PHI}** | sin φ = {Constants.SIN_PHI:.4f}")
            
            st.markdown("#### ⚡ Courants par phase")
            
            # Phase inputs with VIVID colors
            cols = st.columns(3)
            
            phase_configs = [
                {"name": "Phase L1", "color": "#D32F2F", "bg": "#FFEBEE", "icon": "🔴", "default": 65.0},
                {"name": "Phase L2", "color": "#388E3C", "bg": "#E8F5E9", "icon": "🟢", "default": 75.0},
                {"name": "Phase L3", "color": "#F57C00", "bg": "#FFF3E0", "icon": "🟠", "default": 45.0}
            ]
            
            currents = []
            for idx, (col, config) in enumerate(zip(cols, phase_configs)):
                with col:
                    st.markdown(f"""
                    <div class="phase-card">
                        <div class="phase-title" style="color: {config['color']}; border-bottom-color: {config['color']};">
                            {config['icon']} {config['name']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    i_val = st.number_input(
                        f"Courant (A)", 
                        min_value=0.0, 
                        value=config['default'], 
                        step=5.0, 
                        key=f"i_{idx+1}",
                        help=f"Courant mesuré sur {config['name']}"
                    )
                    currents.append(i_val)
            
            st.markdown("---")
            st.markdown("#### 🔌 Paramètres du câble")
            
            col1, col2 = st.columns(2)
            with col1:
                L = st.number_input("Longueur du câble (m)", min_value=1.0, value=100.0, step=10.0)
                section = st.selectbox("Section du câble (mm²)", Constants.CABLE_SECTIONS)
            with col2:
                material = st.radio("Matériau conducteur", list(Constants.RESISTIVITY.keys()), horizontal=True)
                network_type = st.selectbox("Type de réseau", ["Personnalisé"] + list(Constants.NETWORK_VOLTAGES.keys()))
                if network_type != "Personnalisé":
                    tension_ref = Constants.NETWORK_VOLTAGES[network_type]
                else:
                    tension_ref = st.number_input("Tension (V)", min_value=100.0, value=400.0, step=10.0)
            
            if st.button("⚡ Calculer la chute de tension", key="btn_t2", use_container_width=True):
                with st.spinner("Calcul en cours..."):
                    result = calculate_three_phase_unbalanced(
                        tuple(currents), L, section, material, tension_ref
                    )
                    st.session_state.res_t2 = result
            
            if st.session_state.res_t2:
                result = st.session_state.res_t2
                
                # Imbalance analysis
                imbalance_status = result['imbalance']['status']
                st.markdown(f"""
                <div class="result-box result-{imbalance_status}">
                    <div class="result-label">⚖️ DÉSÉQUILIBRE DE PHASES</div>
                    <div class="result-value">{result['imbalance']['max_deviation']:.1f} %</div>
                    <div class="result-msg">{result['imbalance']['message']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Per phase voltage drop
                st.markdown("#### 📉 Chutes de tension par phase")
                cols = st.columns(3)
                
                phase_colors = ["#D32F2F", "#388E3C", "#F57C00"]
                phase_icons = ["🔴", "🟢", "🟠"]
                
                for idx, (col, color, icon) in enumerate(zip(cols, phase_colors, phase_icons)):
                    phase = result['phases'][idx]
                    
                    # Status indicator
                    if phase['perc_drop'] <= 3:
                        status_icon = "✅"
                        status_text = "Conforme"
                    elif phase['perc_drop'] <= 5:
                        status_icon = "⚠️"
                        status_text = "Limite"
                    else:
                        status_icon = "❌"
                        status_text = "Non conforme"
                    
                    with col:
                        st.markdown(f"""
                        <div style="background: #FFFFFF; border-radius: 16px; padding: 20px; margin: 8px 0; border-left: 6px solid {color}; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <div style="font-size: 18px; font-weight: 800; color: {color}; margin-bottom: 12px;">
                                {icon} Phase L{idx+1}
                            </div>
                            <div style="margin: 10px 0;">
                                <span style="font-size: 12px; color: #6B7C6B;">Courant:</span>
                                <span style="font-size: 24px; font-weight: 800; color: #1F2A1F;"> {phase['current']:.1f} A</span>
                            </div>
                            <div style="margin: 10px 0;">
                                <span style="font-size: 12px; color: #6B7C6B;">Chute de tension:</span>
                                <span style="font-size: 28px; font-weight: 800; color: {color};"> {phase['perc_drop']:.2f}%</span>
                                <span style="font-size: 18px;"> {status_icon}</span>
                            </div>
                            <div style="margin: 8px 0;">
                                <span style="font-size: 12px; color: #6B7C6B;">ΔU total:</span>
                                <span style="font-size: 16px; font-weight: 600;"> {phase['delta_u']:.1f} V</span>
                            </div>
                            <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #E8F0E8;">
                                <span style="font-size: 10px; color: #6B7C6B;">Résistif: {phase['delta_u_resistive']:.1f} V | Réactif: {phase['delta_u_reactive']:.1f} V</span>
                            </div>
                            <div style="margin-top: 4px;">
                                <span style="font-size: 10px; color: #6B7C6B;">P: {phase['P']:.1f} kW | Q: {phase['Q']:.1f} kVAR</span>
                            </div>
                            <div style="margin-top: 4px;">
                                <span style="font-size: 10px; color: #6B7C6B;">cos φ = {Constants.COS_PHI}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Global statistics
                st.markdown("---")
                st.markdown("#### 📊 Statistiques globales")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Courant total", f"{result['total_current']:.1f} A")
                col2.metric("Chute moyenne", f"{result['avg_drop']:.2f} %")
                col3.metric("Chute maximale", f"{result['max_drop']:.2f} %", delta=f"Phase {result['max_drop_phase']}")
                col4.metric("cos φ global", f"{result['cos_phi_global']:.3f}")
                
                # Power summary
                st.markdown("---")
                st.markdown("#### ⚡ Bilan de puissance")
                col1, col2, col3 = st.columns(3)
                col1.metric("Puissance active totale", f"{result['total_P']:.1f} kW")
                col2.metric("Puissance réactive totale", f"{result['total_Q']:.1f} kVAR")
                col3.metric("Puissance apparente totale", f"{result['total_S']:.1f} kVA")
                
                # Recommendations
                if result['recommendations']:
                    st.markdown("---")
                    st.warning("### 💡 Recommandations")
                    for rec in result['recommendations']:
                        st.write(f"• {rec}")
                else:
                    st.markdown("---")
                    st.success("✓ Aucune recommandation corrective nécessaire")
                
                # Summary
                summary_class = f"result-{result['status']}"
                st.markdown(f"""
                <div class="result-box {summary_class}">
                    <div class="result-label">📋 SYNTHÈSE</div>
                    <div class="result-msg">{result['message']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown(f"""
    <div class="onee-footer">
        <span class="badge">⚡ ONEE Tech v2.2</span>
        <span class="badge">📊 cos φ = {Constants.COS_PHI}</span>
        <span class="badge">📐 ΔU = √3 × I × (R×cosφ + X×sinφ)</span>
        <br/><br/>
        <small>Outil professionnel de calculs électriques — Conforme aux normes NFC 11-201</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
