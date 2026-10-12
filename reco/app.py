import cv2
import numpy as np
import streamlit as st
from datetime import datetime
import openpyxl
from io import BytesIO

# Configuración de la página web
st.set_page_config(page_title="Sistema de Inspección Estructural", page_icon="🏗️", layout="wide")

st.title("🏗️ Sistema Inteligente de Detección y Análisis de Grietas")
st.markdown("Utiliza la cámara de tu dispositivo para capturar la superficie, realizar el análisis métrico, visualizar el dashboard analítico y exportar el reporte técnico en Excel.")

st.markdown("---")

# Sección de Captura con Cámara
st.subheader("📷 Captura de Imagen en Vivo")
foto_capturada = st.camera_input("Apunta con la cámara de tu laptop, tablet o celular a la superficie y toma la foto")

if foto_capturada is not None:
    # Convertir bytes de la cámara a matriz de OpenCV
    bytes_data = foto_capturada.getvalue()
    nparr = np.frombuffer(bytes_data, np.uint8)
    imagen = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if imagen is not None:
        # Procesamiento de Visión Artificial con OpenCV
        gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gris, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)
        
        kernel = np.ones((2, 2), np.uint8)
        dilatado = cv2.dilate(thresh, kernel, iterations=1)

        contornos, _ = cv2.findContours(dilatado, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        conteo = 0
        alto_riesgo = 0
        estables = 0
        registros = []
        resultado = imagen.copy()

        for cnt in contornos:
            area = cv2.contourArea(cnt)
            # Filtrar ruido pequeño
            if area > 150:
                conteo += 1
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Conversión de píxeles a medidas estimadas en centímetros
                ancho_cm = w * 0.04
                largo_cm = h * 0.04

                # Lógica de severidad y alertas por colores
                if largo_cm > 3.0:
                    severidad = "ALTO RIESGO"
                    color = (0, 0, 255) # Rojo en BGR
                    alto_riesgo += 1
                else:
                    severidad = "Estable / Leve"
                    color = (0, 165, 255) # Naranja en BGR
                    estables += 1

                # Delinear la grieta y colocar recuadro con dimensiones
                cv2.rectangle(resultado, (x, y), (x + w, y + h), color, 2)
                cv2.drawContours(resultado, [cnt], -1, (0, 255, 0), 1)
                
                # Texto directo sobre la imagen procesada
                cv2.putText(resultado, f"#{conteo} {largo_cm:.1f}cm", (x, max(20, y - 5)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                registros.append({
                    "id": conteo,
                    "ancho": round(ancho_cm, 2),
                    "largo": round(largo_cm, 2),
                    "severidad": severidad,
                    "obs": f"Fisura detectada. Ancho: {ancho_cm:.1f}cm, Largo: {largo_cm:.1f}cm. Condición: {severidad}."
                })

        # Convertir imagen procesada de BGR a RGB para mostrar en Streamlit
        imagen_rgb = cv2.cvtColor(resultado, cv2.COLOR_BGR2RGB)

        st.markdown("---")
        
        # Análisis Rápido / Resumen Ejecutivo
        st.subheader("⚡ Análisis Rápido y Diagnóstico Preliminar")
        if conteo > 0:
            if alto_riesgo > 0:
                st.error(f"🚨 **Alerta Crítica:** Se detectaron {alto_riesgo} zonas de alto riesgo estructural que requieren atención inmediata.")
            else:
                st.success(f"✅ **Estructura Estable:** Las {conteo} fisuras detectadas se encuentran dentro de parámetros estables o superficiales.")
        else:
            st.info("No se han detectado anomalías dimensionales evidentes en esta captura.")

        st.markdown("---")

        # Layout del Dashboard en la Web
        col_img, col_dash = st.columns([1, 1])

        with col_img:
            st.subheader("🖼️ Imagen Analizada y Delineada")
            st.image(imagen_rgb, channels="RGB", use_column_width=True)

        with col_dash:
            st.subheader("📊 Dashboard Analítico de Daños")
            
            # Tarjetas de Métricas (KPIs)
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Grietas", conteo)
            m2.metric("Alto Riesgo", alto_riesgo)
            m3.metric("Estables", estables)

            if conteo > 0:
                st.markdown("**Distribución Porcentual de Severidad**")
                pct_alto = float(alto_riesgo / conteo) if conteo > 0 else 0.0
                pct_estables = float(estables / conteo) if conteo > 0 else 0.0
                
                st.markdown(f"🔴 **Alto Riesgo:** {alto_riesgo} de {conteo}")
                st.progress(pct_alto)
                
                st.markdown(f"🟠 **Estables / Leves:** {estables} de {conteo}")
                st.progress(pct_estables)

        # Tabla de Detalles y Botón de Excel
        if registros:
            st.markdown("---")
            st.subheader("📋 Registro Detallado de Observaciones")
            
            for r in registros:
                st.markdown(f"- **Grieta #{r['id']}** | Severidad: **{r['severidad']}** | Ancho: {r['ancho']} cm | Largo: {r['largo']} cm -> _{r['obs']}_")

            # Generar Excel en memoria con openpyxl (100% nativo, sin dependencias conflictivas)
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Reporte_Grietas"

            # Encabezados
            ws.append(["Grieta ID", "Ancho (cm)", "Largo (cm)", "Severidad", "Observaciones Técnicas"])
            
            # Filas de datos
            for r in registros:
                ws.append([r["id"], r["ancho"], r["largo"], r["severidad"], r["obs"]])

            output = BytesIO()
            wb.save(output)
            excel_bytes = output.getvalue()

            st.markdown("---")
            st.download_button(
                label="📥 Descargar Reporte Ejecutivo en Excel",
                data=excel_bytes,
                file_name=f"reporte_grietas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )