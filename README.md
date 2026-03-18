# app.mu
import streamlit as st
import math

st.set_page_config(page_title="ONEE Tech Assistant", page_icon="⚡")

st.title("⚡ مساعد تقني الكهرباء (ONEE)")
st.subheader("حساب حمولة المحول وهبوط الجهد")

tab1, tab2 = st.tabs(["Charge Transfo", "Chute de Tension"])

with tab1:
    st.header("📊 Charge du Transformateur")
    s_nom = st.number_input("القدرة الاسمية للمحول (kVA)", value=100.0)
    p_reel = st.number_input("القدرة الفعالة الحالية (kW)", value=80.0)
    cos_phi_t = st.slider("معامل القدرة (cos φ)", 0.0, 1.0, 0.85, key="t1")
    
    if st.button("احسب الحمولة"):
        s_reel = p_reel / cos_phi_t
        charge = (s_reel / s_nom) * 100
        st.metric("الحمولة (%)", f"{charge:.2f} %")
        if charge > 100:
            st.error("⚠️ تحذير: المحول في حالة حمل زائد (Surcharge)!")
        elif charge > 80:
            st.warning("تنبيه: الحمولة مرتفعة.")
        else:
            st.success("الحمولة عادية.")

with tab2:
    st.header("📉 Chute de Tension (Triphasé)")
    i = st.number_input("شدة التيار (Ampère)", value=50.0)
    L = st.number_input("طول الكابل (Mètre)", value=100.0)
    section = st.selectbox("مقطع الكابل (mm²)", [16, 25, 35, 50, 70, 95, 120, 150])
    material = st.radio("مادة الكابل", ["Cuivre (النحاس)", "Aluminium (الألومنيوم)"])
    
    # قيم تقريبية للمقاومة (R) حسب المقطع والمادة
    r_val = 0.0225 if "Cuivre" in material else 0.036 # rho
    R = (r_val * L) / section
    
    if st.button("احسب هبوط الجهد"):
        # حساب مبسط: Delta U = sqrt(3) * I * R (إهمال X في المسافات القصيرة)
        delta_u = math.sqrt(3) * i * (r_val * L / section)
        perc_drop = (delta_u / 400) * 100
        
        st.write(f"هبوط الجهد هو: **{delta_u:.2f} Volt**")
        st.metric("نسبة الهبوط (%)", f"{perc_drop:.2f} %")
        
        if perc_drop > 5:
            st.error("❌ هبوط الجهد يتجاوز 5% (غير مقبول حسب المعايير)")
        else:
            st.success("✅ هبوط الجهد ضمن الحدود المقبولة.")

st.info("ملاحظة: هذه الحسابات تقريبية للمساعدة في الميدان.")
