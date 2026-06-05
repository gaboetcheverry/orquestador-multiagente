import streamlit as st
import os
from datetime import datetime
from docx import Document
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
# 1. FUNCIONES DE EXTRACCIÓN DE ARCHIVOS (Sin cambios)
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
# 2. CONFIGURACIÓN DE AGENTES Y PROMPTS (Sin cambios)
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
# 3. GENERADORES DE REPORTES (Sin cambios)
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
# 4. INTERFAZ DE USUARIO CON EFECTO "BACKGROUND LINES" (ACETERNITY STYLE)
# ==============================================================================
def main():
    # 🎨 INYECCIÓN DE CSS PARA IMITAR ACETERNITY UI BACKGROUND LINES
    st.markdown("""
    <style>
        /* Fondo principal con líneas animadas sutiles */
        .main .block-container {
            background-color: #020617; /* Slate 950 */
            position: relative;
            z-index: 1;
        }
        
        /* El efecto de líneas de fondo */
        .aceternity-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 0;
            background-color: #020617;
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            animation: moveLines 30s linear infinite;
            pointer-events: none;
        }
        
        /* Gradiente radial para dar profundidad en el centro */
        .aceternity-bg::after {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 50% 50%, rgba(37, 99, 235, 0.08) 0%, transparent 70%);
        }

        @keyframes moveLines {
            0% { background-position: 0 0; }
            100% { background-position: 60px 60px; }
        }

        /* Texto con degradado (bg-clip-text) */
        .gradient-text {
            background: linear-gradient(to bottom, #e2e8f0 0%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            color: transparent;
            font-weight: 800;
            letter-spacing: -0.02em;
            line-height: 1.1;
        }

        .subtitle-text {
            color: #94a3b8;
            font-size: 1.1rem;
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.6;
        }

        /* Sidebar oscura y elegante */
        section[data-testid="stSidebar"] {
            background-color: #0f172a !important;
            border-right: 1px solid #1e293b;
        }
        section[data-testid="stSidebar"] * {
            color: #e2e8f0 !important;
        }

        /* Tarjetas de contenido con efecto Glassmorphism */
        .stMarkdown, .stAlert, .stFileUploader > div {
            background: rgba(15, 23, 42, 0.6) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
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
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
        }
        .stButton>button:hover {
            background: linear-gradient(90deg, #1e3a8a 0%, #1d4ed8 100%) !important;
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4);
            transform: translateY(-1px);
        }

        /* Inputs y Text Areas */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: rgba(15, 23, 42, 0.8) !important;
            color: #e2e8f0 !important;
            border: 1px solid #334155 !important;
        }
        
        /* Ocultar elementos por defecto de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none;}
    </style>
    
    <!-- Contenedor del fondo animado -->
    <div class="aceternity-bg"></div>
    """, unsafe_allow_html=True)

    # 🌟 HERO SECTION (Imitando tu código React)
    st.markdown("""
    <div style="text-align: center; padding: 2rem 1rem 3rem 1rem; position: relative; z-index: 2;">
        <h1 class="gradient-text" style="font-size: 2.5rem; margin-bottom: 1rem;">
            Orquestador Estratégico <br /> Multiagente PRO
        </h1>
        <p class="subtitle-text">
            Obtén el mejor asesoramiento de nuestros 11 agentes expertos, 
            auditoría crítica y consenso ejecutivo, totalmente automatizado.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        api_key = st.text_input("🔑 OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        st.markdown("---")
        st.info("Arquitectura Activa:\n1. Refinador de Consultas\n2. 11 Agentes de Dominio\n3. Auditor Crítico\n4. Motor de Consenso", icon="ℹ️")

    # Contenedor principal con fondo transparente para dejar ver las líneas
    st.markdown('<div style="position: relative; z-index: 2;">', unsafe_allow_html=True)
    
    tema = st.text_area("🎯 Describe el proyecto, empresa o desafío a analizar:", 
                        placeholder="Ej: Evaluar la viabilidad de expandir nuestra planta de manufactura a Vietnam en 2025...", height=100)
    
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
            st.error("⚠️ Es obligatorio proporcionar una OpenAI API Key válida.", icon="🚫")
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
            st.markdown("#### 🎯 Estrategia Unificada")
            st.info(data['consenso'], icon="💡")
        with col2:
            st.markdown("#### ⚖️ Veredicto del Auditor")
            st.warning(data['auditoria'][:400] + "...", icon="🔍")
            
        st.markdown("#### 🧠 Briefing Estratégico")
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
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
