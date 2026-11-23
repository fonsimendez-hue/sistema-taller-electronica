import gspread
import pandas as pd
import io
import openpyxl
from fpdf import FPDF
import unicodedata
import streamlit as st
import os

ENCABEZADOS_HOJA = [
    "fecha", "orden_trabajo", "cliente", "articulo", "marca", "modelo", "serie",
    "falla", "diagnostico", "presupuesto", "iva", "total", "plazo_garantia",
    "aceptado", "fecha_aceptado", "fecha_listo", "retirado", "fecha_retirado",
    "medio_pago", "comentarios", "es_garantia", "fecha_ingreso_garantia",
    "falla_garantia", "procedimiento_garantia", "fecha_listo_garantia", "fecha_retiro_garantia"
]

@st.cache_resource
def obtener_hoja():
    if os.path.exists("credenciales.json"):
        cliente = gspread.service_account(filename="credenciales.json")
    else:
        cliente = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
        
    hoja = cliente.open("Base_Datos_Taller").sheet1
    if not hoja.row_values(1):
        hoja.append_row(ENCABEZADOS_HOJA)
    return hoja

@st.cache_data(ttl=60)
def leer_ordenes():
    hoja = obtener_hoja()
    datos = hoja.get_all_records()
    if not datos:
        return pd.DataFrame(columns=ENCABEZADOS_HOJA)
    df = pd.DataFrame(datos)
    for col in ["presupuesto", "iva", "total"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df

def agregar_orden(fila_lista):
    hoja = obtener_hoja()
    hoja.append_row(fila_lista)
    st.cache_data.clear()

def actualizar_orden(orden_trabajo, datos_dict):
    hoja = obtener_hoja()
    celda = hoja.find(orden_trabajo, in_column=2)
    if celda:
        fila_num = celda.row
        fila_actual = hoja.row_values(fila_num)
        while len(fila_actual) < len(ENCABEZADOS_HOJA):
            fila_actual.append("")
        for clave, valor in datos_dict.items():
            if clave in ENCABEZADOS_HOJA:
                idx = ENCABEZADOS_HOJA.index(clave)
                fila_actual[idx] = valor
        hoja.update(f"A{fila_num}:Z{fila_num}", [fila_actual])
        st.cache_data.clear()

def generar_excel(df_all):
    wb = openpyxl.Workbook()
    hoja = wb.active
    hoja.title = "Control_Taller"
    
    encabezados = [
        "A - Fecha", "B - Orden Trabajo", "Cliente", "C - Artículo", "D - Marca",
        "E - Modelo", "F - Serie", "G - Falla", "H - Diagnóstico",
        "I - Presupuesto (₡)", "J - IVA 13% (₡)", "K - Total Reparación (₡)",
        "L - Plazo Garantía", "M - Aceptado", "N - Fecha Aceptado", "O - Fecha Listo",
        "P - Retirado", "Q - Fecha Retirado", "R - Medio de Pago", "S - Comentarios",
        "T - Reservado", "U - Reservado", "V - Ingreso Garantía", "W - Fecha Ingreso Gar.",
        "X - Falla Garantía", "Y - Procedimiento Gar.", "Z - Fecha Listo Gar.", "AA - Fecha Retiro Gar."
    ]
    hoja.append(encabezados)
    
    for _, r in df_all.iterrows():
        fila_datos = [
            r["fecha"], r["orden_trabajo"], r["cliente"], r["articulo"], r["marca"],
            r["modelo"], r["serie"], r["falla"], r["diagnostico"],
            float(r["presupuesto"] or 0), float(r["iva"] or 0), float(r["total"] or 0),
            r["plazo_garantia"], r["aceptado"], r["fecha_aceptado"], r["fecha_listo"],
            r["retirado"], r["fecha_retirado"], r["medio_pago"], r["comentarios"],
            "", "", r["es_garantia"], r["fecha_ingreso_garantia"],
            r["falla_garantia"], r["procedimiento_garantia"], r["fecha_listo_garantia"], r["fecha_retiro_garantia"]
        ]
        hoja.append(fila_datos)
        
    for fila in hoja.iter_rows(min_row=2, min_col=10, max_col=12):
        for celda in fila:
            celda.number_format = '"₡"#,##0.00'
            
    for idx, col in enumerate(hoja.columns, start=1):
        letra = openpyxl.utils.get_column_letter(idx)
        largo_max = max(len(str(c.value or "")) for c in col)
        hoja.column_dimensions[letra].width = min(largo_max + 5, 45)
        
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

def limpiar_txt(texto):
    s = str(texto or "")
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')

def generar_pdf_orden(row):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    ancho = pdf.epw
    
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(ancho, 10, "COMPROBANTE DE ORDEN DE TRABAJO", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(ancho, 6, "Taller Especializado en Electronica", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    pdf.set_fill_color(230, 235, 240)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(ancho / 2, 9, f"Orden N: {limpiar_txt(row['orden_trabajo'])}", border=1, fill=True)
    pdf.cell(ancho / 2, 9, f"Fecha Ingreso: {limpiar_txt(row['fecha'])}", border=1, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(ancho, 8, "1. DATOS DEL CLIENTE Y EQUIPO", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(ancho, 7, f"Cliente: {limpiar_txt(row['cliente'])}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(ancho / 2, 7, f"Articulo: {limpiar_txt(row['articulo'])}", border=1)
    pdf.cell(ancho / 2, 7, f"Marca: {limpiar_txt(row['marca'])}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(ancho / 2, 7, f"Modelo: {limpiar_txt(row['modelo'])}", border=1)
    pdf.cell(ancho / 2, 7, f"Serie: {limpiar_txt(row['serie'])}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(ancho, 8, "2. FALLA REPORTADA Y DIAGNOSTICO TECNICO", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(ancho, 7, f"Falla: {limpiar_txt(row['falla'])}", border=1, new_x="LMARGIN", new_y="NEXT")
    diag_txt = limpiar_txt(row['diagnostico']) if row['diagnostico'] else "En proceso de revision"
    pdf.multi_cell(ancho, 7, f"Diagnostico: {diag_txt}", border=1, new_x="LMARGIN", new_y="NEXT")
    if row["comentarios"]:
        pdf.multi_cell(ancho, 7, f"Observaciones: {limpiar_txt(row['comentarios'])}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(ancho, 8, "3. DETALLE DE PRESUPUESTO Y GARANTIA", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(ancho / 3, 8, f"Presupuesto: CRC {float(row['presupuesto'] or 0):,.2f}", border=1)
    pdf.cell(ancho / 3, 8, f"IVA (13%): CRC {float(row['iva'] or 0):,.2f}", border=1)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(ancho / 3, 8, f"TOTAL: CRC {float(row['total'] or 0):,.2f}", border=1, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(ancho / 2, 7, f"Estado Aceptacion: {limpiar_txt(row['aceptado'])}", border=1)
    pdf.cell(ancho / 2, 7, f"Plazo Garantia: {limpiar_txt(row['plazo_garantia'])}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(ancho / 2, 7, f"Estado Retiro: {limpiar_txt(row['retirado'])} ({limpiar_txt(row['fecha_retirado'])})", border=1)
    pdf.cell(ancho / 2, 7, f"Medio de Pago: {limpiar_txt(row['medio_pago'])}", border=1, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(15)
    pdf.cell(ancho / 2, 6, "___________", align="C")
    pdf.cell(ancho / 2, 6, "___________", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(ancho / 2, 6, "Firma del Cliente", align="C")
    pdf.cell(ancho / 2, 6, "Firma Autorizada Taller", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(ancho, 4, "Nota: La garantia cubre unicamente la reparacion realizada dentro del plazo indicado, siempre que los sellos de seguridad no hayan sido violados. Pasados 30 dias de notificado como listo, el taller no se hace responsable por equipos no retirados.", new_x="LMARGIN", new_y="NEXT")
    
    return bytes(pdf.output())