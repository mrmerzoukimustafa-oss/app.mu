import streamlit as st
import math
import io
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional, List, Any
import warnings
warnings.filterwarnings('ignore')

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ONEE Tech Assistant - Réseaux Triphasés Déséquilibrés",
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
    UNBALANCE_WARNING = 20.0  # % de déséquilibre maximum recommandé
    UNBALANCE_CRITICAL = 30.0

# ── Session state init ─────────────────────────────────────────────────────────
def init_session_state():
    defaults = {
        "res_t1": None,
        "res_t2": None,
        "calculation_history": [],
        "theme": "light",
        "show_advanced": True
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

init_session_state()

# ── Enhanced CSS ─────────────────────────────────────────────────────────────────
def load_enhanced_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #F8FAF5 0%, #F0F4EA 100%);
    }
    
    /* Glass morphism header */
    .onee-header {
        background: linear-gradient(135deg, rgba(0,121,59,0.95) 0%, rgba(0,80,31,0.95) 100%);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 40px 48px;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 40px -12px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .onee-header::before {
        content: '⚡';
        position: absolute;
        right: 40px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 120px;
        opacity: 0.08;
        animation: pulse 3s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.08; transform: translateY(-50%) scale(1); }
        50% { opacity: 0.12; transform: translateY(-50%) scale(1.05); }
    }
    
    .onee-logo {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 3px;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    
    .onee-title {
        font-size: 42px;
        font-weight: 800;
        color: white;
        line-height: 1.1;
        margin: 0;
        background: linear-gradient(135deg, #FFFFFF 0%, #E8F5EE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .onee-subtitle {
        font-size: 15px;
        color: rgba(255,255,255,0.8);
        margin-top: 12px;
    }
    
    /* Modern cards */
    .calc-card {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 32px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border: 1px solid rgba(255,255,255,0.5);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .calc-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 48px rgba(0,0,0,0.12);
    }
    
    .card-title {
        font-size: 24px;
        font-weight: 700;
        background: linear-gradient(135deg, #00793B 0%, #00501F 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 2px solid #E8F5EE;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .card-title::before {
        content: '';
        width: 4px;
        height: 28px;
        background: linear-gradient(135deg, #F4A800, #FFC107);
        border-radius: 2px;
    }
    
    /* Phase cards */
    .phase-card {
        background: linear-gradient(135deg, #F8FAF5 0%, #FFFFFF 100%);
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #E8F5EE;
        transition: all 0.3s ease;
    }
    
    .phase-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,121,59,0.1);
        border-color: #00793B;
    }
    
    .phase-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid #E8F5EE;
    }
    
    .phase-l1 { color: #FF6B6B; border-left: 3px solid #FF6B6B; padding-left: 12px; }
    .phase-l2 { color: #4ECDC4; border-left: 3px solid #4ECDC4; padding-left: 12px; }
    .phase-l3 { color: #FFE66D; border-left: 3px solid #FFE66D; padding-left: 12px; }
    
    /* Result boxes */
    .result-box {
        border-radius: 20px;
        padding: 28px 32px;
        margin-top: 24px;
        position: relative;
        overflow: hidden;
        animation: slideInUp 0.5s cubic-bezier(0.4, 0, 0.2, 1);
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
        background: linear-gradient(135deg, #E8F5EE 0%, #D4E8DA 100%);
        border-left: 4px solid #00793B;
    }
    
    .result-warn {
        background: linear-gradient(135deg, #FFF8E1 0%, #FFEFB9 100%);
        border-left: 4px solid #F4A800;
    }
    
    .result-err {
        background: linear-gradient(135deg, #FFEBEE 0%, #FFDADF 100%);
        border-left: 4px solid #D32F2F;
    }
    
    .result-label {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 8px;
        opacity: 0.7;
    }
    
    .result-value {
        font-size: 56px;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 12px;
    }
    
    .result-msg {
        font-size: 14px;
        font-weight: 500;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid rgba(0,0,0,0.1);
    }
    
    /* Metrics */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #F8FAF5 0%, #FFFFFF 100%);
        border-radius: 16px;
        padding: 20px !important;
        border: 1px solid #E8F5EE;
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,121,59,0.12);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(232, 245, 238, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 60px;
        padding: 6px;
        gap: 8px;
        border: 1px solid rgba(255,255,255,0.5);
        margin-bottom: 32px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 50px;
        font-weight: 600;
        font-size: 15px;
        padding: 12px 28px;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00793B 0%, #00501F 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(0,121,59,0.3);
    }
    
    /* Inputs */
    .stNumberInput > div > div > input {
        background: white !important;
        border: 2px solid #E8F5EE !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: #00793B !important;
        box-shadow: 0 0 0 3px rgba(0,121,59,0.1) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00793B 0%, #00501F 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        padding: 14px 32px !important;
        width: 100%;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,121,59,0.4) !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F8FAF5 0%, #FFFFFF 100%);
        border-right: 1px solid #E8F5EE;
    }
    
    /* Footer */
    .onee-footer {
        text-align: center;
        padding: 32px;
        margin-top: 48px;
        border-top: 1px solid #E8F5EE;
        background: rgba(255,255,255,0.6);
        border-radius: 24px;
    }
    
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, #E8F5EE 0%, #D4E8DA 100%);
        color: #00501F;
        font-size: 11px;
        font-weight: 700;
        padding: 6px 12px;
        border-radius: 30px;
    }
    
    @media (max-width: 768px) {
        .onee-title { font-size: 28px; }
        .result-value { font-size: 36px; }
        .calc-card { padding: 20px; }
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #F0F4EA;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #00793B, #00501F);
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ── Advanced Calculation Functions ────────────────────────────────────────────

def calculate_phase_imbalance(currents: Tuple[float, float, float]) -> Dict[str, Any]:
    """Calculate phase imbalance parameters"""
    i_avg = sum(currents) / 3
    
    if i_avg > 0:
        deviations = [(abs(i - i_avg) / i_avg) * 100 for i in currents]
        max_deviation = max(deviations)
        
        if max_deviation > Constants.UNBALANCE_CRITICAL:
            status = "critical"
            message = f"⚠️ DÉSÉQUILIBRE CRITIQUE ({max_deviation:.1f}%) — Risque de surchauffe et pertes excessives"
        elif max_deviation > Constants.UNBALANCE_WARNING:
            status = "warning"
            message = f"⚡ Déséquilibre modéré ({max_deviation:.1f}%) — Recommander répartition des charges"
        else:
            status = "normal"
            message = f"✓ Déséquilibre acceptable ({max_deviation:.1f}%) — Répartition satisfaisante"
        
        return {
            "i_avg": i_avg,
            "deviations": deviations,
            "max_deviation": max_deviation,
            "status": status,
            "message": message
        }
    else:
        return {
            "i_avg": 0,
            "deviations": [0, 0, 0],
            "max_deviation": 0,
            "status": "normal",
            "message": "Aucun courant mesuré"
        }

def calculate_voltage_drop_per_phase(
    i_phase: float,
    cos_phi: float,
    L: float,
    section: float,
    material: str,
    tension_ref: float
) -> Dict[str, Any]:
    """Calculate voltage drop for a single phase considering power factor"""
    rho = Constants.RESISTIVITY[material]
    R = (rho * L) / section
    
    # Active and reactive components
    I_active = i_phase * cos_phi
    I_reactive = i_phase * math.sin(math.acos(cos_phi))
    
    # Voltage drop with power factor consideration
    # ΔU = √3 * I * (R * cosφ + X * sinφ) but for simplification we use R only
    # For unbalanced systems, we calculate per phase
    delta_u = math.sqrt(3) * i_phase * R * cos_phi
    
    # Additional reactive component
    # X is approximated for simplification
    X = 0.08  # Reactance approx for cables (Ω/km)
    delta_u_reactive = math.sqrt(3) * i_phase * X * L / 1000 * math.sin(math.acos(cos_phi))
    
    delta_u_total = math.sqrt(delta_u**2 + delta_u_reactive**2)
    
    perc_drop = (delta_u_total / tension_ref) * 100
    
    return {
        "delta_u": delta_u_total,
        "perc_drop": perc_drop,
        "I_active": I_active,
        "I_reactive": I_reactive,
        "resistance_drop": delta_u,
        "reactance_drop": delta_u_reactive
    }

def calculate_three_phase_unbalanced(
    currents: Tuple[float, float, float],
    cos_phi_phases: Tuple[float, float, float],
    L: float,
    section: float,
    material: str,
    tension_ref: float
) -> Dict[str, Any]:
    """Calculate complete unbalanced three-phase system analysis"""
    
    # Phase imbalance analysis
    imbalance = calculate_phase_imbalance(currents)
    
    # Per phase voltage drop
    phase_results = []
    for i, (current, cos_phi) in enumerate(zip(currents, cos_phi_phases)):
        result = calculate_voltage_drop_per_phase(
            current, cos_phi, L, section, material, tension_ref
        )
        result["phase"] = i + 1
        phase_results.append(result)
    
    # Global parameters
    total_current = sum(currents)
    total_active = sum([r["I_active"] for r in phase_results])
    total_reactive = sum([r["I_reactive"] for r in phase_results])
    
    # Average voltage drop
    avg_drop = sum([r["perc_drop"] for r in phase_results]) / 3
    max_drop = max([r["perc_drop"] for r in phase_results])
    min_drop = min([r["perc_drop"] for r in phase_results])
    
    # Determine overall status
    if max_drop > Constants.VOLTAGE_DROP_CRITICAL:
        status = "critical"
        message = f"❌ Chute excessive sur phase {phase_results[[r['perc_drop'] for r in phase_results].index(max_drop)]+1} — Non conforme"
    elif max_drop > Constants.VOLTAGE_DROP_WARNING:
        status = "warning"
        message = f"⚠️ Chute limite sur certaines phases — Vérifier le dimensionnement"
    else:
        status = "normal"
        message = f"✓ Chutes conformes — Installation correcte"
    
    # Recommendations
    recommendations = []
    if imbalance["max_deviation"] > Constants.UNBALANCE_WARNING:
        recommendations.append(f"Rééquilibrer les charges (déséquilibre: {imbalance['max_deviation']:.1f}%)")
    if max_drop > Constants.VOLTAGE_DROP_WARNING:
        s_min = (Constants.RESISTIVITY[material] * L * math.sqrt(3) * max(currents)) / (0.05 * tension_ref)
        recommended_section = next((s for s in Constants.CABLE_SECTIONS if s >= s_min), 
                                   Constants.CABLE_SECTIONS[-1])
        recommendations.append(f"Augmenter la section du câble à {recommended_section} mm²")
    
    return {
        "imbalance": imbalance,
        "phases": phase_results,
        "total_current": total_current,
        "total_active": total_active,
        "total_reactive": total_reactive,
        "avg_drop": avg_drop,
        "max_drop": max_drop,
        "min_drop": min_drop,
        "status": status,
        "message": message,
        "recommendations": recommendations
    }

def calculate_transformer_load_unbalanced(
    s_nom: float,
    p_reel_phases: Tuple[float, float, float],
    cos_phi_phases: Tuple[float, float, float]
) -> Dict[str, Any]:
    """Calculate transformer load considering phase unbalance"""
    
    # Per phase apparent power
    s_phases = [p / cos_phi if cos_phi > 0 else 0 for p, cos_phi in zip(p_reel_phases, cos_phi_phases)]
    s_total = sum(s_phases)
    
    # Total active and reactive power
    p_total = sum(p_reel_phases)
    q_total = sum([p * math.tan(math.acos(cos_phi)) for p, cos_phi in zip(p_reel_phases, cos_phi_phases)])
    
    # Global power factor
    if s_total > 0:
        cos_phi_global = p_total / s_total
    else:
        cos_phi_global = 0
    
    charge = (s_total / s_nom) * 100 if s_nom > 0 else 0
    
    # Phase imbalance
    if s_total > 0:
        max_phase_load = max(s_phases)
        min_phase_load = min(s_phases)
        imbalance = ((max_phase_load - min_phase_load) / (s_total / 3)) * 100 if s_total > 0 else 0
    else:
        imbalance = 0
    
    if charge > Constants.CHARGE_CRITICAL:
        status = "critical"
        message = "🚨 SURCHARGE CRITIQUE — Risque de détérioration du transformateur"
    elif charge > Constants.CHARGE_WARNING:
        status = "warning"
        message = "⚡ Charge ÉLEVÉE — Prévoir renforcement"
    elif imbalance > Constants.UNBALANCE_WARNING:
        status = "warning"
        message = f"⚠️ Déséquilibre important ({imbalance:.1f}%) — Répartir les charges"
    else:
        status = "normal"
        message = "✓ Charge normale — Fonctionnement optimal"
    
    return {
        "s_phases": s_phases,
        "s_total": s_total,
        "p_total": p_total,
        "q_total": q_total,
        "cos_phi_global": cos_phi_global,
        "charge": charge,
        "imbalance": imbalance,
        "status": status,
        "message": message
    }

def format_unbalanced_result_display(result: Dict, title: str, value_key: str, unit: str = "%") -> None:
    """Display formatted results for unbalanced systems"""
    status_map = {
        "normal": "result-ok",
        "warning": "result-warn",
        "critical": "result-err"
    }
    box_class = status_map.get(result["status"], "result-ok")
    
    value = result.get(value_key, 0)
    
    st.markdown(f"""
    <div class="result-box {box_class}">
        <div class="result-label">📊 {title}</div>
        <div class="result-value">{value:.1f} {unit}</div>
        <div class="result-msg">{result['message']}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Main App ───────────────────────────────────────────────────────────────────
def main():
    load_enhanced_css()
    
    # Header
    st.markdown("""
    <div class="onee-header">
        <div class="onee-logo">Office National de l'Electricité et de l'Eau Potable</div>
        <div class="onee-title">ONEE Tech Assistant</div>
        <div class="onee-subtitle">Analyse avancée des réseaux triphasés déséquilibrés</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Tableau de bord")
        
        if st.session_state.res_t1:
            with st.container():
                st.markdown("**Charge transformateur**")
                charge = st.session_state.res_t1['charge']
                if charge > 80:
                    st.warning(f"Taux: {charge:.1f}%")
                else:
                    st.success(f"Taux: {charge:.1f}%")
        
        if st.session_state.res_t2 and 'imbalance' in st.session_state.res_t2:
            with st.container():
                st.markdown("**Déséquilibre**")
                imbalance = st.session_state.res_t2['imbalance']['max_deviation']
                if imbalance > 20:
                    st.warning(f"{imbalance:.1f}%")
                else:
                    st.success(f"{imbalance:.1f}%")
        
        st.markdown("---")
        st.markdown("### ℹ️ À propos")
        st.caption("Version 2.2 — Analyse triphasée déséquilibrée avec cos φ par phase")
        st.caption("Conforme aux normes NFC 11-201 et IEC 60364")
    
    # Tabs
    tab1, tab2 = st.tabs(["🔌 Charge Transformateur Triphasé", "📉 Chute de Tension Déséquilibrée"])
    
    # Tab 1: Transformer Load with Phase Unbalance
    with tab1:
        with st.container():
            st.markdown('<div class="calc-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">🔌 Analyse de charge avec déséquilibre de phases</div>', unsafe_allow_html=True)
            
            # Transformer nominal power
            s_nom = st.number_input(
                "Puissance nominale du transformateur (kVA)",
                min_value=1.0, value=160.0, step=10.0,
                help="Puissance apparente nominale du transformateur"
            )
            
            st.markdown("#### Puissance active par phase (kW)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="phase-card"><div class="phase-title phase-l1">🔴 Phase L1</div>', unsafe_allow_html=True)
                p1 = st.number_input("P active L1 (kW)", min_value=0.0, value=45.0, step=5.0, key="p1")
                cos1 = st.slider("cos φ L1", 0.50, 1.0, 0.85, 0.01, key="cos1")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="phase-card"><div class="phase-title phase-l2">🟢 Phase L2</div>', unsafe_allow_html=True)
                p2 = st.number_input("P active L2 (kW)", min_value=0.0, value=55.0, step=5.0, key="p2")
                cos2 = st.slider("cos φ L2", 0.50, 1.0, 0.82, 0.01, key="cos2")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="phase-card"><div class="phase-title phase-l3">🟡 Phase L3</div>', unsafe_allow_html=True)
                p3 = st.number_input("P active L3 (kW)", min_value=0.0, value=35.0, step=5.0, key="p3")
                cos3 = st.slider("cos φ L3", 0.50, 1.0, 0.88, 0.01, key="cos3")
                st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("⚡ Calculer la charge triphasée", key="btn_t1", use_container_width=True):
                with st.spinner("Analyse en cours..."):
                    result = calculate_transformer_load_unbalanced(
                        s_nom, (p1, p2, p3), (cos1, cos2, cos3)
                    )
                    st.session_state.res_t1 = result
                    st.session_state.calculation_history.append({
                        "timestamp": datetime.now(),
                        "type": "Charge Transformateur Déséquilibré",
                        "parameters": {"S_nom": s_nom, "P": (p1, p2, p3), "cos": (cos1, cos2, cos3)},
                        "results": result
                    })
            
            if st.session_state.res_t1:
                result = st.session_state.res_t1
                
                # Global results
                format_unbalanced_result_display(result, "Charge globale", "charge")
                
                # Phase details
                st.markdown("---")
                st.markdown("#### 📊 Analyse par phase")
                col1, col2, col3 = st.columns(3)
                
                phases = ["L1", "L2", "L3"]
                colors = ["phase-l1", "phase-l2", "phase-l3"]
                powers = [(p1, cos1), (p2, cos2), (p3, cos3)]
                
                for idx, (col, phase, color, power) in enumerate(zip([col1, col2, col3], phases, colors, powers)):
                    with col:
                        st.markdown(f"""
                        <div class="phase-card">
                            <div class="phase-title {color}">Phase {phase}</div>
                            <div><strong>P active:</strong> {power[0]:.1f} kW</div>
                            <div><strong>cos φ:</strong> {power[1]:.2f}</div>
                            <div><strong>S apparente:</strong> {result['s_phases'][idx]:.1f} kVA</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Global metrics
                st.markdown("---")
                st.markdown("#### 📈 Paramètres globaux")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Puissance totale", f"{result['p_total']:.1f} kW")
                col2.metric("Puissance réactive", f"{result['q_total']:.1f} kVAR")
                col3.metric("Puissance apparente", f"{result['s_total']:.1f} kVA")
                col4.metric("cos φ global", f"{result['cos_phi_global']:.3f}")
                
                if result['imbalance'] > Constants.UNBALANCE_WARNING:
                    st.warning(f"⚠️ **Déséquilibre entre phases: {result['imbalance']:.1f}%** — Répartir les charges uniformément")
                else:
                    st.success(f"✓ Déséquilibre acceptable: {result['imbalance']:.1f}%")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 2: Unbalanced Voltage Drop
    with tab2:
        with st.container():
            st.markdown('<div class="calc-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📉 Chute de tension en régime déséquilibré</div>', unsafe_allow_html=True)
            
            st.markdown("#### Courants et facteurs de puissance par phase")
            
            # Phase inputs
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="phase-card"><div class="phase-title phase-l1">🔴 Phase L1</div>', unsafe_allow_html=True)
                i1 = st.number_input("Courant L1 (A)", min_value=0.0, value=65.0, step=5.0, key="i1")
                cos_i1 = st.slider("cos φ L1", 0.50, 1.0, 0.85, 0.01, key="cos_i1")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="phase-card"><div class="phase-title phase-l2">🟢 Phase L2</div>', unsafe_allow_html=True)
                i2 = st.number_input("Courant L2 (A)", min_value=0.0, value=75.0, step=5.0, key="i2")
                cos_i2 = st.slider("cos φ L2", 0.50, 1.0, 0.82, 0.01, key="cos_i2")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="phase-card"><div class="phase-title phase-l3">🟡 Phase L3</div>', unsafe_allow_html=True)
                i3 = st.number_input("Courant L3 (A)", min_value=0.0, value=45.0, step=5.0, key="i3")
                cos_i3 = st.slider("cos φ L3", 0.50, 1.0, 0.88, 0.01, key="cos_i3")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Cable parameters
            col1, col2 = st.columns(2)
            with col1:
                L = st.number_input("Longueur du câble (m)", min_value=1.0, value=120.0, step=10.0,
                                   help="Distance entre la source et la charge")
            with col2:
                section = st.selectbox("Section du câble (mm²)", Constants.CABLE_SECTIONS,
                                      help="Section du conducteur")
            
            col1, col2 = st.columns(2)
            with col1:
                material = st.radio("Matériau conducteur", list(Constants.RESISTIVITY.keys()),
                                   horizontal=True)
            with col2:
                network_type = st.selectbox("Type de réseau", ["Personnalisé"] + list(Constants.NETWORK_VOLTAGES.keys()))
                if network_type != "Personnalisé":
                    tension_ref = Constants.NETWORK_VOLTAGES[network_type]
                else:
                    tension_ref = st.number_input("Tension du réseau (V)", min_value=100.0, value=400.0, step=10.0)
            
            if st.button("⚡ Analyser le déséquilibre et chutes", key="btn_t2", use_container_width=True):
                with st.spinner("Analyse avancée en cours..."):
                    result = calculate_three_phase_unbalanced(
                        (i1, i2, i3), (cos_i1, cos_i2, cos_i3),
                        L, section, material, tension_ref
                    )
                    st.session_state.res_t2 = result
                    st.session_state.calculation_history.append({
                        "timestamp": datetime.now(),
                        "type": "Chute Tension Déséquilibrée",
                        "parameters": {"I": (i1, i2, i3), "cos": (cos_i1, cos_i2, cos_i3), "L": L, "Section": section},
                        "results": result
                    })
            
            if st.session_state.res_t2:
                result = st.session_state.res_t2
                
                # Imbalance analysis
                st.markdown(f"""
                <div class="result-box result-{result['imbalance']['status']}">
                    <div class="result-label">⚖️ DÉSÉQUILIBRE DE PHASES</div>
                    <div class="result-value">{result['imbalance']['max_deviation']:.1f} %</div>
                    <div class="result-msg">{result['imbalance']['message']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Per phase voltage drop
                st.markdown("#### 📉 Chutes de tension par phase")
                col1, col2, col3 = st.columns(3)
                
                phases = ["L1", "L2", "L3"]
                colors = ["phase-l1", "phase-l2", "phase-l3"]
                
                for idx, (col, phase, color) in enumerate(zip([col1, col2, col3], phases, colors)):
                    phase_result = result['phases'][idx]
                    drop_color = "🟢" if phase_result['perc_drop'] <= 3 else ("🟡" if phase_result['perc_drop'] <= 5 else "🔴")
                    
                    with col:
                        st.markdown(f"""
                        <div class="phase-card">
                            <div class="phase-title {color}">Phase {phase}</div>
                            <div><strong>Courant:</strong> {(i1, i2, i3)[idx]:.1f} A</div>
                            <div><strong>cos φ:</strong> {(cos_i1, cos_i2, cos_i3)[idx]:.2f}</div>
                            <div><strong>Chute tension:</strong> {phase_result['perc_drop']:.2f}% {drop_color}</div>
                            <div><strong>ΔU total:</strong> {phase_result['delta_u']:.2f} V</div>
                            <div><small>Résistif: {phase_result['resistance_drop']:.2f} V | Réactif: {phase_result['reactance_drop']:.2f} V</small></div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Global statistics
                st.markdown("---")
                st.markdown("#### 📊 Statistiques globales")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Chute moyenne", f"{result['avg_drop']:.2f} %")
                col2.metric("Chute max", f"{result['max_drop']:.2f} %", delta=f"Phase {result['phases'][[r['perc_drop'] for r in result['phases']].index(result['max_drop'])]['phase']}")
                col3.metric("Chute min", f"{result['min_drop']:.2f} %")
                col4.metric("Déséquilibre max", f"{result['imbalance']['max_deviation']:.1f} %")
                
                # Recommendations
                if result['recommendations']:
                    st.warning("### 💡 Recommandations")
                    for rec in result['recommendations']:
                        st.write(f"• {rec}")
                else:
                    st.success("✓ Aucune recommandation corrective nécessaire")
                
                # Summary message
                st.markdown(f"""
                <div class="result-box result-{result['status']}">
                    <div class="result-label">📋 SYNTHÈSE</div>
                    <div class="result-msg">{result['message']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown(f"""
    <div class="onee-footer">
        <span class="badge">⚡ ONEE Tech v2.2</span>
        <span class="badge">📊 Analyse triphasée déséquilibrée</span>
        <span class="badge">📅 {datetime.now().strftime('%d/%m/%Y')}</span>
        <br/><br/>
        <small>Outil professionnel de calculs électriques — Prend en compte le déséquilibre de phases et cos φ par phase</small>
        <br/>
        <small>Conforme aux normes NFC 11-201, IEC 60364 et recommandations ONEE</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
