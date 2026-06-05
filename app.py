import streamlit as st
import os
from datetime import datetime
from docx import Document
import plotly.express as px
import pandas as pd
import PyPDF2
import base64
from PIL import Image
import io

# Importaciones para PDF Profesional
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor

# Importaciones para LLM Robusto
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

st.set_page_config(page_title="Orquestador Estratégico Multiagente PRO", layout="wide")

# ==============================================================================
# 1. FUNCIONES DE EXTRACCIÓN DE ARCHIVOS
# ==============================================================================
def extraer_texto_csv_excel(archivo):
    """Extrae datos de CSV o Excel y los convierte en texto estructurado."""
    try:
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:  # Excel
            df = pd.read_excel(archivo)
        
        texto = f"📊 DATOS DEL ARCHIVO: {archivo.name}\n"
        texto += f"Filas: {len(df)}, Columnas: {len(df.columns)}\n\n"
        texto += "COLUMNAS:\n" + ", ".join(df.columns.tolist()) + "\n\n"
        texto += "PRIMERAS 10 FILAS:\n"
        texto += df.head(10).to_string(index=False)
        return texto
    except Exception as e:
        return f"Error al leer {archivo.name}: {str(e)}"

def extraer_texto_pdf(archivo):
    """Extrae texto de un archivo PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(archivo)
        texto = f"📄 CONTENIDO DEL PDF: {archivo.name}\n"
        texto += f"Páginas: {len(pdf_reader.pages)}\n\n"
        
        for i, page in enumerate(pdf_reader.pages[:10]):
            texto += f"--- Página {i+1} ---\n"
            texto += page.extract_text() + "\n\n"
        
        if len(pdf_reader.pages) > 10:
            texto += f"\n[... {len(pdf_reader.pages) - 10} páginas adicionales omitidas para optimizar el análisis ...]"
        
        return texto
    except Exception as e:
        return f"Error al leer {archivo.name}: {str(e)}"

def extraer_texto_word(archivo):
    """Extrae texto de un archivo Word."""
    try:
        doc = Document(archivo)
        texto = f"📝 CONTENIDO DEL WORD: {archivo.name}\n\n"
        
        for para in doc.paragraphs:
            if para.text.strip():
                texto += para.text + "\n"
        
        return texto
    except Exception as e:
        return f"Error al leer {archivo.name}: {str(e)}"

def procesar_imagen(archivo):
    """Convierte imagen a base64 para análisis multimodal."""
    try:
        imagen = Image.open(archivo)
        buffered = io.BytesIO()
        imagen.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return img_base64
    except Exception as e:
        return None

# ==============================================================================
# 2. CONFIGURACIÓN DE AGENTES Y PROMPTS ROBUSTOS
# ==============================================================================
AGENTES_DOMINIO = [
    "Agente Financiero (ROI, CAPEX, OPEX, Flujo de Caja)",
    "Agente Macroeconómico (Inflación, Tasas, Geopolítica)",
    "Agente de Riesgos (Mitigación, Escenarios, Probabilidades)",
    "Agente de Sistemas (Infraestructura, Ciberseguridad, Legacy)",
    "Agente de Talento (Cultura, Retención, Upskilling)",
    "Agente ESG (Sostenibilidad, Gobernanza, Impacto Social)",
    "Agente de Mercado (Competencia, Cuota, Tendencias de Consumo)",
    "Agente Digital (Transformación, Automatización, Data)",
    "Agente de Innovación (I+D, Nuevos Modelos de Negocio)",
    "Agente de Prospectiva (Escenarios a 5 y 10 años)",
    "Agente Probabilístico (Análisis Bayesiano, Montecarlo)"
]

def ejecutar_cadena_multiagente(tema_crudo: str, api_key: str, archivos_texto: str, imagen_base64: str = None):
    """Ejecuta la orquestación real usando LLM para cada etapa."""
    os.environ["OPENAI_API_KEY"] = api_key
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    
    resultados = {"tema_original": tema_crudo, "fecha": datetime.now().strftime("%d de %B de %Y")}
    
    total_steps = 14
    current_step = 0

    # PASO 1: Agente de Limpieza y Refinamiento
    current_step += 1
    status_text.text("🧹 Agente de Limpieza: Estructurando el briefing estratégico...")
    progress_bar.progress(current_step / total_steps)
    
    contexto_archivos = f"\n\nINFORMACIÓN ADICIONAL DE ARCHIVOS ADJUNTOS:\n{archivos_texto}" if archivos_texto else ""
    
    prompt_refinar = PromptTemplate.from_template(
        "Eres un Consultor Estratégico Senior. El usuario dio esta consulta cruda: '{tema}'{archivos}\n\n"
        "Reescríbela como un 'Briefing Estratégico Ejecutivo' formal, detallando: Objetivo Central, Alcance, Restricciones Asumidas y KPIs de Éxito. "
        "Si hay datos de archivos, incorpóralos de manera relevante. Sé conciso pero muy profesional."
    )
    briefing = llm.invoke(prompt_refinar.format(tema=tema_crudo, archivos=contexto_archivos)).content
    resultados["briefing"] = briefing

    # PASO 2: Análisis de los 11 Agentes Especializados
    resultados["analisis_dominios"] = {}
    for i, agente in enumerate(AGENTES_DOMINIO):
        current_step += 1
        status_text.text(f"🧠 {agente} generando análisis profundo... ({i+1}/11)")
        progress_bar.progress(current_step / total_steps)
        
        prompt_agente = PromptTemplate.from_template(
            "Eres el {rol}. Analiza el siguiente Briefing Estratégico: \n\n'{briefing}'\n\n"
            "Genera un análisis robusto, técnico y accionable (mínimo 3 párrafos). Incluye: "
            "1. Diagnóstico actual, 2. Riesgos/Oportunidades específicos de tu dominio, 3. Recomendación táctica inmediata."
        )
        analisis = llm.invoke(prompt_agente.format(rol=agente, briefing=briefing)).content
        resultados["analisis_dominios"][agente] = analisis

    # PASO 3: Auditor Crítico
    current_step += 1
    status_text.text("⚖️ Auditor Crítico: Buscando sesgos, contradicciones y viabilidad...")
    progress_bar.progress(current_step / total_steps)
    
    prompt_auditor = PromptTemplate.from_template(
        "Eres un Auditor Crítico implacable. Revisa los análisis de los 11 agentes sobre este briefing: '{briefing}'. "
        "Identifica: 1. Contradicciones entre agentes (ej: Finanzas vs ESG), 2. Suposiciones no validadas, 3. Puntos ciegos críticos. "
        "Emite un veredicto de viabilidad (Alta, Media, Baja) con justificación."
    )
    auditoria = llm.invoke(prompt_auditor.format(briefing=briefing)).content
    resultados["auditoria"] = auditoria

    # PASO 4: Motor de Consenso
    current_step += 1
    status_text.text("🤝 Motor de Consenso: Sintetizando la estrategia final...")
    progress_bar.progress(current_step / total_steps)
    
    prompt_consenso = PromptTemplate.from_template(
        "Eres el CEO y Motor de Consenso. Basado en el Briefing: '{briefing}', los 11 análisis y la Auditoría Crítica: '{auditoria}', "
        "redacta la 'Estrategia Unificada Final'. Debe incluir: Resumen Ejecutivo (1 párrafo), 3 Pilares Estratégicos Prioritarios, "
        "Hoja de Ruta a 90 días y Métrica de Éxito principal. Sé directo y orientado a la acción."
    )
    consenso = llm.invoke(prompt_consenso.format(briefing=briefing, auditoria=auditoria)).content
    resultados["consenso"] = consenso
    
    status_text.text("✅ ¡Orquestación Multiagente Completada con Éxito!")
    progress_bar.progress(1.0)
    
    return resultados

# ==============================================================================
# 3. GENERADOR DE PDF PROFESIONAL (PLATYPUS)
# ==============================================================================
def generar_pdf_profesional(data, filename="Reporte_Estrategico_Pro.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(name='TituloPrincipal', fontName='Helvetica-Bold', fontSize=22, textColor=HexColor('#1f3a93'), alignment=TA_CENTER, spaceAfter=30))
    styles.add(ParagraphStyle(name='Subtitulo', fontName='Helvetica-Bold', fontSize=14, textColor=HexColor('#1f3a93'), spaceBefore=20, spaceAfter=10))
    styles.add(ParagraphStyle(name='Cuerpo', fontName='Helvetica', fontSize=11, leading=16, alignment=TA_JUSTIFY, spaceAfter=12))
    styles.add(ParagraphStyle(name='CajaResumen', fontName='Helvetica', fontSize=11, leading=16, backColor=HexColor('#f0f4f8'), borderColor=HexColor('#1f3a93'), borderWidth=1, borderPadding=10, spaceAfter=20))

    story.append(Paragraph("REPORTE ESTRATÉGICO MULTIAGENTE", styles['TituloPrincipal']))
    story.append(Paragraph(f"Tema: {data['tema_original']}", styles['Subtitulo']))
    story.append(Paragraph(f"Fecha de Emisión: {data['fecha']}", styles['Cuerpo']))
    story.append(Spacer(1, 30))

    story.append(Paragraph("1. CONSENSO ESTRATÉGICO Y HOJA DE RUTA", styles['Subtitulo']))
    story.append(Paragraph(data['consenso'].replace('\n', '<br/>'), styles['CajaResumen']))
    story.append(PageBreak())

    story.append(Paragraph("2. DICTAMEN DEL AUDITOR CRÍTICO", styles['Subtitulo']))
    story.append(Paragraph(data['auditoria'].replace('\n', '<br/>'), styles['Cuerpo']))
    story.append(Spacer(1, 20))

    story.append(PageBreak())
    story.append(Paragraph("3. ANÁLISIS DETALLADO POR DOMINIO DE EXPERTOS", styles['Subtitulo']))
    
    for agente, analisis in data['analisis_dominios'].items():
        story.append(Paragraph(agente, styles['Subtitulo']))
        texto_formateado = analisis.replace('\n', '<br/>')
        story.append(Paragraph(texto_formateado, styles['Cuerpo']))
        story.append(Spacer(1, 15))

    doc.build(story)
    return filename

# ==============================================================================
# 4. GENERADOR WORD
# ==============================================================================
def generar_word(data, filename="Reporte_Estrategico.docx"):
    doc = Document()
    doc.add_heading(f'Reporte Estratégico: {data["tema_original"]}', 0)
    doc.add_paragraph(f'Fecha: {data["fecha"]}')
    doc.add_heading('Consenso Ejecutivo', level=1)
    doc.add_paragraph(data['consenso'])
    doc.add_heading('Auditoría Crítica', level=1)
    doc.add_paragraph(data['auditoria'])
    for agente, analisis in data['analisis_dominios'].items():
        doc.add_heading(agente, level=2)
        doc.add_paragraph(analisis)
    doc.save(filename)
    return filename

# ==============================================================================
# 5. INTERFAZ DE USUARIO (STREAMLIT)
# ==============================================================================
def main():
    st.title("🏢 Orquestador Estratégico Multiagente PRO")
    st.markdown("Sistema de inteligencia colectiva con **Agente de Limpieza**, 11 Especialistas, Auditoría Crítica y Motor de Consenso.")
    
    with st.sidebar:
        st.header("⚙️ Configuración del Motor")
        api_key = st.text_input("🔑 OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        st.markdown("---")
        st.info("Arquitectura Activa:\n1. Refinador de Consultas\n2. 11 Agentes de Dominio\n3. Auditor Crítico\n4. Motor de Consenso")

    st.markdown("### 🎯 Definir Objetivo Estratégico")
    tema = st.text_area("Describe el proyecto, empresa o desafío a analizar:", 
                        placeholder="Ej: Evaluar la viabilidad de expandir nuestra planta de manufactura a Vietnam en 2025, considerando riesgos geopolíticos, costos laborales y cumplimiento ESG.", height=100)
    
    # Carga de archivos
    st.markdown("### 📎 Adjuntar Archivos de Soporte (Opcional)")
    st.caption("Sube documentos, datos o imágenes que quieras que los agentes analicen junto con tu consulta.")
    
    archivos_subidos = st.file_uploader(
        "Arrastra archivos aquí o haz clic para seleccionar",
        type=['csv', 'xlsx', 'xls', 'pdf', 'docx', 'jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="Formatos soportados: CSV, Excel, PDF, Word, Imágenes (JPG, PNG)"
    )
    
    if archivos_subidos:
        st.success(f"✅ {len(archivos_subidos)} archivo(s) listo(s) para análisis")
    
    if st.button("🚀 INICIAR ORQUESTACIÓN MULTIAGENTE", type="primary", use_container_width=True):
        if not tema:
            st.warning("Por favor, ingrese un tema para analizar.")
            return
        if not api_key:
            st.error("⚠️ Es obligatorio proporcionar una OpenAI API Key válida para el análisis robusto.")
            return
            
        with st.spinner("Procesando cadena multiagente... (Esto toma 1-2 minutos)"):
            try:
                # Procesar archivos adjuntos
                archivos_texto = ""
                imagen_base64 = None
                
                if archivos_subidos:
                    for archivo in archivos_subidos:
                        if archivo.name.endswith(('.csv', '.xlsx', '.xls')):
                            archivos_texto += extraer_texto_csv_excel(archivo) + "\n\n"
                        elif archivo.name.endswith('.pdf'):
                            archivos_texto += extraer_texto_pdf(archivo) + "\n\n"
                        elif archivo.name.endswith('.docx'):
                            archivos_texto += extraer_texto_word(archivo) + "\n\n"
                        elif archivo.name.endswith(('.jpg', '.jpeg', '.png')):
                            imagen_base64 = procesar_imagen(archivo)
                            if imagen_base64:
                                archivos_texto += f"🖼️ IMAGEN ADJUNTA: {archivo.name} (Análisis visual disponible)\n\n"
                
                resultados = ejecutar_cadena_multiagente(tema, api_key, archivos_texto, imagen_base64)
                st.session_state['resultados'] = resultados
                st.success("✅ Análisis multiagente completado exitosamente.")
            except Exception as e:
                st.error(f"Error en la API: {str(e)}. Verifica tu clave.")
                return

    if 'resultados' in st.session_state:
        data = st.session_state['resultados']
        
        st.markdown("---")
        st.subheader("📊 Dashboard de Consenso Estratégico")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("#### 🎯 Estrategia Unificada (Motor de Consenso)")
            st.info(data['consenso'])
        with col2:
            st.markdown("#### ⚖️ Veredicto del Auditor")
            st.warning(data['auditoria'][:400] + "...")
            
        st.markdown("#### 🧠 Briefing Estratégico (Generado por Agente de Limpieza)")
        st.markdown(f"*{data['briefing']}*")

        st.markdown("---")
        st.subheader("📥 Centro de Descarga de Reportes Profesionales")
        
        colA, colB = st.columns(2)
        
        pdf_file = generar_pdf_profesional(data)
        word_file = generar_word(data)
        
        with colA:
            with open(pdf_file, "rb") as f:
                st.download_button(label="📄 Descargar PDF Profesional", data=f, file_name=pdf_file, mime="application/pdf", use_container_width=True)
        with colB:
            with open(word_file, "rb") as f:
                st.download_button(label="📝 Descargar Word", data=f, file_name=word_file, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

if __name__ == "__main__":
    main()
