import streamlit as st
import math
import io
import matplotlib.pyplot as plt
import numpy as np
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
    COS_PHI_CHARGE = 0.8
    SIN_PHI_CHARGE = math.sqrt(1 - COS_PHI_CHARGE**2)
    COS_PHI_CHUTE = 0.9
    SIN_PHI_CHUTE = math.sqrt(1 - COS_PHI_CHUTE**2)
    CABLE_SECTIONS = [16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]
    NETWORK_VOLTAGES = {"Triphasé BT (400V)": 400.0, "Monophasé (230V)": 230.0, "MT (5500V)": 5500.0}
    CHARGE_WARNING = 80.0
    CHARGE_CRITICAL = 100.0
    VOLTAGE_DROP_WARNING = 3.0
    VOLTAGE_DROP_CRITICAL = 5.0
    UNBALANCE_WARNING = 20.0
    UNBALANCE_CRITICAL = 30.0
    TEMP_DERATE_COEFF = 0.0025
    MAX_DEPARTS = 8

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
    # Données des départs pour la charge (courants initiaux à 0)
    if "departs_charge" not in st.session_state:
        st.session_state.departs_charge = [{
            "name": "Départ 1",
            "currents": [0.0, 0.0, 0.0],
            "coeff_individuel": None
        }]
    # Données des départs pour la chute (courants initiaux à 0)
    if "departs_chute" not in st.session_state:
        st.session_state.departs_chute = [{
            "name": "Départ 1",
            "currents": [0.0, 0.0, 0.0],
            "L": 100.0,
            "section": 16,
            "material": "Cuivre (Cu)"
        }]

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
    .metric-critical {
        background: #FFEBEE !important;
        border-left: 4px solid #D32F2F !important;
    }
    .metric-warning {
        background: #FFF3E0 !important;
        border-left: 4px solid #FF9800 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PDF Generation (inchangée) ---
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

# --- Fonctions de calcul pour la charge avec plusieurs départs ---
def calculate_depart_contributions(depart: dict, line_voltage: float, global_coeff: float) -> Tuple[float, float, float, float, list, list, list]:
    """Calcule pour un départ : P, Q, S (kVA) après application du coefficient de simultanéité.
       Retourne (P_total_kW, Q_total_kVAR, S_total_kVA, cos_phi_phase, p_phases, q_phases, s_phases)"""
    cos_phi = Constants.COS_PHI_CHARGE
    sin_phi = Constants.SIN_PHI_CHARGE
    phase_voltage = line_voltage / math.sqrt(3)
    # Puissance par phase
    p_phases = []
    q_phases = []
    s_phases = []
    for I in depart["currents"]:
        p = (phase_voltage * I * cos_phi) / 1000
        q = (phase_voltage * I * sin_phi) / 1000
        s = (phase_voltage * I) / 1000
        p_phases.append(p)
        q_phases.append(q)
        s_phases.append(s)
    # Coefficient individuel ou global
    coeff = depart["coeff_individuel"] if depart["coeff_individuel"] is not None else global_coeff
    p_total = sum(p_phases) * coeff
    q_total = sum(q_phases) * coeff
    s_total = math.sqrt(p_total**2 + q_total**2)
    # cos φ du départ (identique au global)
    cos_depart = cos_phi
    return p_total, q_total, s_total, cos_depart, p_phases, q_phases, s_phases

def calculate_transformer_load_multi_depart(
    s_nom: float,
    departs: List[dict],
    line_voltage: float,
    global_simultaneity: float,
    temp_amb: float,
    future_p: float
) -> Dict[str, Any]:
    """
    Calcule la charge totale du transformateur à partir de plusieurs départs.
    """
    p_total_all = 0.0
    q_total_all = 0.0
    details = []  # pour stocker les infos par départ
    for dep in departs:
        p_dep, q_dep, s_dep, cos_dep, p_ph, q_ph, s_ph = calculate_depart_contributions(dep, line_voltage, global_simultaneity)
        p_total_all += p_dep
        q_total_all += q_dep
        details.append({
            "name": dep["name"],
            "p": p_dep,
            "q": q_dep,
            "s": s_dep,
            "cos": cos_dep,
            "currents": dep["currents"],
            "coeff_applique": dep["coeff_individuel"] if dep["coeff_individuel"] is not None else global_simultaneity,
            "p_phases": p_ph,
            "q_phases": q_ph,
            "s_phases": s_ph
        })
    # Total après addition (pas de second coefficient, car déjà appliqué)
    p_total = p_total_all
    q_total = q_total_all
    s_total = math.sqrt(p_total**2 + q_total**2)
    cos_global = p_total / s_total if s_total > 0 else Constants.COS_PHI_CHARGE

    # Déclassement température
    if temp_amb > 40:
        derate_factor = 1 - Constants.TEMP_DERATE_COEFF * (temp_amb - 40)
        s_nom_derated = s_nom * derate_factor
    else:
        derate_factor = 1.0
        s_nom_derated = s_nom

    charge_actual = (s_total / s_nom_derated) * 100 if s_nom_derated > 0 else 0

    # Charge future
    if future_p > 0:
        s_future = future_p / Constants.COS_PHI_CHARGE
        charge_future = (s_future / s_nom_derated) * 100 if s_nom_derated > 0 else 0
    else:
        future_p = 0
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
        "p_total": p_total,
        "q_total": q_total,
        "s_total": s_total,
        "cos_global": cos_global,
        "charge_actual": charge_actual,
        "future_p": future_p,
        "charge_future": charge_future,
        "status": status,
        "message": message,
        "message_future": message_future,
        "details": details,
        "global_simultaneity": global_simultaneity,
        "temp_amb": temp_amb,
        "line_voltage": line_voltage
    }

