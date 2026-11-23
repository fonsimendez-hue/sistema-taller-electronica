import streamlit as st
from datetime import date
import base_datos as bd

def mostrar():
    df = bd.leer_ordenes()
    if df.empty:
        st.info("No hay órdenes todavía.")
        return
    df_inv = df.iloc[::-1]
    busq = st.text_input("🔍 Buscar por N° Orden, Cliente, Artículo, Marca o Serie:")
    if busq:
        df_filt = df_inv[
            df_inv["orden_trabajo"].astype(str).str.contains(busq, case=False, na=False) |
            df_inv["cliente"].astype(str).str.contains(busq, case=False, na=False) |
            df_inv["articulo"].astype(str).str.contains(busq, case=False, na=False) |
            df_inv["marca"].astype(str).str.contains(busq, case=False, na=False) |
            df_inv["serie"].astype(str).str.contains(busq, case=False, na=False)
        ]
    else:
        df_filt = df_inv
    if df_filt.empty:
        st.warning("No se encontraron órdenes con esa búsqueda.")
        return
    opciones = df_filt["orden_trabajo"].tolist()
    sel_ot = st.selectbox("Selecciona la Orden a editar o imprimir:", opciones,
        format_func=lambda x: f"{x} | {df_filt[df_filt['orden_trabajo']==x]['cliente'].squeeze()} - {df_filt[df_filt['orden_trabajo']==x]['articulo'].squeeze()}")
    row = df[df["orden_trabajo"] == sel_ot].squeeze()

    ed1, ed2, ed3, ed4 = st.columns(4)
    ed_cliente = ed1.text_input("Cliente:", value=str(row["cliente"]), key=f"c_{sel_ot}")
    ed_articulo = ed2.text_input("Artículo:", value=str(row["articulo"]), key=f"a_{sel_ot}")
    ed_marca = ed3.text_input("Marca:", value=str(row["marca"]), key=f"m_{sel_ot}")
    ed_modelo = ed4.text_input("Modelo:", value=str(row["modelo"]), key=f"mo_{sel_ot}")

    ed5, ed6 = st.columns(2)
    ed_serie = ed5.text_input("Serie:", value=str(row["serie"]), key=f"s_{sel_ot}")
    ed_falla = ed6.text_input("Falla reportada:", value=str(row["falla"]), key=f"f_{sel_ot}")
    st.divider()

    col_d, col_p = st.columns(2)
    diag = col_d.text_area("H. Diagnóstico:", value=str(row["diagnostico"]), height=120, key=f"d_{sel_ot}")
    
    clave_p = f"p_{sel_ot}"
    if clave_p not in st.session_state:
        st.session_state[clave_p] = str(int(float(row["presupuesto"] or 0)))
        
    presup_txt = col_p.text_input("I. Presupuesto sin IVA (₡):", key=clave_p)
    try:
        limpio = presup_txt.replace("₡", "").replace(" ", "").replace(",", "")
        presup = float(limpio or 0)
    except ValueError:
        presup = 0.0
        
    con_iva = col_p.checkbox("Calcular 13% IVA (J)", value=True, key=f"iva_{sel_ot}")
    iva_val = round(presup * 0.13, 2) if con_iva else 0.0
    tot_val = presup + iva_val
    col_p.markdown(f"*I. Presupuesto:* ₡{presup:,.2f} | *J. IVA:* ₡{iva_val:,.2f} | *K. Total:* ₡{tot_val:,.2f}")

    c_m, c_n, c_o = st.columns(3)
    ops_ac = ["Pendiente", "Sí", "No"]
    ac = c_m.selectbox("M. ¿Aceptado?", ops_ac, index=ops_ac.index(row["aceptado"]) if row["aceptado"] in ops_ac else 0, key=f"ac_{sel_ot}")
    f_ac = c_n.text_input("N. Fecha Aceptado:", value=str(row["fecha_aceptado"]), key=f"fac_{sel_ot}")
    f_li = c_o.text_input("O. Fecha Listo:", value=str(row["fecha_listo"]), key=f"fli_{sel_ot}")

    c_p, c_q, c_r = st.columns(3)
    ops_ret = ["No", "Sí"]
    ret = c_p.selectbox("P. ¿Retirado?", ops_ret, index=ops_ret.index(row["retirado"]) if row["retirado"] in ops_ret else 0, key=f"ret_{sel_ot}")
    f_ret = c_q.text_input("Q. Fecha Retirado:", value=str(row["fecha_retirado"]), key=f"fret_{sel_ot}")
    medios = ["Pendiente", "SINPE Móvil", "Efectivo", "Transferencia", "Tarjeta", "No aplica"]
    pago = c_r.selectbox("R. Medio Pago:", medios, index=medios.index(row["medio_pago"]) if row["medio_pago"] in medios else 0, key=f"pag_{sel_ot}")
    coment = st.text_area("S. Comentarios:", value=str(row["comentarios"]), height=130, key=f"com_{sel_ot}")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("🔄 Guardar Modificaciones en la Nube", type="primary", key=f"save_{sel_ot}"):
            hoy = date.today().strftime("%d/%m/%Y")
            if ac == "Sí" and not f_ac.strip(): f_ac = hoy
            if ret == "Sí" and not f_ret.strip(): f_ret = hoy
            bd.actualizar_orden(sel_ot, {
                "cliente": ed_cliente, "articulo": ed_articulo, "marca": ed_marca, "modelo": ed_modelo,
                "serie": ed_serie, "falla": ed_falla, "diagnostico": diag, "presupuesto": presup,
                "iva": iva_val, "total": tot_val, "aceptado": ac, "fecha_aceptado": f_ac,
                "fecha_listo": f_li, "retirado": ret, "fecha_retirado": f_ret, "medio_pago": pago, "comentarios": coment
            })
            st.success(f"✅ Orden {sel_ot} actualizada.")
            st.rerun()
    with b2:
        pdf_bytes = bd.generar_pdf_orden(row)
        st.download_button(f"🖨️ Descargar Boleta {sel_ot} en PDF", data=pdf_bytes,
            file_name=f"Orden_{sel_ot}{row['cliente']}.pdf", mime="application/pdf", key=f"pdf{sel_ot}")