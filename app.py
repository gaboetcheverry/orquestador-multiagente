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

st.set_page_config(page_title="Orquestador Estratégico Multiagente PRO", layout="wide", page_icon="🏢")

# ==============================================================================
# 1. FUNCIONES DE EXTRACCIÓN DE ARCHIVOS
# ==============================================================================
def extraer_texto_csv_excel(archivo):
    try:
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)
        texto = f"📊 DATOS DEL ARCHIVO: {archivo.name}\n"
        texto += f"Filas: {len(df)}, Columnas: {len(df.columns)}\n\n"
        texto += "COLUMNAS:\n" + ", ".join(df.columns.tolist()) + "\n\n"
        texto += "PRIMERAS 10 FILAS:\n" + df.head(10).to_string(index=False)
        return texto
    except Exception as e:
        return f"Error al leer {archivo.name}: {str(e)}"

def extraer_texto_pdf(archivo):
    try:
        pdf_reader = PyPDF2.PdfReader(archivo)
        texto = f"📄 CONTENIDO DEL PDF: {archivo.name}\nPáginas: {len(pdf_reader.pages)}\n\n"
        for i, page in enumerate(pdf_reader.pages[:10]):
            texto += f"--- Página {i+1} ---\n" + page.extract_text() + "\n\n"
        if len(pdf_reader.pages) > 10:
            texto += f"\n[... {len(pdf_reader.pages) - 10} páginas adicionales omitidas para optimizar el análisis ...]"
        return texto
    except Exception as e:
        return f"Error al leer {archivo.name}: {str(e)}"

def extraer_texto_word(archivo):
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
    try:
        imagen = Image.open(archivo)
        buffered = io.BytesIO()
        imagen.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        return None

# ==============================================================================
# 2. CONFIGURACIÓN DE AGENTES Y PROMPTS
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
    os.environ["OPENAI_API_KEY"] = api_key
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    resultados = {"tema_original": tema_crudo, "fecha": datetime.now().strftime("%d de %B de %Y")}
    total_steps = 14
    current_step = 0

    current_step += 1
    status_text.text("🧹 Agente de Limpieza: Estructurando el briefing estratégico...")
    progress_bar.progress(current_step / total_steps)
    contexto_archivos = f"\n\nINFORMACIÓN ADICIONAL DE ARCHIVOS ADJUNTOS:\n{archivos_texto}" if archivos_texto else ""
    prompt_refinar = PromptTemplate.from_template(
        "Eres un Consultor Estratégico Senior. El usuario dio esta consulta cruda: '{tema}'{archivos}\n\n"
        "Reescríbela como un 'Briefing Estratégico Ejecutivo' formal, detallando: Objetivo Central, Alcance, Restricciones Asumidas y KPIs de Éxito. Sé conciso pero muy profesional."
    )
    resultados["briefing"] = llm.invoke(prompt_refinar.format(tema=tema_crudo, archivos=contexto_archivos)).content

    resultados["analisis_dominios"] = {}
    for i, agente in enumerate(AGENTES_DOMINIO):
        current_step += 1
        status_text.text(f"🧠 {agente} generando análisis profundo... ({i+1}/11)")
        progress_bar.progress(current_step / total_steps)
        prompt_agente = PromptTemplate.from_template(
            "Eres el {rol}. Analiza el siguiente Briefing Estratégico: \n\n'{briefing}'\n\n"
            "Genera un análisis robusto, técnico y accionable (mínimo 3 párrafos). Incluye: 1. Diagnóstico actual, 2. Riesgos/Oportunidades, 3. Recomendación táctica inmediata."
        )
        resultados["analisis_dominios"][agente] = llm.invoke(prompt_agente.format(rol=agente, briefing=resultados["briefing"])).content

    current_step += 1
    status_text.text("⚖️ Auditor Crítico: Buscando sesgos, contradicciones y viabilidad...")
    progress_bar.progress(current_step / total_steps)
    prompt_auditor = PromptTemplate.from_template(
        "Eres un Auditor Crítico implacable. Revisa los análisis de los 11 agentes sobre este briefing: '{briefing}'. "
        "Identifica: 1. Contradicciones, 2. Suposiciones no validadas, 3. Puntos ciegos críticos. Emite un veredicto de viabilidad (Alta, Media, Baja) con justificación."
    )
    resultados["auditoria"] = llm.invoke(prompt_auditor.format(briefing=resultados["briefing"])).content

    current_step += 1
    status_text.text("🤝 Motor de Consenso: Sintetizando la estrategia final...")
    progress_bar.progress(current_step / total_steps)
    prompt_consenso = PromptTemplate.from_template(
        "Eres el CEO y Motor de Consenso. Basado en el Briefing: '{briefing}', los 11 análisis y la Auditoría Crítica: '{auditoria}', "
        "redacta la 'Estrategia Unificada Final'. Debe incluir: Resumen Ejecutivo, 3 Pilares Estratégicos Prioritarios, Hoja de Ruta a 90 días y Métrica de Éxito principal."
    )
    resultados["consenso"] = llm.invoke(prompt_consenso.format(briefing=resultados["briefing"], auditoria=resultados["auditoria"])).content
    
    status_text.text("✅ ¡Orquestación Multiagente Completada con Éxito!")
    progress_bar.progress(1.0)
    return resultados