def suggest_cable_section(s_total_kva, tension_v=400, L_m=100, material="Cuivre (Cu)"):
    I = (s_total_kva * 1000) / (math.sqrt(3) * tension_v)
    delta_u_max = 0.03 * tension_v
    rho = Constants.RESISTIVITY[material]
    cosphi = Constants.COS_PHI_CHARGE
    S_min = (math.sqrt(3) * I * rho * L_m * cosphi) / delta_u_max
    for s in Constants.CABLE_SECTIONS:
        if s >= S_min:
            return s
    return Constants.CABLE_SECTIONS[-1]

# --- Fonctions de calcul pour la chute de tension (départs) ---
def calculate_voltage_drop_per_phase(i_phase, L, section, material, tension_ref):
    cos_phi = Constants.COS_PHI_CHUTE
    sin_phi = Constants.SIN_PHI_CHUTE
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
    return {"delta_u": delta_u, "delta_u_resistive": delta_u_resistive, "delta_u_reactive": delta_u_reactive,
            "perc_drop": perc_drop, "R": R, "X": X, "S": S, "P": P, "Q": Q, "cos_phi": cos_phi}

def calculate_depart_results(currents, L, section, material, tension_ref):
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
    cos_phi_global = total_P / total_S if total_S > 0 else Constants.COS_PHI_CHUTE
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
        recommendations.append(f"Rééquilibrer les charges (déséquilibre: {max_dev:.1f}%)")
    if max_drop > Constants.VOLTAGE_DROP_WARNING:
        worst_idx = drops.index(max_drop)
        worst_current = currents[worst_idx]
        s_min = (Constants.RESISTIVITY[material] * L * math.sqrt(3) * worst_current * Constants.COS_PHI_CHUTE) / (0.05 * tension_ref)
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

# --- Fonctions d'affichage ---
def get_load_status(charge: float) -> Tuple[str, str]:
    if charge > Constants.CHARGE_CRITICAL:
        return "err", "❌ Surcharge critique"
    elif charge > Constants.CHARGE_WARNING:
        return "warn", "⚠️ Charge élevée"
    else:
        return "ok", "✅ Charge normale"

