import streamlit as st
import math
import io
from datetime import datetime
from typing import Dict, Tuple, Any, List

# --- ReportLab pour le PDF ---
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    st.warning("La génération PDF nécessite la bibliothèque 'reportlab'. Installez-la avec: pip install reportlab")

# --- Constantes ---
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
    TEMP_DERATE_COEFF = 0.0025  # 0,25 % par °C au-dessus de 40°C

# --- Session state ---
def init_session_state():
    if "res_t1" not in st.session_state:
        st.session_state.res_t1 = None
    if "res_t2" not in st.session_state:
        st.session_state.res_t2 = None
    if "client_name" not in st.session_state:
        st.session_state.client_name = ""
    if "poste_name" not in st.session_state:
        st.session_state.poste_name = ""
    if "poste_matricule" not in st.session_state:
        st.session_state.poste_matricule = ""

init_session_state()

# --- CSS (inchangé) ---
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #E8E8E8; }
    body, .stMarkdown, p, div, span, label, .stText, .stAlert, .stInfo, .stWarning, .stSuccess {
        color: #1E3A8A !important;
    }
    .onee-header * { color: #FFFFFF !important; }
    .card-title { color: #1B5E20 !important; }
    .result-value { color: #1A2A1A !important; }
    [data-testid="stMetricLabel"] { color: #1B5E20 !important; }
    [data-testid="stMetricValue"] { color: #2563EB !important; }
    .calc-card h3, .calc-card h4 { color: #1E3A8A !important; }
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div[data-baseweb="select"] > div {
        color: #1E3A8A !important;
        -webkit-text-fill-color: #1E3A8A !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] span {
        color: #1E3A8A !important;
    }
    .badge, .cos-badge { color: #1B5E20 !important; }
    .onee-header {
        background: #1B5E20;
        border-radius: 16px;
        padding: 32px 40px;
        margin-bottom: 24px;
    }
    .onee-logo { font-size: 12px; font-weight: 600; text-transform: uppercase; }
    .onee-title { font-size: 36px; font-weight: 800; margin: 0; }
    .onee-subtitle { font-size: 14px; }
    .calc-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 24px;
        border: 1px solid #D0D0D0;
    }
    .card-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 24px;
        padding-bottom: 12px;
        border-bottom: 2px solid #E8F5E9;
    }
    .result-box {
        border-radius: 12px;
        padding: 24px 28px;
        margin-top: 20px;
        border-left: 5px solid;
    }
    .result-ok { background: #E8F5E9; border-left-color: #1B5E20; }
    .result-warn { background: #FFF3E0; border-left-color: #FF9800; }
    .result-err { background: #FFEBEE; border-left-color: #D32F2F; }
    .result-label { font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; color: #5A6B5A !important; }
    .result-value { font-size: 48px; font-weight: 800; line-height: 1; margin-bottom: 8px; }
    .result-msg { font-size: 13px; font-weight: 500; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(0,0,0,0.08); }
    [data-testid="metric-container"] {
        background: #F8F9F8;
        border-radius: 12px;
        padding: 16px !important;
        border: 1px solid #D0D0D0;
    }
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
    .stNumberInput > div > div > input {
        background: #FFFFFF !important;
        border: 1px solid #C0C0C0 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }
    .stSelectbox > div > div > div[data-baseweb="select"] > div {
        background: #FFFFFF !important;
        border: 1px solid #C0C0C0 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }
    div[role="listbox"] div {
        color: #1A2A1A !important;
        font-weight: 500 !important;
        background: #FFFFFF !important;
    }
    div[role="listbox"] div:hover { background: #E8F5E9 !important; }
    .stRadio label, .stSlider label { font-weight: 500 !important; }
    .stButton > button {
        background: #1B5E20 !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        width: 100%;
    }
    .stButton > button:hover { background: #0F4A13 !important; }
    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #D0D0D0;
    }
    .onee-footer {
        text-align: center;
        padding: 24px;
        margin-top: 40px;
        border-top: 1px solid #D0D0D0;
        background: #FFFFFF;
        border-radius: 16px;
    }
    .badge {
        background: #E8F5E9;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        margin: 0 4px;
        display: inline-block;
    }
    .cos-badge {
        background: #E8F5E9;
        font-size: 16px;
        font-weight: 800;
        padding: 8px 20px;
        border-radius: 40px;
        text-align: center;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PDF Generation ---
def generate_pdf_report(title: str, data_rows: List[Tuple[str, str, str]], summary_message: str, client_name: str = "", poste_name: str = "", poste_matricule: str = "") -> io.BytesIO:
    if not REPORTLAB_AVAILABLE:
        return None
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        fontSize=16,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1B5E20"),
        spaceAfter=12
    )
    sub_style = ParagraphStyle(
        "Sub",
        fontSize=9,
        fontName="Helvetica",
        textColor=colors.grey,
        spaceAfter=8
    )
    normal_style = styles["Normal"]
    story = []
    if client_name:
        story.append(Paragraph(f"Client : {client_name}", sub_style))
    if poste_name:
        story.append(Paragraph(f"Poste : {poste_name}", sub_style))
    if poste_matricule:
        story.append(Paragraph(f"Matricule : {poste_matricule}", sub_style))
    if client_name or poste_name or poste_matricule:
        story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(f"ONEE — {title}", title_style))
    story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", sub_style))
    story.append(Spacer(1, 0.5*cm))
    # Table
    table_data = [["Paramètre", "Valeur", "Unité"]]
    for param, value, unit in data_rows:
        table_data.append([param, value, unit])
    table = Table(table_data, colWidths=[7*cm, 5*cm, 3*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B5E20")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#E8F5E9")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C0C0C0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Synthèse : {summary_message}", normal_style))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("ONEE Tech Assistant - Outil de calculs électriques", sub_style))
    doc.build(story)
    buf.seek(0)
    return buf

# --- Fonctions de calcul améliorées pour la charge (avec courant) ---
def calculate_transformer_load(
    s_nom: float,
    currents: Tuple[float, float, float],
    cos_phases: Tuple[float, float, float],
    line_voltage: float,
    simultaneity: float,
    temp_amb: float,
    future_p: float
) -> Dict[str, Any]:
    """
    Calcule la charge du transformateur à partir des courants par phase.
    - currents : (I1, I2, I3) en A
    - cos_phases : (cosφ1, cosφ2, cosφ3)
    - line_voltage : tension composée (V)
    """
    # Tension simple
    phase_voltage = line_voltage / math.sqrt(3)

    # Puissance active par phase
    p_phases = [phase_voltage * I * cos for I, cos in zip(currents, cos_phases)]
    # Puissance apparente par phase
    s_phases = [phase_voltage * I for I in currents]  # S = V * I (monophasé)
    # Correction : on pourrait aussi utiliser S = sqrt(3)*U*I pour la puissance apparente totale,
    # mais pour la décomposition par phase, on garde cette approche.

    # Puissance active totale avec simultanéité
    p_active_total = sum(p_phases) * simultaneity
    # Puissance apparente totale avec simultanéité
    s_total = sum(s_phases) * simultaneity

    # Facteur de puissance global
    cos_global = p_active_total / s_total if s_total > 0 else 0

    # Déclassement par température
    if temp_amb > 40:
        derate_factor = 1 - Constants.TEMP_DERATE_COEFF * (temp_amb - 40)
        s_nom_derated = s_nom * derate_factor
    else:
        derate_factor = 1.0
        s_nom_derated = s_nom

    # Taux de charge actuel
    charge_actual = (s_total / s_nom_derated) * 100 if s_nom_derated > 0 else 0

    # Taux de charge futur
    if future_p > 0:
        # On suppose que le facteur de puissance global reste identique
        s_future = (future_p / cos_global) if cos_global > 0 else future_p / Constants.COS_PHI
        charge_future = (s_future / s_nom_derated) * 100 if s_nom_derated > 0 else 0
    else:
        future_p = 0
        s_future = 0
        charge_future = 0

    # Statut
    if charge_actual > Constants.CHARGE_CRITICAL:
        status = "err"
        message = f"🚨 SURCHARGE CRITIQUE ({charge_actual:.1f}%) — Intervention immédiate"
    elif charge_actual > Constants.CHARGE_WARNING:
        status = "warn"
        message = f"⚡ Charge ÉLEVÉE ({charge_actual:.1f}%) — Surveillance recommandée"
    else:
        status = "ok"
        message = f"✓ Charge NORMALE ({charge_actual:.1f}%) — Fonctionnement correct"

    message_future = ""
    if charge_future > 100 and future_p > 0:
        message_future = f"⚠️ Attention : avec la puissance prévue ({future_p:.1f} kW), le taux de charge atteindra {charge_future:.1f}%."

    return {
        "s_nom": s_nom,
        "s_nom_derated": s_nom_derated,
        "derate_factor": derate_factor,
        "currents": currents,
        "p_phases": p_phases,
        "s_phases": s_phases,
        "cos_phases": cos_phases,
        "p_active_total": p_active_total,
        "s_total": s_total,
        "cos_global": cos_global,
        "charge_actual": charge_actual,
        "future_p": future_p,
        "charge_future": charge_future,
        "status": status,
        "message": message,
        "message_future": message_future,
        "simultaneity": simultaneity,
        "temp_amb": temp_amb,
        "line_voltage": line_voltage
    }

def suggest_cable_section(s_total_kva, tension_v=400, L_m=100, material="Cuivre (Cu)"):
    I = (s_total_kva * 1000) / (math.sqrt(3) * tension_v)
    delta_u_max = 0.03 * tension_v
    rho = Constants.RESISTIVITY[material]
    cosphi = Constants.COS_PHI
    S_min = (math.sqrt(3) * I * rho * L_m * cosphi) / delta_u_max
    for s in Constants.CABLE_SECTIONS:
        if s >= S_min:
            return s
    return Constants.CABLE_SECTIONS[-1]

# --- Fonctions pour la chute de tension (inchangées) ---
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

# --- Interface principale ---
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
        st.markdown(f'<div class="cos-badge">cos φ de référence = {Constants.COS_PHI}</div>', unsafe_allow_html=True)
        st.markdown("### 📐 Formule")
        st.latex(r"\Delta U = \sqrt{3} \times I \times (R \times \cos\phi + X \times \sin\phi)")
        st.caption(f"cos φ = {Constants.COS_PHI} (constant pour la chute de tension)")
        st.caption("X = 0.08 Ω/km")
        st.markdown("---")
        if st.session_state.res_t1:
            ch = st.session_state.res_t1['charge_actual']
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
        st.caption("ΔU ≤ 3% (éclairage), ≤ 5% (force motrice)")
        st.caption("Déclassement température: -0,25%/°C >40°C")

    tab1, tab2 = st.tabs(["🔌 Charge Transformateur", "📉 Chute de Tension"])

    # ===================== TAB 1 : CHARGE TRANSFORMATEUR =====================
    with tab1:
        with st.container():
            st.markdown('<div class="calc-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">🔌 Charge Transformateur (saisie par courant)</div>', unsafe_allow_html=True)

            # Champs d'identification du poste
            col_id1, col_id2 = st.columns(2)
            with col_id1:
                poste_name = st.text_input("Nom du poste", value=st.session_state.poste_name, key="poste_name_input")
                st.session_state.poste_name = poste_name
            with col_id2:
                poste_matricule = st.text_input("Matricule du poste", value=st.session_state.poste_matricule, key="poste_matricule_input")
                st.session_state.poste_matricule = poste_matricule

            # Données nominales
            col1, col2, col3 = st.columns(3)
            with col1:
                s_nom = st.number_input("Puissance nominale (kVA)", min_value=1.0, value=100.0, step=10.0)
            with col2:
                temp_amb = st.number_input("Température ambiante (°C)", min_value=-20.0, value=40.0, step=1.0)
            with col3:
                line_voltage = st.number_input("Tension du réseau (V)", min_value=100.0, value=400.0, step=10.0, help="Tension composée (400 V pour BT standard)")

            # Facteur de simultanéité
            simultaneity = st.slider("Facteur de simultanéité", 0.5, 1.0, 1.0, 0.01, help="Coefficient pour tenir compte que toutes les charges ne fonctionnent pas en même temps.")

            # Courants par phase
            st.markdown("#### Courants par phase (A)")
            cols = st.columns(3)
            phase_labels = ["Phase 1", "Phase 2", "Phase 3"]
            default_currents = [65.0, 75.0, 45.0]
            currents = []
            for idx, (col, label, default) in enumerate(zip(cols, phase_labels, default_currents)):
                with col:
                    I = st.number_input(label, min_value=0.0, value=default, step=5.0, key=f"I_{idx}")
                    currents.append(I)

            # cos φ par phase
            st.markdown("#### Facteur de puissance par phase (cos φ)")
            cols_cos = st.columns(3)
            default_cos = [0.85, 0.82, 0.88]
            cos_vals = []
            for idx, (col, label, default) in enumerate(zip(cols_cos, phase_labels, default_cos)):
                with col:
                    cos = st.slider(f"{label}", 0.5, 1.0, default, 0.01, key=f"cos_{idx}")
                    cos_vals.append(cos)

            # Puissance future
            future_p = st.number_input("Puissance active prévue dans 5 ans (kW) - optionnel", min_value=0.0, value=0.0, step=10.0, help="Laissez 0 si non applicable")

            # Longueur pour recommandation de section
            cable_length = st.number_input("Longueur du câble BT (m) - pour recommandation de section", min_value=0.0, value=100.0, step=10.0)

            if st.button("Calculer la charge", key="btn_t1", use_container_width=True):
                result = calculate_transformer_load(
                    s_nom, tuple(currents), tuple(cos_vals), line_voltage, simultaneity, temp_amb, future_p
                )
                st.session_state.res_t1 = result

            if st.session_state.res_t1:
                r = st.session_state.res_t1

                # Taux de charge actuel
                st.markdown(f"""
                <div class="result-box result-{r['status']}">
                    <div class="result-label">TAUX DE CHARGE ACTUEL</div>
                    <div class="result-value">{r['charge_actual']:.1f} %</div>
                    <div class="result-msg">{r['message']}</div>
                </div>
                """, unsafe_allow_html=True)

                if r['message_future']:
                    st.warning(r['message_future'])

                # Affichage des paramètres importants
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Puissance active totale", f"{r['p_active_total']:.1f} kW")
                col2.metric("Puissance apparente totale", f"{r['s_total']:.1f} kVA")
                col3.metric("cos φ global", f"{r['cos_global']:.3f}")
                col4.metric("Facteur de déclassement", f"{r['derate_factor']:.3f}")

                st.markdown("---")
                st.markdown("#### Détail par phase")
                cols = st.columns(3)
                for idx, col in enumerate(cols):
                    with col:
                        st.markdown(f"""
                        <div style="background:#F8F9F8; border-radius:12px; padding:12px; margin:4px 0; border-left:4px solid #{'D32F2F' if idx==0 else '1B5E20'}">
                            <strong>Phase {idx+1}</strong><br/>
                            Courant: {r['currents'][idx]:.1f} A<br/>
                            cos φ: {r['cos_phases'][idx]:.2f}<br/>
                            P active: {r['p_phases'][idx]:.1f} kW<br/>
                            S: {r['s_phases'][idx]:.1f} kVA
                        </div>
                        """, unsafe_allow_html=True)

                # Recommandation de section de câble
                if cable_length > 0:
                    recommended_section = suggest_cable_section(r['s_total'], tension_v=line_voltage, L_m=cable_length, material="Cuivre (Cu)")
                    st.info(f"💡 **Section de câble recommandée** (pour une chute ≤ 3% sur {cable_length:.0f} m) : **{recommended_section} mm²** (Cuivre, cosφ=0.9)")
                else:
                    st.info("Indiquez la longueur du câble pour obtenir une recommandation de section.")

                # Préparation des données pour PDF
                data_rows = [
                    ("Nom du poste", r.get("poste_name", poste_name) or "", ""),
                    ("Matricule", r.get("poste_matricule", poste_matricule) or "", ""),
                    ("Puissance nominale", f"{r['s_nom']:.1f}", "kVA"),
                    ("Facteur de simultanéité", f"{r['simultaneity']:.2f}", ""),
                    ("Température ambiante", f"{r['temp_amb']:.0f}", "°C"),
                    ("Facteur de déclassement", f"{r['derate_factor']:.3f}", ""),
                    ("Puissance nominale déclassée", f"{r['s_nom_derated']:.1f}", "kVA"),
                    ("Puissance active totale", f"{r['p_active_total']:.1f}", "kW"),
                    ("Puissance apparente totale", f"{r['s_total']:.1f}", "kVA"),
                    ("cos φ global", f"{r['cos_global']:.3f}", ""),
                    ("Taux de charge actuel", f"{r['charge_actual']:.1f}", "%"),
                ]
                if r['future_p'] > 0:
                    data_rows.append(("Puissance future", f"{r['future_p']:.1f}", "kW"))
                    data_rows.append(("Taux de charge futur", f"{r['charge_future']:.1f}", "%"))
                # Ajouter les détails par phase
                for i in range(3):
                    data_rows.append((f"Courant phase {i+1}", f"{r['currents'][i]:.1f}", "A"))
                    data_rows.append((f"cos φ phase {i+1}", f"{r['cos_phases'][i]:.2f}", ""))
                    data_rows.append((f"P active phase {i+1}", f"{r['p_phases'][i]:.1f}", "kW"))
                    data_rows.append((f"S phase {i+1}", f"{r['s_phases'][i]:.1f}", "kVA"))

                if REPORTLAB_AVAILABLE:
                    pdf_buffer = generate_pdf_report(
                        "Rapport Charge Transformateur", data_rows, r['message'],
                        client_name="", poste_name=poste_name, poste_matricule=poste_matricule
                    )
                    if pdf_buffer:
                        st.download_button(
                            label="📄 Télécharger le rapport PDF",
                            data=pdf_buffer,
                            file_name=f"ONEE_Charge_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf",
                            key="pdf_t1",
                            use_container_width=True
                        )
                else:
                    st.info("Installation de reportlab requise pour le PDF")

            st.markdown('</div>', unsafe_allow_html=True)

    # ===================== TAB 2 : CHUTE DE TENSION =====================
    with tab2:
        with st.container():
            st.markdown('<div class="calc-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📉 Chute de Tension</div>', unsafe_allow_html=True)

            # Ligne client
            col_client1, col_client2 = st.columns([1, 3])
            with col_client1:
                st.markdown("**Nom du client**")
            with col_client2:
                client_name = st.text_input("", value=st.session_state.client_name, key="client_name_input", label_visibility="collapsed", placeholder="Saisir le nom du client")
                st.session_state.client_name = client_name
            st.markdown("---")

            st.info(f"📐 Facteur de puissance constant: cos φ = {Constants.COS_PHI}")

            st.markdown("#### Courants par phase")
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

                # Chutes par phase
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

                # Données pour PDF
                data_rows = [
                    ("Tension réseau", f"{tension_ref:.0f}", "V"),
                    ("Courant Phase 1", f"{currents[0]:.1f}", "A"),
                    ("Courant Phase 2", f"{currents[1]:.1f}", "A"),
                    ("Courant Phase 3", f"{currents[2]:.1f}", "A"),
                    ("Courant moyen", f"{r['imbalance']['i_avg']:.2f}", "A"),
                    ("Longueur câble", f"{L:.1f}", "m"),
                    ("Section câble", f"{section}", "mm²"),
                    ("Matériau", material, ""),
                    ("cos φ", f"{Constants.COS_PHI}", ""),
                    ("Chute moyenne", f"{r['avg_drop']:.2f}", "%"),
                    ("Chute max", f"{r['max_drop']:.2f}", "%"),
                    ("Chute min", f"{r['min_drop']:.2f}", "%"),
                    ("Tension arrivée (est.)", f"{tension_ref - (r['max_drop']/100 * tension_ref):.1f}", "V"),
                ]
                if REPORTLAB_AVAILABLE:
                    pdf_buffer = generate_pdf_report(
                        "Rapport Chute de Tension", data_rows, r['message'],
                        client_name=st.session_state.client_name, poste_name="", poste_matricule=""
                    )
                    if pdf_buffer:
                        st.download_button(
                            label="📄 Télécharger le rapport PDF",
                            data=pdf_buffer,
                            file_name=f"ONEE_ChuteTension_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf",
                            key="pdf_t2",
                            use_container_width=True
                        )
                else:
                    st.info("Installation de reportlab requise pour le PDF")

            st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div class="onee-footer">
        <span class="badge">ONEE Tech v2.3</span>
        <span class="badge">cos φ = {Constants.COS_PHI}</span>
        <span class="badge">NFC 11-201</span>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
