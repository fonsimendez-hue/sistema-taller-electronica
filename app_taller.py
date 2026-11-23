import streamlit as st
import importlib
import base_datos as bd
import pestanas as pt

importlib.reload(bd)
importlib.reload(pt)

st.set_page_config(page_title="Gestión de Taller Electrónico", page_icon="🔌", layout="wide")

CLAVE_ACCESO = "taller2026"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔐 Acceso al Sistema de Taller Electrónico")
    clave_ingresada = st.text_input("Ingresa la contraseña de acceso:", type="password")
    if st.button("Ingresar", type="primary"):
        if clave_ingresada == CLAVE_ACCESO:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta.")
    st.stop()

st.title("🔌 Control Diario de Taller Electrónico (En la Nube)")
tab1, tab2, tab3, tab4 = st.tabs([
    "➕ 1. Ingreso", 
    "🔍 2. Buscar y Modificar Orden", 
    "🛡️ 3. Garantía", 
    "📊 4. Excel y General"
])

with tab1:
    pt.mostrar_ingreso()
with tab2:
    pt.mostrar_edicion()
with tab3:
    pt.mostrar_garantia()
with tab4:
    pt.mostrar_excel()