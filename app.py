import cv2
import numpy as np
import streamlit as st
from datetime import datetime
import openpyxl
from io import BytesIO

st.set_page_config(page_title="Sistema de Inspección Estructural", page_icon="🏗️", layout="wide")

st.title("🏗️ Sistema Inteligente de Detección y Análisis de Grietas")
st.markdown("Sistema optimizado para la detección de fisuras finas y superficiales mediante visión artificial avanzada.")

st.markdown("---")

st.subheader("📷 Captura de Imagen en Vivo")
foto_capturada = st.camera_input("Apunta con la cámara a la superficie con fisuras y toma la foto")

if foto_capturada is not None:
    bytes_data = foto_capturada.getvalue()
    nparr = np.frombuffer(bytes_data, np.uint8)
    imagen = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if imagen is not None:
        # 1. Preprocesamiento avanzado para grietas finas
        gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        
        # Reducir ruido manteniendo los bordes finos con filtro bilateral
        bilateral = cv2.bilateralFilter(gris, 9, 75, 75)
        
        # Detección de bordes con Canny adaptado para fisuras
        edges = cv2.Canny(bilateral, 30, 100)
        
        # Conectar trazos fragmentados de la grieta usando dilatación con kernel vertical/horizontal
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilatado = cv2.dilate(edges, kernel, iterations=2)

        contornos, _ = cv2.findContours(dilatado, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        conteo = 0
        alto_riesgo = 0
        estables = 0
        registros = []
        resultado = imagen.copy()

        # Obtener dimensiones de la imagen para filtrar los bordes de la cámara
        alto_img, ancho_img = imagen.shape[:2]

        for cnt in contornos:
            area = cv2.contourArea(cnt)
            x, y, w, h = cv2.boundingRect(cnt)
            
            # Filtro para ignorar los marcos laterales de la cámara y ruido minúsculo
            es_borde_camara = (x < 10 or y < 10 or (x + w) > (ancho_img - 10) or (y + h) > (alto_img - 10))
            
            if area > 40 and not es_borde_camara:
                conteo += 1
                
                # Conversión métrica estimada
                ancho_cm = max(0.1, w * 0.03)
                largo_cm = max(0.5, h * 0.03)

                # Severidad basada en longitud y apertura
                if largo_cm > 2.5 or ancho_cm > 0.4:
                    severidad = "ALTO RIESGO"
                    color = (0, 0, 255) # Rojo
                    alto_riesgo += 1
                else:
                    severidad = "Estable / Leve"
                    color = (0, 165, 255) # Naranja
                    estables += 1

                # Delinear contorno real de la grieta y caja de inspección
                cv2.drawContours(resultado, [cnt], -1, (0, 255, 0), 2)
                cv2.rectangle(resultado, (x, y), (x + w, y + h), color, 2)
                
                # Etiqueta con datos directamente sobre el hallazgo
                cv2.putText(resultado, f"#{conteo} {largo_cm:.1f}cm", (x, max(20, y - 5)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                registros.append({
                    "id": conteo,
                    "ancho": round(ancho_cm, 2),
                    "largo": round(largo_cm, 2),
                    "severidad": severidad,
                    "obs": f"Fisura detectada. Ancho: {ancho_cm:.1f}cm, Largo: {largo_cm:.1f}cm. Condición: {severidad}."
                })

        imagen_rgb = cv2.cvtColor(resultado, cv2.COLOR_BGR2RGB)

        st.markdown("---")
        st.subheader("⚡ Análisis Rápido y Diagnóstico Preliminar")
        if conteo > 0:
            if alto_riesgo > 0:
                st.error(f"🚨 **Alerta Crítica:** Se detectaron {alto_riesgo} zonas de alto riesgo estructural.")
            else:
                st.success(f"✅ **Estructura Estable:** Las {conteo} fisuras detectadas son superficiales o leves.")
        else:
            st.info("No se han detectado fisuras relevantes en esta toma. Intenta acercar un poco más la cámara.")

        st.markdown("---")

        col_img, col_dash = st.columns([1, 1])

        with col_img:
            st.subheader("🖼️ Imagen Analizada y Delineada")
            st.image(imagen_rgb, channels="RGB", use_column_width=True)

        with col_dash:
            st.subheader("📊 Dashboard Analítico de Daños")
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

        if registros:
            st.markdown("---")
            st.subheader("📋 Registro Detallado de Observaciones")
            for r in registros:
                st.markdown(f"- **Grieta #{r['id']}** | Severidad: **{r['severidad']}** | Ancho: {r['ancho']} cm | Largo: {r['largo']} cm -> _{r['obs']}_")

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Reporte_Grietas"

            ws.append(["Grieta ID", "Ancho (cm)", "Largo (cm)", "Severidad", "Observaciones Técnicas"])
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