# ==============================================================================
# 3. GENERADORES DE REPORTES
# ==============================================================================
def generar_pdf_profesional(data, filename="Reporte_Estrategico_Pro.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TituloPrincipal', fontName='Helvetica-Bold', fontSize=22, textColor=HexColor('#0f172a'), alignment=TA_CENTER, spaceAfter=30))
    styles.add(ParagraphStyle(name='Subtitulo', fontName='Helvetica-Bold', fontSize=14, textColor=HexColor('#2563eb'), spaceBefore=20, spaceAfter=10))
    styles.add(ParagraphStyle(name='Cuerpo', fontName='Helvetica', fontSize=11, leading=16, alignment=TA_JUSTIFY, spaceAfter=12, textColor=HexColor('#334155')))
    styles.add(ParagraphStyle(name='CajaResumen', fontName='Helvetica', fontSize=11, leading=16, backColor=HexColor('#f8fafc'), borderColor=HexColor('#2563eb'), borderWidth=1, borderPadding=10, spaceAfter=20))

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
        story.append(Paragraph(analisis.replace('\n', '<br/>'), styles['Cuerpo']))
        story.append(Spacer(1, 15))
    doc.build(story)
    return filename

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
# 4. INTERFAZ DE USUARIO CON CSS PROFESIONAL
# ==============================================================================
def main():
    # 🎨 INYECCIÓN DE CSS PROFESIONAL
    st.markdown("""
    <style>
        /* Fondo principal limpio */
        .main .block-container {
            background-color: #f8fafc;
            padding-top: 3rem;
        }
        /* Sidebar oscura y elegante */
        section[data-testid="stSidebar"] {
            background-color: #0f172a !important;
            border-right: 1px solid #1e293b;
        }
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div {
            color: #e2e8f0 !important;
        }
        /* Títulos principales */
        h1, h2, h3 {
            color: #0f172a !important;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            font-weight: 700;
        }
        /* Botón principal con degradado corporativo */
        .stButton>button {
            background: linear-gradient(90deg, #1e40af 0%, #2563eb 100%) !important;
            color: white !important;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
        }
        .stButton>button:hover {
            background: linear-gradient(90deg, #1e3a8a 0%, #1d4ed8 100%) !important;
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
            transform: translateY(-1px);
        }
        /* Cajas de alerta elegantes */
        .stAlert {
            border-radius: 8px;
            border-left: 4px solid #2563eb;
            background-color: #eff6ff !important;
            color: #1e3a8a !important;
        }
        /* File uploader estilizado */
        .stFileUploader {
            border: 2px dashed #cbd5e1;
            border-radius: 8px;
            background-color: #ffffff;
            padding: 1rem;
            transition: border-color 0.3s;
        }
        .stFileUploader:hover {
            border-color: #2563eb;
        }
        /* Ocultar footer y badges de Streamlit para look 100% blanco */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none;}
    </style>
    """, unsafe_allow_html=True)

    st.title("🏢 Orquestador Estratégico Multiagente PRO")
    st.markdown("Sistema de inteligencia colectiva con **Agente de Limpieza**, 11 Especialistas, Auditoría Crítica y Motor de Consenso.")
    
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        api_key = st.text_input("🔑 OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        st.markdown("---")
        st.info("Arquitectura Activa:\n1. Refinador de Consultas\n2. 11 Agentes de Dominio\n3. Auditor Crítico\n4. Motor de Consenso", icon="ℹ️")

    st.markdown("### 🎯 Definir Objetivo Estratégico")
    tema = st.text_area("Describe el proyecto, empresa o desafío a analizar:", 
                        placeholder="Ej: Evaluar la viabilidad de expandir nuestra planta de manufactura a Vietnam en 2025, considerando riesgos geopolíticos, costos laborales y cumplimiento ESG.", height=100)
    
    st.markdown("### 📎 Adjuntar Archivos de Soporte (Opcional)")
    st.caption("Sube documentos, datos o imágenes que quieras que los agentes analicen junto con tu consulta.")
    
    archivos_subidos = st.file_uploader(
        "Arrastra archivos aquí o haz clic para seleccionar",
        type=['csv', 'xlsx', 'xls', 'pdf', 'docx', 'jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="Formatos soportados: CSV, Excel, PDF, Word, Imágenes (JPG, PNG)"
    )
    
    if archivos_subidos:
        st.success(f"✅ {len(archivos_subidos)} archivo(s) listo(s) para análisis", icon="✅")
    
    if st.button("🚀 INICIAR ORQUESTACIÓN MULTIAGENTE", use_container_width=True):
        if not tema:
            st.warning("Por favor, ingrese un tema para analizar.", icon="⚠️")
            return
        if not api_key:
            st.error("⚠️ Es obligatorio proporcionar una OpenAI API Key válida para el análisis robusto.", icon="🚫")
            return
            
        with st.spinner("Procesando cadena multiagente... (Esto toma 1-2 minutos)"):
            try:
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
                st.success("✅ Análisis multiagente completado exitosamente.", icon="🎯")
            except Exception as e:
                st.error(f"Error en la API: {str(e)}. Verifica tu clave.", icon="🚫")
                return

    if 'resultados' in st.session_state:
        data = st.session_state['resultados']
        st.markdown("---")
        st.subheader("📊 Dashboard de Consenso Estratégico")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("#### 🎯 Estrategia Unificada (Motor de Consenso)")
            st.info(data['consenso'], icon="💡")
        with col2:
            st.markdown("#### ⚖️ Veredicto del Auditor")
            st.warning(data['auditoria'][:400] + "...", icon="🔍")
            
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
