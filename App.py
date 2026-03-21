import streamlit as st
import math
import io
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ONEE Tech Assistant",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── Session state init ─────────────────────────────────────────────────────────
for key in ["res_t1", "res_t2"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ── Custom CSS (Charte ONEE) ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700;800&family=Barlow+Condensed:wght@700;800&display=swap');

:root {
    --onee-green:  #00793B;
    --onee-dark:   #00501F;
    --onee-light:  #E8F5EE;
    --onee-accent: #F4A800;
    --onee-red:    #D32F2F;
    --bg:          #F4F6F0;
    --card:        #FFFFFF;
    --text:        #1A2E1A;
    --muted:       #5A7A5A;
    --border:      #C8DCC8;
}

* { font-family: 'Barlow', sans-serif; }

.stApp {
    background: var(--bg);
}

/* Header UI */
.onee-header {
    background: linear-gradient(135deg, var(--onee-dark) 0%, var(--onee-green) 100%);
    border-radius: 20px;
    padding: 32px 36px 28px;
    margin-bottom: 28px;
    position: relative;
    box-shadow: 0 8px 32px rgba(0,80,31,0.25);
}
.onee-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 34px;
    font-weight: 800;
    color: #FFFFFF;
    margin: 0;
}

/* Cards & Components */
.calc-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 20px;
}
.result-box {
    border-radius: 12px;
    padding: 20px 24px;
    margin-top: 20px;
    border-left: 5px solid;
}
.result-ok   { background:#E8F5EE; border-color:var(--onee-green); }
.result-warn { background:#FFF8E1; border-color:var(--onee-accent); }
.result-err  { background:#FFEBEE; border-color:var(--onee-red);   }

/* Styles inputs */
.stNumberInput label, .stSlider label { font-weight: 700 !important; color: #1A2E1A !important; }

/* Boutons */
.stButton > button {
    background: linear-gradient(135deg, var(--onee-green), var(--onee-dark)) !important;
    color: white !important;
    border-radius: 10px !important;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ── Fonctions Export (Excel & PDF) ──────────────────────────────────────────────
def make_excel(title, data_rows):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rapport"
    ws.append([f"ONEE - {title}"])
    ws.append(["Paramètre", "Valeur", "Unité"])
    for row in data_rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def make_pdf(title, data_rows, statut):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    story = []
    story.append(Paragraph(f"ONEE - {title}", getSampleStyleSheet()['Title']))
    story.append(Paragraph(f"Statut : {statut}", getSampleStyleSheet()['Normal']))
    t = Table([["Paramètre", "Valeur", "Unité"]] + [[r[0], str(r[1]), r[2]] for r in data_rows])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0), colors.grey), ('GRID',(0,0),(-1,-1), 1, colors.black)]))
    story.append(t)
    doc.build(story)
    buf.seek(0)
    return buf

# ── Interface Principale ───────────────────────────────────────────────────────
st.markdown("""
<div class="onee-header">
    <div class="onee-title">ONEE Tech Assistant</div>
    <div style="color:rgba(255,255,255,0.7)">Version 2.2 - Améliorations Techniques (Réactance & Sécurité)</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔌 Charge Transformateur", "📉 Chute de Tension"])

# ── TAB 1 : Charge Transformateur ──────────────────────────────────────────────
with tab1:
    st.markdown('<div class="calc-card">', unsafe_allow_html=True)
    s_nom = st.number_input("Puissance nominale Sn (kVA)", value=100.0)
    p_reel = st.number_input("Puissance active P (kW)", value=80.0)
    cos_phi_t = st.slider("Facteur de puissance (cos φ)", 0.50, 1.0, 0.85, 0.01)

    if st.button("Calculer la charge"):
        s_reel = p_reel / cos_phi_t
        charge = (s_reel / s_nom) * 100
        
        # Modification Technique 3 : Sécurité cos phi = 1
        q_reel = 0.0 if cos_phi_t >= 1.0 else p_reel * math.tan(math.acos(cos_phi_t))

        if charge > 100: box_class, msg = "result-err", "SURCHARGE !"
        elif charge > 80: box_class, msg = "result-warn", "Attention : Charge élevée."
        else: box_class, msg = "result-ok", "Charge normale."

        st.session_state.res_t1 = {"charge": charge, "s_reel": s_reel, "q_reel": q_reel, "msg": msg, "class": box_class}

    if st.session_state.res_t1:
        res = st.session_state.res_t1
        st.markdown(f'<div class="result-box {res["class"]}"><small>Taux de charge</small><h3>{res["charge"]:.1f} %</h3>{res["msg"]}</div>', unsafe_allow_html=True)
        data = [("S réelle", round(res['s_reel'],2), "kVA"), ("Q réactive", round(res['q_reel'],2), "kVAR"), ("Charge", round(res['charge'],1), "%")]
        st.download_button("Export Excel", make_excel("Charge Transfo", data), "Charge.xlsx")
    st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 2 : Chute de Tension ───────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="calc-card">', unsafe_allow_html=True)
    i = st.number_input("Courant de ligne I (A)", value=50.0)
    L = st.number_input("Longueur (m)", value=100.0)
    section = st.selectbox("Section (mm²)", [16, 25, 35, 50, 70, 95, 120, 150])
    mat = st.radio("Métal", ["Cuivre", "Alu"])
    tension_ref = st.number_input("Tension (V)", value=400.0)
    cos_phi_2 = st.slider("cos φ charge", 0.50, 1.0, 0.85, 0.01)

    if st.button("Calculer ΔU"):
        # Modification Technique 1 : Intégration de la Réactance X
        rho = 0.0225 if mat == "Cuivre" else 0.036
        R = (rho * L) / section
        X = 0.00008 * L  # 0.08 ohm/km
        sin_phi = math.sqrt(1 - cos_phi_2**2)
        
        # Formule Triphasée complète
        delta_u = math.sqrt(3) * i * (R * cos_phi_2 + X * sin_phi)
        perc = (delta_u / tension_ref) * 100

        box_c = "result-ok" if perc <= 3 else "result-warn" if perc <= 5 else "result-err"
        st.session_state.res_t2 = {"delta_u": delta_u, "perc": perc, "class": box_c}

    if st.session_state.res_t2:
        res = st.session_state.res_t2
        st.markdown(f'<div class="result-box {res["class"]}"><small>Chute de tension (V + X)</small><h3>{res["delta_u"]:.2f} V ({res["perc"]:.2f}%)</h3></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
