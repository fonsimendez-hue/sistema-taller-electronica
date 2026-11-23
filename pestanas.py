import streamlit as st
from datetime import datetime, date
import importlib
import base_datos as bd
import pestana_edicion as pe

importlib.reload(pe)

def mostrar_ingreso():
    with st.form("form_ingreso", clear_on_submit=True):
        c1, c2, c3 = st.columns([1.2, 1.5, 2.3])
        fecha_ing = c1.date_input("A. Fecha", value=date.today())
        df_actual = bd.leer_ordenes()
        ot_sug = f"OT-{len(df_actual) + 1:03d}"
        ot = c2.text_input("B. Orden de Trabajo *", value=ot_sug)
        cliente = c3.text_input("B2. Nombre del Cliente *")
        
        e1, e2, e3, e4 = st.columns(4)
        articulo = e1.text_input("C. Artículo *")
        marca = e2.text_input("D. Marca *")
        modelo = e3.text_input("E. Modelo")
        serie = e4.text_input("F. Serie")
        
        f1, f2 = st.columns(2)
        falla = f1.text_area("G. Falla reportada *")
        plazo_gar = f2.selectbox("L. Plazo Garantía:", ["30 días", "60 días", "90 días", "6 meses", "Sin garantía"])
        coment_ini = f2.text_area("S. Comentarios iniciales:")
        
        if st.form_submit_button("💾 Guardar Ingreso en Google Drive", type="primary"):
            if ot and cliente and articulo and falla:
                fila = [
                    fecha_ing.strftime("%d/%m/%Y"), ot, cliente, articulo, marca, modelo, serie,
                    falla, "", 0.0, 0.0, 0.0, plazo_gar, "Pendiente", "", "", "No", "", "Pendiente",
                    coment_ini, "No", "", "", "", "", ""
                ]
                bd.agregar_orden(fila)
                st.success(f"✅ Orden {ot} guardada en Google Drive.")
            else:
                st.error("⚠️ Llena los campos con (*).")

def mostrar_edicion():
    pe.mostrar()

def mostrar_garantia():
    df_g = bd.leer_ordenes()
    if df_g.empty:
        return
    ot_g = st.selectbox("Orden por Garantía:", df_g.iloc[::-1]["orden_trabajo"].tolist())
    rg = df_g[df_g["orden_trabajo"] == ot_g].squeeze()
    with st.form("form_gar"):
        g1, g2 = st.columns(2)
        es_g = g1.selectbox("V. ¿Ingresa por Garantía?", ["No", "Sí"], index=1 if rg["es_garantia"] == "Sí" else 0)
        f_ig = g2.text_input("Fecha Ingreso Garantía:", value=str(rg["fecha_ingreso_garantia"]) or date.today().strftime("%d/%m/%Y"))
        falla_g = st.text_area("Falla en Garantía:", value=str(rg["falla_garantia"]))
        proc_g = st.text_area("Procedimiento aplicado:", value=str(rg["procedimiento_garantia"]))
        g3, g4 = st.columns(2)
        f_lg = g3.text_input("Fecha Listo Garantía:", value=str(rg["fecha_listo_garantia"]))
        f_rg = g4.text_input("Fecha Retiro Garantía:", value=str(rg["fecha_retiro_garantia"]))
        if st.form_submit_button("💾 Guardar Garantía en la Nube", type="primary"):
            bd.actualizar_orden(ot_g, {
                "es_garantia": es_g, "fecha_ingreso_garantia": f_ig, "falla_garantia": falla_g,
                "procedimiento_garantia": proc_g, "fecha_listo_garantia": f_lg, "fecha_retiro_garantia": f_rg
            })
            st.success("✅ Garantía guardada.")
            st.rerun()

def mostrar_excel():
    df_all = bd.leer_ordenes()
    if df_all.empty:
        return
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Órdenes", len(df_all))
    m2.metric("Pendientes de Retiro", len(df_all[df_all["retirado"] == "No"]))
    m3.metric("Total Cobrado / Presupuestado", f"₡{df_all['total'].sum():,.2f}")
    df_vista = df_all.copy()
    for col_m in ["presupuesto", "iva", "total"]:
        df_vista[col_m] = df_vista[col_m].apply(lambda x: f"₡{x:,.2f}")
    st.dataframe(df_vista, use_container_width=True, hide_index=True)
    st.download_button("📥 Descargar Excel (.xlsx) Exacto", data=bd.generar_excel(df_all),
        file_name=f"Taller_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")