def get_drop_status(drop: float) -> Tuple[str, str]:
    if drop > Constants.VOLTAGE_DROP_CRITICAL:
        return "err", "❌ Non conforme (>5%)"
    elif drop > Constants.VOLTAGE_DROP_WARNING:
        return "warn", "⚠️ Limite (3-5%)"
    else:
        return "ok", "✅ Conforme (≤3%)"

def plot_voltage_drop_bar_chart(drops: List[float], phases: List[int], title="Chutes de tension"):
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(phases, drops, color=['#FF6B6B', '#4ECDC4', '#FFE66D'])
    ax.axhline(y=3, color='orange', linestyle='--', label='Seuil d\'alerte (3%)')
    ax.axhline(y=5, color='red', linestyle='--', label='Limite max (5%)')
    ax.set_ylabel('Chute de tension (%)')
    ax.set_xlabel('Phase')
    ax.set_title(title)
    ax.set_ylim(0, max(max(drops), 5.5))
    ax.legend()
    for bar, val in zip(bars, drops):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, f'{val:.1f}%', ha='center', va='bottom')
    st.pyplot(fig)

def generate_recommendations(load_result: Dict, depart_results: List[Dict]) -> List[str]:
    recs = []
    if load_result:
        charge = load_result['charge_actual']
        if charge > Constants.CHARGE_CRITICAL:
            recs.append("🔧 SURCHARGE TRANSFORMATEUR : Remplacez par un transformateur de puissance supérieure ou réduisez la charge.")
        elif charge > Constants.CHARGE_WARNING:
            recs.append("⚠️ CHARGE ÉLEVÉE : Surveillez l'évolution et prévoyez un renforcement.")
        if load_result['charge_future'] > 100 and load_result['future_p'] > 0:
            recs.append(f"📈 ÉVOLUTION FUTURE : Avec la puissance prévue ({load_result['future_p']:.0f} kW), le transformateur sera en surcharge. Anticipez un remplacement.")
    if depart_results:
        for idx, res in enumerate(depart_results):
            if res:
                if res['imbalance']['max_deviation'] > Constants.UNBALANCE_WARNING:
                    recs.append(f"⚖️ DÉPART {idx+1} : Déséquilibre de {res['imbalance']['max_deviation']:.1f}%. Répartissez les charges.")
                if res['max_drop'] > Constants.VOLTAGE_DROP_CRITICAL:
                    recs.append(f"📉 DÉPART {idx+1} : Chute excessive ({res['max_drop']:.2f}%). Augmentez la section du câble ou réduisez la distance.")
                elif res['max_drop'] > Constants.VOLTAGE_DROP_WARNING:
                    recs.append(f"⚠️ DÉPART {idx+1} : Chute limite ({res['max_drop']:.2f}%). Vérifiez le dimensionnement.")
                if res.get('recommendations'):
                    recs.extend(res['recommendations'])
    recs = list(dict.fromkeys(recs))
    return recs

