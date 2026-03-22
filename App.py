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
    
    # Réactance approximative des câbles (Ω/km)
    REACTANCE = 0.08
    
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
        "calculation_history": [],
        "show_advanced": True
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

init_session_state()

# ── Enhanced CSS with visible colors ───────────────────────────────────────────
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
    
    /* Header */
    .onee-header {
        background: linear-gradient(135deg, #00793B 0%, #00501F 100%);
        border-radius: 24px;
        padding: 40px 48px;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 40px -12px rgba(0,0,0,0.2);
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
        color: rgba(255,255,255,0.8);
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    
    .onee-title {
        font-size: 42px;
        font-weight: 800;
        color: white;
        line-height: 1.1;
        margin: 0;
    }
    
    .onee-subtitle {
        font-size: 15px;
        color: rgba(255,255,255,0.9);
        margin-top: 12px;
    }
    
    /* Cards */
    .calc-card {
        background: white;
        border-radius: 24px;
        padding: 32px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border: 1px solid #E8F5EE;
    }
    
    .card-title {
        font-size: 24px;
        font-weight: 700;
        color: #00501F;
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
        background: #F4A800;
        border-radius: 2px;
    }
    
    /* Phase cards with VISIBLE colors */
    .phase-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        border: 2px solid #E8F5EE;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .phase-title {
        font-size: 20px;
        font-weight: 800;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .phase-l1 {
        color: #DC2626;
        border-bottom-color: #DC2626;
    }
    
    .phase-l2 {
        color: #10B981;
        border-bottom-color: #10B981;
    }
    
    .phase-l3 {
        color: #F59E0B;
        border-bottom-color: #F59E0B;
    }
    
    .phase-value {
        font-size: 24px;
        font-weight: 700;
        margin: 8px 0;
    }
    
    .phase-label {
        font-size: 12px;
        color: #6B7280;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Result boxes */
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
        background: linear-gradient(135deg, #E8F5EE 0%, #D4E8DA 100%);
        border-left: 5px solid #00793B;
    }
    
    .result-warn {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        border-left: 5px solid #F59E0B;
    }
    
    .result-err {
        background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
        border-left: 5px solid #DC2626;
    }
    
    .result-label {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 8px;
        color: #374151;
    }
    
    .result-value {
        font-size: 56px;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 12px;
        color: #1F2937;
    }
    
    .result-msg {
        font-size: 14px;
        font-weight: 500;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid rgba(0,0,0,0.1);
        color: #374151;
    }
    
    /* Metrics */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #F9FAFB 0%, #FFFFFF 100%);
        border-radius: 16px;
        padding: 20px !important;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    [data-testid="stMetricLabel"] {
        color: #6B7280 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #00501F !important;
        font-weight: 800 !important;
        font-size: 28px !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #E8F5EE;
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
        color: #4B5563;
    }
    
    .stTabs [aria-selected="true"] {
        background: #00793B !important;
        color: white !important;
    }
    
    /* Inputs */
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > input {
        background: white !important;
        border: 2px solid #E5E7EB !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: #00793B !important;
        box-shadow: 0 0 0 3px rgba(0,121,59,0.1) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: #00793B !important;
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
        background: #00501F !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,121,59,0.3) !important;
    }
    
    /* Info/Warning boxes */
    .stInfo {
        background: #EFF6FF !important;
        border-left: 4px solid #3B82F6 !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }
    
    .stWarning {
        background: #FEF3C7 !important;
        border-left: 4px solid #F59E0B !important;
        border-radius: 12px !important;
    }
    
    .stSuccess {
        background: #E8F5EE !important;
        border-left: 4px solid #00793B !important;
        border-radius: 12px !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
    
    /* Footer */
    .onee-footer {
        text-align: center;
        padding: 32px;
        margin-top: 48px;
        border-top: 1px solid #E5E7EB;
        background: white;
        border-radius: 24px;
    }
    
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #E8F5EE;
        color: #00501F;
        font-size: 11px;
        font-weight: 700;
        padding: 6px 12px;
        border-radius: 30px;
        margin: 0 4px;
    }
    
    @media (max-width: 768px) {
        .onee-title { font-size: 28px; }
        .result-value { font-size: 36px; }
        .calc-card { padding: 20px; }
    }
    
    /* Hide default elements */
    #MainMenu, footer, header { visibility: hidden; }
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
            status = "err"
            message = f"⚠️ DÉSÉQUILIBRE CRITIQUE ({max_deviation:.1f}%) — Risque de surchauffe"
        elif max_deviation > Constants.UNBALANCE_WARNING:
            status = "warn"
            message = f"⚡ Déséquilibre modéré ({max_deviation:.1f}%) — Répartir les charges"
        else:
            status = "ok"
            message = f"✓ Déséquilibre acceptable ({max_deviation:.1f}%)"
        
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
            "status": "ok",
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
    """
    Calculate voltage drop for a single phase with power factor consideration
    Formule selon NFC 11-201: ΔU = √3 * I * (R * cosφ + X * sinφ)
    """
    rho = Constants.RESISTIVITY[material]
    R = (rho * L) / section  # Résistance en ohms
    X = Constants.REACTANCE * L / 1000  # Réactance en ohms
    
    # Calcul avec prise en compte complète du cos φ
    sin_phi = math.sin(math.acos(cos_phi))
    
    # Chute de tension complète
    delta_u = math.sqrt(3) * i_phase * (R * cos_phi + X * sin_phi)
    
    # Composantes séparées pour analyse
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
        result["current"] = current
        phase_results.append(result)
    
    # Global parameters
    total_current = sum(currents)
    total_S = sum([r["S"] for r in phase_results])
    total_P = sum([r["P"] for r in phase_results])
    total_Q = sum([r["Q"] for r in phase_results])
    
    # Global power factor
    if total_S > 0:
        cos_phi_global = total_P / total_S
    else:
        cos_phi_global = 0
    
    # Average voltage drop
    avg_drop = sum([r["perc_drop"] for r in phase_results]) / 3
    max_drop = max([r["perc_drop"] for r in phase_results])
    min_drop = min([r["perc_drop"] for r in phase_results])
    max_drop_phase = phase_results[[r["perc_drop"] for r in phase_results].index(max_drop)]["phase"]
    
    # Determine overall status
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
    if imbalance["max_deviation"] > Constants.UNBALANCE_WARNING:
        recommendations.append(f"Rééquilibrer les charges (déséquilibre: {imbalance['max_deviation']:.1f}%)")
    if max_drop > Constants.VOLTAGE_DROP_WARNING:
        # Calcul de section minimale recommandée
        worst_phase_idx = [r["perc_drop"] for r in phase_results].index(max_drop)
        worst_current = currents[worst_phase_idx]
        worst_cos = cos_phi_phases[worst_phase_idx]
        s_min = (Constants.RESISTIVITY[material] * L * math.sqrt(3) * worst_current * worst_cos) / (0.05 * tension_ref)
        recommended_section = next((s for s in Constants.CABLE_SECTIONS if s >= s_min), 
                                   Constants.CABLE_SECTIONS[-1])
        if recommended_section > section:
            recommendations.append(f"Augmenter la section du câble à {recommended_section} mm² (actuel: {section} mm²)")
    
    return {
        "imbalance": imbalance,
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
        "recommendations": recommendations,
        "L": L,
        "section": section,
        "material": material,
        "tension_ref": tension_ref
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
        avg_phase_load = s_total / 3
        imbalance = ((max_phase_load - min_phase_load) / avg_phase_load) * 100 if avg_phase_load > 0 else 0
    else:
        imbalance = 0
    
    if charge > Constants.CHARGE_CRITICAL:
        status = "err"
        message = "🚨 SURCHARGE CRITIQUE — Risque de détérioration du transformateur"
    elif charge > Constants.CHARGE_WARNING:
        status = "warn"
        message = "⚡ Charge ÉLEVÉE — Prévoir renforcement"
    elif imbalance > Constants.UNBALANCE_WARNING:
        status = "warn"
        message = f"⚠️ Déséquilibre important ({imbalance:.1f}%) — Répartir les charges"
    else:
        status = "ok"
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
        "message": message,
        "p_phases": p_reel_phases,
        "cos_phases": cos_phi_phases
    }

# ── Main App ───────────────────────────────────────────────────────────────────
def main():
    load_enhanced_css()
    
    # Header
    st.markdown("""
    <div class="onee-header">
        <div class="onee-logo">Office National de l'Electricité et de l'Eau Potable</div>
        <div class="onee-title">ONEE Tech Assistant</div>
        <div class="onee-subtitle">Analyse avancée des réseaux triphasés déséquilibrés avec cos φ par phase</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Tableau de bord")
        
        if st.session_state.res_t1:
            st.markdown("**Charge transformateur**")
            charge = st.session_state.res_t1['charge']
            if charge > 80:
                st.warning(f"Taux: {charge:.1f}%")
            else:
                st.success(f"Taux: {charge:.1f}%")
        
        if st.session_state.res_t2:
            st.markdown("**Déséquilibre**")
            imbalance = st.session_state.res_t2['imbalance']['max_deviation']
            if imbalance > 20:
                st.warning(f"{imbalance:.1f}%")
            else:
                st.success(f"{imbalance:.1f}%")
            
            st.markdown("**Chute max**")
            max_drop = st.session_state.res_t2['max_drop']
            if max_drop > 5:
                st.error(f"{max_drop:.2f}%")
            elif max_drop > 3:
                st.warning(f"{max_drop:.2f}%")
            else:
                st.success(f"{max_drop:.2f}%")
        
        st.markdown("---")
        st.markdown("### 📐 Formules utilisées")
        st.caption("ΔU = √3 × I × (R × cosφ + X × sinφ)")
        st.caption("cosφ = facteur de puissance par phase")
        st.caption("X = réactance du câble (0.08 Ω/km)")
        
        st.markdown("---")
        st.markdown("### ℹ️ Normes")
        st.caption("NFC 11-201: ΔU ≤ 3% (éclairage), ≤ 5% (force motrice)")
        st.caption("Déséquilibre recommandé < 20%")
    
    # Tabs
    tab1, tab2 = st.tabs(["🔌 Charge Transformateur Triphasé", "📉 Chute de Tension Déséquilibrée"])
    
    # Tab 1: Transformer Load with Phase Unbalance
    with tab1:
        with st.container():
            st.markdown('<div class="calc-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">🔌 Analyse de charge avec déséquilibre de phases</div>', unsafe_allow_html=True)
            
            # Transformer nominal power
            col1, col2 = st.columns([1, 2])
            with col1:
                s_nom = st.number_input(
                    "Puissance nominale (kVA)",
                    min_value=1.0, value=160.0, step=10.0,
                    help="Puissance apparente nominale du transformateur"
                )
            
            st.markdown("#### ⚡ Puissance active et cos φ par phase")
            
            # Phase inputs with visible colors
            cols = st.columns(3)
            phase_data = []
            
            phase_configs = [
                {"name": "Phase L1", "color": "#DC2626", "icon": "🔴", "default_p": 45.0, "default_cos": 0.85, "key": "p1"},
                {"name": "Phase L2", "color": "#10B981", "icon": "🟢", "default_p": 55.0, "default_cos": 0.82, "key": "p2"},
                {"name": "Phase L3", "color": "#F59E0B", "icon": "🟡", "default_p": 35.0, "default_cos": 0.88, "key": "p3"}
            ]
            
            for idx, (col, config) in enumerate(zip(cols, phase_configs)):
                with col:
                    st.markdown(f"""
                    <div class="phase-card">
                        <div class="phase-title" style="color: {config['color']}; border-bottom-color: {config['color']};">
                            {config['icon']} {config['name']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    p_val = st.number_input(
                        f"P active (kW)", 
                        min_value=0.0, 
                        value=config['default_p'], 
                        step=5.0, 
                        key=f"p_{config['key']}"
                    )
                    cos_val = st.slider(
                        f"cos φ", 
                        0.50, 1.0, 
                        config['default_cos'], 
                        0.01, 
                        key=f"cos_{config['key']}"
                    )
                    phase_data.append((p_val, cos_val))
            
            p1, p2, p3 = [d[0] for d in phase_data]
            cos1, cos2, cos3 = [d[1] for d in phase_data]
            
            if st.button("⚡ Calculer la charge triphasée", key="btn_t1", use_container_width=True):
                with st.spinner("Analyse en cours..."):
                    result = calculate_transformer_load_unbalanced(
                        s_nom, (p1, p2, p3), (cos1, cos2, cos3)
                    )
                    st.session_state.res_t1 = result
            
            if st.session_state.res_t1:
                result = st.session_state.res_t1
                
                # Global results
                box_class = f"result-{result['status']}"
                st.markdown(f"""
                <div class="result-box {box_class}">
                    <div class="result-label">📊 TAUX DE CHARGE GLOBAL</div>
                    <div class="result-value">{result['charge']:.1f} %</div>
                    <div class="result-msg">{result['message']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Phase details
                st.markdown("---")
                st.markdown("#### 📊 Analyse par phase")
                cols = st.columns(3)
                
                phase_colors = ["#DC2626", "#10B981", "#F59E0B"]
                phase_icons = ["🔴", "🟢", "🟡"]
                
                for idx, (col, color, icon) in enumerate(zip(cols, phase_colors, phase_icons)):
                    with col:
                        st.markdown(f"""
                        <div style="background: #F9FAFB; border-radius: 12px; padding: 16px; margin: 8px 0; border-left: 4px solid {color};">
                            <div style="font-size: 18px; font-weight: 800; color: {color}; margin-bottom: 12px;">
                                {icon} Phase L{idx+1}
                            </div>
                            <div style="margin: 8px 0;">
                                <span style="font-size: 12px; color: #6B7280;">P active:</span>
                                <span style="font-size: 20px; font-weight: 700; color: #1F2937;"> {result['p_phases'][idx]:.1f} kW</span>
                            </div>
                            <div style="margin: 8px 0;">
                                <span style="font-size: 12px; color: #6B7280;">cos φ:</span>
                                <span style="font-size: 20px; font-weight: 700; color: #1F2937;"> {result['cos_phases'][idx]:.3f}</span>
                            </div>
                            <div style="margin: 8px 0;">
                                <span style="font-size: 12px; color: #6B7280;">S apparente:</span>
                                <span style="font-size: 20px; font-weight: 700; color: #1F2937;"> {result['s_phases'][idx]:.1f} kVA</span>
                            </div>
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
            st.markdown('<div class="card-title">📉 Chute de tension avec cos φ par phase</div>', unsafe_allow_html=True)
            
            st.markdown("#### ⚡ Courants et facteurs de puissance par phase")
            st.info("📐 Formule: ΔU = √3 × I × (R × cosφ + X × sinφ) avec X = 0.08 Ω/km")
            
            # Phase inputs
            cols = st.columns(3)
            current_data = []
            
            current_configs = [
                {"name": "Phase L1", "color": "#DC2626", "icon": "🔴", "default_i": 65.0, "default_cos": 0.85, "key": "i1"},
                {"name": "Phase L2", "color": "#10B981", "icon": "🟢", "default_i": 75.0, "default_cos": 0.82, "key": "i2"},
                {"name": "Phase L3", "color": "#F59E0B", "icon": "🟡", "default_i": 45.0, "default_cos": 0.88, "key": "i3"}
            ]
            
            for idx, (col, config) in enumerate(zip(cols, current_configs)):
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
                        value=config['default_i'], 
                        step=5.0, 
                        key=f"i_{config['key']}"
                    )
                    cos_val = st.slider(
                        f"cos φ", 
                        0.50, 1.0, 
                        config['default_cos'], 
                        0.01, 
                        key=f"cos_i_{config['key']}"
                    )
                    current_data.append((i_val, cos_val))
            
            i1, i2, i3 = [d[0] for d in current_data]
            cos_i1, cos_i2, cos_i3 = [d[1] for d in current_data]
            
            st.markdown("---")
            st.markdown("#### 🔌 Paramètres du câble")
            
            col1, col2 = st.columns(2)
            with col1:
                L = st.number_input("Longueur du câble (m)", min_value=1.0, value=120.0, step=10.0)
                section = st.selectbox("Section du câble (mm²)", Constants.CABLE_SECTIONS)
            with col2:
                material = st.radio("Matériau conducteur", list(Constants.RESISTIVITY.keys()), horizontal=True)
                network_type = st.selectbox("Type de réseau", ["Personnalisé"] + list(Constants.NETWORK_VOLTAGES.keys()))
                if network_type != "Personnalisé":
                    tension_ref = Constants.NETWORK_VOLTAGES[network_type]
                else:
                    tension_ref = st.number_input("Tension (V)", min_value=100.0, value=400.0, step=10.0)
            
            if st.button("⚡ Analyser le déséquilibre et chutes", key="btn_t2", use_container_width=True):
                with st.spinner("Analyse avancée en cours..."):
                    result = calculate_three_phase_unbalanced(
                        (i1, i2, i3), (cos_i1, cos_i2, cos_i3),
                        L, section, material, tension_ref
                    )
                    st.session_state.res_t2 = result
            
            if st.session_state.res_t2:
                result = st.session_state.res_t2
                
                # Imbalance analysis
                imbalance_status = result['imbalance']['status']
                imbalance_color = "#DC2626" if imbalance_status == "err" else ("#F59E0B" if imbalance_status == "warn" else "#10B981")
                
                st.markdown(f"""
                <div class="result-box result-{imbalance_status}">
                    <div class="result-label">⚖️ DÉSÉQUILIBRE DE PHASES</div>
                    <div class="result-value">{result['imbalance']['max_deviation']:.1f} %</div>
                    <div class="result-msg">{result['imbalance']['message']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Per phase voltage drop
                st.markdown("#### 📉 Chutes de tension par phase (avec cos φ)")
                cols = st.columns(3)
                
                phase_colors = ["#DC2626", "#10B981", "#F59E0B"]
                phase_icons = ["🔴", "🟢", "🟡"]
                
                for idx, (col, color, icon) in enumerate(zip(cols, phase_colors, phase_icons)):
                    phase = result['phases'][idx]
                    drop_status = "🟢" if phase['perc_drop'] <= 3 else ("🟡" if phase['perc_drop'] <= 5 else "🔴")
                    
                    with col:
                        st.markdown(f"""
                        <div style="background: #F9FAFB; border-radius: 12px; padding: 16px; margin: 8px 0; border-left: 4px solid {color};">
                            <div style="font-size: 18px; font-weight: 800; color: {color}; margin-bottom: 12px;">
                                {icon} Phase L{idx+1}
                            </div>
                            <div style="margin: 8px 0;">
                                <span style="font-size: 12px; color: #6B7280;">Courant:</span>
                                <span style="font-size: 20px; font-weight: 700; color: #1F2937;"> {phase['current']:.1f} A</span>
                            </div>
                            <div style="margin: 8px 0;">
                                <span style="font-size: 12px; color: #6B7280;">cos φ:</span>
                                <span style="font-size: 20px; font-weight: 700; color: #1F2937;"> {phase['cos_phi']:.3f}</span>
                            </div>
                            <div style="margin: 8px 0;">
                                <span style="font-size: 12px; color: #6B7280;">Chute tension:</span>
                                <span style="font-size: 24px; font-weight: 800; color: {color};"> {phase['perc_drop']:.2f}%</span>
                                <span style="font-size: 16px;"> {drop_status}</span>
                            </div>
                            <div style="margin: 8px 0;">
                                <span style="font-size: 12px; color: #6B7280;">ΔU total:</span>
                                <span style="font-size: 14px; font-weight: 600;"> {phase['delta_u']:.1f} V</span>
                            </div>
                            <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #E5E7EB;">
                                <span style="font-size: 10px; color: #6B7280;">Résistif: {phase['delta_u_resistive']:.1f} V | Réactif: {phase['delta_u_reactive']:.1f} V</span>
                            </div>
                            <div style="margin-top: 4px;">
                                <span style="font-size: 10px; color: #6B7280;">P: {phase['P']:.1f} kW | Q: {phase['Q']:.1f} kVAR</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Global statistics
                st.markdown("---")
                st.markdown("#### 📊 Statistiques globales")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Chute moyenne", f"{result['avg_drop']:.2f} %")
                col2.metric("Chute maximale", f"{result['max_drop']:.2f} %", delta=f"Phase {result['max_drop_phase']}")
                col3.metric("Chute minimale", f"{result['min_drop']:.2f} %")
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
                
                # Summary message
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
        <span class="badge">📊 Analyse triphasée déséquilibrée</span>
        <span class="badge">📐 ΔU = √3 × I × (R×cosφ + X×sinφ)</span>
        <br/><br/>
        <small>Outil professionnel de calculs électriques — Prend en compte le déséquilibre de phases et cos φ par phase</small>
        <br/>
        <small>Conforme aux normes NFC 11-201, IEC 60364 et recommandations ONEE</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