# --- Interface principale ---
def main():
    load_css()
    st.markdown("""
    <div class="onee-header">
        <div class="onee-title">Tech Assistant</div>
        <div class="onee-subtitle">Calculs électriques BT/MT</div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### ⚙️ Paramètres")
        st.markdown(f'<div class="cos-badge">cos φ charge = {Constants.COS_PHI_CHARGE}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cos-badge">cos φ chute = {Constants.COS_PHI_CHUTE}</div>', unsafe_allow_html=True)
        st.markdown("### 📐 Formule")
        st.latex(r"\Delta U = \sqrt{3} \times I \times (R \times \cos\phi + X \times \sin\phi)")
        st.caption(f"cos φ = {Constants.COS_PHI_CHUTE} (chute de tension)")
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

    tab1, tab2 = st.tabs(["🔌 Charge Transformateur", "📉 Chute de Tension - Départs BT"])

    # ===================== TAB 1 : CHARGE TRANSFORMATEUR (multi-départs) =====================
    with tab1:
        with st.container():
            st.markdown('<div class="calc-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">🔌 Charge Transformateur - Multi départs BT (max 8)</div>', unsafe_allow_html=True)

            # Infos poste
            col_id1, col_id2 = st.columns(2)
            with col_id1:
                poste_name = st.text_input("Nom du poste", value=st.session_state.poste_name, key="poste_name_input")
                st.session_state.poste_name = poste_name
            with col_id2:
                poste_matricule = st.text_input("Matricule du poste", value=st.session_state.poste_matricule, key="poste_matricule_input")
                st.session_state.poste_matricule = poste_matricule

            # Paramètres généraux
            col1, col2, col3 = st.columns(3)
            with col1:
                s_nom = st.number_input("Puissance nominale (kVA)", min_value=1.0, value=100.0, step=10.0)
            with col2:
                temp_amb = st.number_input("Température ambiante (°C)", min_value=-20.0, value=40.0, step=1.0)
            with col3:
                line_voltage = st.number_input("Tension du réseau (V)", min_value=100.0, value=400.0, step=10.0)

            # Facteur de simultanéité global
            global_simultaneity = st.slider("Facteur de simultanéité global", 0.5, 1.0, 1.0, 0.01, help="Appliqué à tous les départs qui n'ont pas de coefficient individuel.")

            # Gestion des départs
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("➕ Ajouter un départ", use_container_width=True, key="add_depart_charge"):
                    if len(st.session_state.departs_charge) < Constants.MAX_DEPARTS:
                        st.session_state.departs_charge.append({
                            "name": f"Départ {len(st.session_state.departs_charge)+1}",
                            "currents": [0.0, 0.0, 0.0],
                            "coeff_individuel": None
                        })
                    else:
                        st.warning(f"Maximum {Constants.MAX_DEPARTS} départs atteint.")
            with col_btn2:
                if st.button("➖ Supprimer le dernier départ", use_container_width=True, key="remove_depart_charge"):
                    if len(st.session_state.departs_charge) > 1:
                        st.session_state.departs_charge.pop()
                    else:
                        st.warning("Il doit y avoir au moins un départ.")

            # Affichage des départs
            for i, depart in enumerate(st.session_state.departs_charge):
                with st.expander(f"📌 {depart['name']} (Départ {i+1})", expanded=False):
                    col_name, col_coeff = st.columns([2, 1])
                    with col_name:
                        new_name = st.text_input("Nom du départ", value=depart["name"], key=f"charge_name_{i}")
                        st.session_state.departs_charge[i]["name"] = new_name
                    with col_coeff:
                        coeff_val = depart["coeff_individuel"] if depart["coeff_individuel"] is not None else global_simultaneity
                        use_indiv = st.checkbox("Utiliser un coefficient individuel", value=(depart["coeff_individuel"] is not None), key=f"use_indiv_{i}")
                        if use_indiv:
                            indiv_coeff = st.slider("Coefficient (0.5-1)", 0.5, 1.0, coeff_val, 0.01, key=f"indiv_coeff_{i}")
                            st.session_state.departs_charge[i]["coeff_individuel"] = indiv_coeff
                        else:
                            st.session_state.departs_charge[i]["coeff_individuel"] = None
                    # Courants
                    st.markdown("**Courants par phase (A)**")
                    cols_c = st.columns(3)
                    currents = depart["currents"]
                    for j, col_c in enumerate(cols_c):
                        with col_c:
                            new_cur = st.number_input(f"Phase {j+1}", value=currents[j], step=5.0, key=f"charge_cur_{i}_{j}", format="%.1f")
                            currents[j] = new_cur
                    st.session_state.departs_charge[i]["currents"] = currents

            # Puissance future et longueur câble (pour recommandation)
            future_p = st.number_input("Puissance active prévue dans 5 ans (kW) - optionnel", min_value=0.0, value=0.0, step=10.0)
            cable_length = st.number_input("Longueur du câble BT (m) - pour recommandation de section", min_value=0.0, value=100.0, step=10.0)

            if st.button("Calculer la charge", key="btn_t1", use_container_width=True):
                result = calculate_transformer_load_multi_depart(
                    s_nom, st.session_state.departs_charge, line_voltage, global_simultaneity, temp_amb, future_p
                )
                st.session_state.res_t1 = result

            if st.session_state.res_t1:
                r = st.session_state.res_t1

                # Indicateur de conformité
                status, status_text = get_load_status(r['charge_actual'])
                st.markdown(f'<div style="display: flex; justify-content: space-between; align-items: center;">'
                            f'<div><span style="font-size: 24px; font-weight: bold;">Taux de charge</span></div>'
                            f'<div style="background: {"#4CAF50" if status=="ok" else "#FF9800" if status=="warn" else "#F44336"}; color: white; padding: 6px 12px; border-radius: 20px;">{status_text}</div>'
                            f'</div>', unsafe_allow_html=True)

                st.markdown(f"""
                <div class="result-box result-{r['status']}">
                    <div class="result-label">TAUX DE CHARGE ACTUEL</div>
                    <div class="result-value">{r['charge_actual']:.1f} %</div>
                    <div class="result-msg">{r['message']}</div>
                </div>
                """, unsafe_allow_html=True)

                if r['message_future']:
                    st.warning(r['message_future'])

                # Métriques globales
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Puissance active totale", f"{r['p_total']:.1f} kW")
                col2.metric("Puissance apparente totale", f"{r['s_total']:.1f} kVA")
                col3.metric("cos φ global", f"{r['cos_global']:.3f}")
                col4.metric("Facteur de déclassement", f"{r['derate_factor']:.3f}")

                # Détail par départ
                st.markdown("---")
                st.markdown("#### Détail par départ")
                for idx, dep in enumerate(r['details']):
                    with st.expander(f"{dep['name']} - P: {dep['p']:.1f} kW, S: {dep['s']:.1f} kVA", expanded=False):
                        st.markdown(f"**Courants :** {dep['currents'][0]:.1f} A / {dep['currents'][1]:.1f} A / {dep['currents'][2]:.1f} A")
                        st.markdown(f"**Coefficient appliqué :** {dep['coeff_applique']:.2f}")
                        st.markdown(f"**Puissance active :** {dep['p']:.1f} kW")
                        st.markdown(f"**Puissance réactive :** {dep['q']:.1f} kVAR")
                        st.markdown(f"**Puissance apparente :** {dep['s']:.1f} kVA")
                        st.markdown(f"**cos φ :** {dep['cos']:.2f}")
                        # Détail par phase
                        st.markdown("**Détail par phase**")
                        cols_ph = st.columns(3)
                        for j, col_ph in enumerate(cols_ph):
                            with col_ph:
                                st.markdown(f"Phase {j+1}<br/>P: {dep['p_phases'][j]:.2f} kW<br/>Q: {dep['q_phases'][j]:.2f} kVAR<br/>S: {dep['s_phases'][j]:.2f} kVA", unsafe_allow_html=True)

                # Recommandation section câble (globale)
                if cable_length > 0:
                    recommended_section = suggest_cable_section(r['s_total'], tension_v=line_voltage, L_m=cable_length, material="Cuivre (Cu)")
                    st.info(f"💡 **Section de câble recommandée** (pour une chute ≤ 3% sur {cable_length:.0f} m) : **{recommended_section} mm²** (Cuivre, cosφ={Constants.COS_PHI_CHARGE})")
                else:
                    st.info("Indiquez la longueur du câble pour obtenir une recommandation de section.")

                if r['charge_actual'] > Constants.CHARGE_WARNING:
                    st.warning("### 💡 Recommandation\n" + ("Augmenter la puissance du transformateur ou réduire la charge." if r['charge_actual'] > Constants.CHARGE_CRITICAL else "Surveiller l'évolution de la charge."))

                # Export PDF pour la charge
                data_rows = [
                    ("Nom du poste", poste_name or "", ""),
                    ("Matricule", poste_matricule or "", ""),
                    ("Puissance nominale", f"{r['s_nom']:.1f}", "kVA"),
                    ("Facteur de simultanéité global", f"{r['global_simultaneity']:.2f}", ""),
                    ("Température ambiante", f"{r['temp_amb']:.0f}", "°C"),
                    ("Facteur de déclassement", f"{r['derate_factor']:.3f}", ""),
                    ("Puissance nominale déclassée", f"{r['s_nom_derated']:.1f}", "kVA"),
                    ("Puissance active totale", f"{r['p_total']:.1f}", "kW"),
                    ("Puissance réactive totale", f"{r['q_total']:.1f}", "kVAR"),
                    ("Puissance apparente totale", f"{r['s_total']:.1f}", "kVA"),
                    ("cos φ global", f"{r['cos_global']:.3f}", ""),
                    ("Taux de charge actuel", f"{r['charge_actual']:.1f}", "%"),
                ]
                if r['future_p'] > 0:
                    data_rows.append(("Puissance future", f"{r['future_p']:.1f}", "kW"))
                    data_rows.append(("Taux de charge futur", f"{r['charge_future']:.1f}", "%"))
                for i, dep in enumerate(r['details']):
                    data_rows.append((f"Départ {i+1} - {dep['name']}", "", ""))
                    data_rows.append((f"  Courants", f"{dep['currents'][0]:.1f}/{dep['currents'][1]:.1f}/{dep['currents'][2]:.1f}", "A"))
                    data_rows.append((f"  Coefficient appliqué", f"{dep['coeff_applique']:.2f}", ""))
                    data_rows.append((f"  P", f"{dep['p']:.1f}", "kW"))
                    data_rows.append((f"  Q", f"{dep['q']:.1f}", "kVAR"))
                    data_rows.append((f"  S", f"{dep['s']:.1f}", "kVA"))

                if REPORTLAB_AVAILABLE:
                    pdf_buffer = generate_pdf_report("Rapport Charge Transformateur - Multi départs", data_rows, r['message'],
                                                      client_name="", poste_name=poste_name, poste_matricule=poste_matricule)
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

    # ===================== TAB 2 : CHUTE DE TENSION - DÉPARTS BT =====================
    with tab2:
        with st.container():
            st.markdown('<div class="calc-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📉 Chute de Tension - Départs BT (max 8)</div>', unsafe_allow_html=True)

            # Ligne client
            col_client1, col_client2 = st.columns([1, 3])
            with col_client1:
                st.markdown("**Nom du client**")
            with col_client2:
                client_name = st.text_input("", value=st.session_state.client_name, key="client_name_input", label_visibility="collapsed", placeholder="Saisir le nom du client")
                st.session_state.client_name = client_name
            st.markdown("---")

            st.info(f"📐 Facteur de puissance constant: cos φ = {Constants.COS_PHI_CHUTE}")

            # Tension source
            source_voltage = st.number_input(
                "Tension au départ (source) [V]",
                min_value=100.0,
                value=400.0,
                step=10.0,
                help="Tension aux bornes du transformateur (côté BT)"
            )
            tension_ref = source_voltage

            # Gestion des départs pour la chute
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("➕ Ajouter un départ", key="add_depart_chute", use_container_width=True):
                    if len(st.session_state.departs_chute) < Constants.MAX_DEPARTS:
                        st.session_state.departs_chute.append({
                            "name": f"Départ {len(st.session_state.departs_chute)+1}",
                            "currents": [0.0, 0.0, 0.0],
                            "L": 100.0,
                            "section": 16,
                            "material": "Cuivre (Cu)"
                        })
                    else:
                        st.warning(f"Maximum {Constants.MAX_DEPARTS} départs atteint.")
            with col_btn2:
                if st.button("➖ Supprimer le dernier départ", key="remove_depart_chute", use_container_width=True):
                    if len(st.session_state.departs_chute) > 1:
                        st.session_state.departs_chute.pop()
                    else:
                        st.warning("Il doit y avoir au moins un départ.")

            # Affichage des départs
            for i, depart in enumerate(st.session_state.departs_chute):
                with st.expander(f"📌 {depart['name']} (Départ {i+1})", expanded=False):
                    col_name, col_other = st.columns([1, 2])
                    with col_name:
                        new_name = st.text_input("Nom du départ", value=depart["name"], key=f"chute_name_{i}")
                        st.session_state.departs_chute[i]["name"] = new_name
                    # Courants
                    st.markdown("**Courants par phase (A)**")
                    cols_c = st.columns(3)
                    currents = depart["currents"]
                    for j, col_c in enumerate(cols_c):
                        with col_c:
                            new_cur = st.number_input(f"Phase {j+1}", value=currents[j], step=5.0, key=f"chute_cur_{i}_{j}", format="%.1f")
                            currents[j] = new_cur
                    st.session_state.departs_chute[i]["currents"] = currents
                    colL, colS, colM = st.columns(3)
                    with colL:
                        L = st.number_input("Longueur (m)", value=depart["L"], step=10.0, key=f"chute_L_{i}")
                        st.session_state.departs_chute[i]["L"] = L
                    with colS:
                        section = st.selectbox("Section (mm²)", Constants.CABLE_SECTIONS, index=Constants.CABLE_SECTIONS.index(depart["section"]), key=f"chute_sec_{i}")
                        st.session_state.departs_chute[i]["section"] = section
                    with colM:
                        material = st.selectbox("Matériau", list(Constants.RESISTIVITY.keys()), index=0 if depart["material"]=="Cuivre (Cu)" else 1, key=f"chute_mat_{i}")
                        st.session_state.departs_chute[i]["material"] = material

            if st.button("Calculer tous les départs", key="btn_t2", use_container_width=True):
                depart_results = []
                for depart in st.session_state.departs_chute:
                    res = calculate_depart_results(depart["currents"], depart["L"], depart["section"], depart["material"], tension_ref)
                    depart_results.append(res)
                st.session_state.depart_results = depart_results
                st.session_state.res_t2 = {"max_drop": max([r["max_drop"] for r in depart_results]) if depart_results else 0}

            if hasattr(st.session_state, "depart_results") and st.session_state.depart_results:
                st.markdown("---")
                st.markdown("### Résultats par départ")
                critical_depart = None
                max_drop_overall = 0
                for idx, res in enumerate(st.session_state.depart_results):
                    depart_name = st.session_state.departs_chute[idx]["name"]
                    drop_max = res["max_drop"]
                    if drop_max > max_drop_overall:
                        max_drop_overall = drop_max
                        critical_depart = depart_name
                    with st.expander(f"📊 {depart_name} - Chute max: {drop_max:.2f}%", expanded=False):
                        # Conformité
                        status, status_text = get_drop_status(drop_max)
                        st.markdown(f'<div style="background: {"#4CAF50" if status=="ok" else "#FF9800" if status=="warn" else "#F44336"}; color: white; padding: 4px 8px; border-radius: 12px; display: inline-block; margin-bottom: 12px;">{status_text}</div>', unsafe_allow_html=True)

                        # Graphique
                        phases = [1,2,3]
                        drops = [p["perc_drop"] for p in res["phases"]]
                        plot_voltage_drop_bar_chart(drops, phases, title=f"{depart_name} - Chutes par phase")

                        # Déséquilibre
                        st.markdown(f"""
                        <div class="result-box result-{res['imbalance']['status']}" style="padding:12px; margin-top:8px;">
                            <div class="result-label">DÉSÉQUILIBRE</div>
                            <div class="result-value" style="font-size:24px;">{res['imbalance']['max_deviation']:.1f} %</div>
                            <div class="result-msg">{res['imbalance']['message']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Détail phases
                        st.markdown("**Détail des phases**")
                        cols = st.columns(3)
                        for ph_idx, col in enumerate(cols):
                            ph = res["phases"][ph_idx]
                            color = "#D32F2F" if ph_idx == 0 else "#1B5E20"
                            bg_color = "#FFEBEE" if ph['perc_drop'] > 5 else ("#FFF3E0" if ph['perc_drop'] > 3 else "#F8F9F8")
                            with col:
                                st.markdown(f"""
                                <div style="background:{bg_color}; border-radius:8px; padding:8px; border-left:3px solid {color};">
                                    <strong>Phase {ph_idx+1}</strong><br/>
                                    Courant: {ph['current']:.1f} A<br/>
                                    Chute: <span style="font-size:18px; font-weight:800; color:{color};">{ph['perc_drop']:.2f}%</span><br/>
                                    ΔU: {ph['delta_u']:.1f} V
                                </div>
                                """, unsafe_allow_html=True)

                        if res["recommendations"]:
                            st.warning("#### 💡 Recommandations")
                            for rec in res["recommendations"]:
                                st.write(f"• {rec}")

                # Synthèse globale
                st.markdown("---")
                st.markdown("### 📋 Synthèse générale")
                st.info(f"**Départ le plus critique :** {critical_depart} avec une chute de {max_drop_overall:.2f}%")
                if max_drop_overall > Constants.VOLTAGE_DROP_CRITICAL:
                    st.error("❌ La chute de tension dépasse la limite réglementaire (5%). Une action corrective est nécessaire.")
                elif max_drop_overall > Constants.VOLTAGE_DROP_WARNING:
                    st.warning("⚠️ La chute de tension est proche de la limite. Surveillez l'installation.")
                else:
                    st.success("✅ Tous les départs respectent les limites de chute de tension.")

                # Recommandations globales
                all_recs = generate_recommendations(st.session_state.res_t1, st.session_state.depart_results)
                if all_recs:
                    st.warning("### 💡 Recommandations globales")
                    for rec in all_recs:
                        st.write(f"• {rec}")

                # Export PDF
                if REPORTLAB_AVAILABLE:
                    all_data_rows = [("Tension source", f"{tension_ref:.0f}", "V")]
                    for idx, depart in enumerate(st.session_state.departs_chute):
                        res = st.session_state.depart_results[idx]
                        all_data_rows.append((f"Départ {depart['name']} - Chute max", f"{res['max_drop']:.2f}", "%"))
                        all_data_rows.append((f"Départ {depart['name']} - Déséquilibre", f"{res['imbalance']['max_deviation']:.1f}", "%"))
                        for j in range(3):
                            all_data_rows.append((f"  Phase {j+1} courant", f"{depart['currents'][j]:.1f}", "A"))
                            all_data_rows.append((f"  Phase {j+1} chute", f"{res['phases'][j]['perc_drop']:.2f}", "%"))
                        all_data_rows.append((f"  Longueur", f"{depart['L']:.1f}", "m"))
                        all_data_rows.append((f"  Section", f"{depart['section']}", "mm²"))
                        all_data_rows.append((f"  Matériau", depart["material"], ""))
                    summary_msg = f"Départ critique: {critical_depart} avec {max_drop_overall:.2f}% de chute."
                    pdf_buffer = generate_pdf_report("Rapport Chute de Tension - Départs BT", all_data_rows, summary_msg,
                                                      client_name=st.session_state.client_name, poste_name=st.session_state.poste_name, poste_matricule=st.session_state.poste_matricule)
                    if pdf_buffer:
                        st.download_button(
                            label="📄 Télécharger le rapport complet (PDF)",
                            data=pdf_buffer,
                            file_name=f"ONEE_ChuteTension_Departs_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
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
        <span class="badge">Tech Assistant v3.2</span>
        <span class="badge">cos φ charge = {Constants.COS_PHI_CHARGE}</span>
        <span class="badge">cos φ chute = {Constants.COS_PHI_CHUTE}</span>
        <span class="badge">NFC 11-201</span>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
