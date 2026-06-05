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
# 4. INTERFAZ CON AURORA BACKGROUND (ACETERNITY STYLE EN CSS PURO)
# ==============================================================================
def main():
    # 🎨 INYECCIÓN DE CSS PARA AURORA BACKGROUND + ANIMACIONES DE ENTRADA
    st.markdown("""
    <style>
        /* Fondo base oscuro */
        .main .block-container {
            background-color: #050505;
            position: relative;
            z-index: 1;
        }
        
        /* Contenedor de la Aurora */
        .aurora-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 0;
            background: #050505;
            overflow: hidden;
            pointer-events: none;
        }
        
        /* Manchas de luz difuminadas (Aurora Blobs) */
        .aurora-blob {
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            opacity: 0.5;
            mix-blend-mode: screen;
            animation: float 15s infinite ease-in-out alternate;
        }
        
        .blob-1 { 
            top: -10%; left: -10%; width: 60vw; height: 60vw; 
            background: radial-gradient(circle, #4f46e5 0%, transparent 70%); 
            animation-delay: 0s; 
        }
        .blob-2 { 
            bottom: -10%; right: -10%; width: 70vw; height: 70vw; 
            background: radial-gradient(circle, #06b6d4 0%, transparent 70%); 
            animation-delay: -5s; 
        }
        .blob-3 { 
            top: 30%; left: 30%; width: 50vw; height: 50vw; 
            background: radial-gradient(circle, #ec4899 0%, transparent 70%); 
            animation-delay: -10s; 
        }

        @keyframes float {
            0% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(40px, 60px) scale(1.15); }
            100% { transform: translate(-30px, -40px) scale(0.9); }
        }

        /* Animación de entrada suave (imitando Framer Motion) */
        .fade-in-up {
            animation: fadeInUp 0.8s ease-out forwards;
            opacity: 0;
            transform: translateY(30px);
        }
        
        .fade-in-up-delay-1 { animation-delay: 0.1s; }
        .fade-in-up-delay-2 { animation-delay: 0.3s; }
        .fade-in-up-delay-3 { animation-delay: 0.5s; }

        @keyframes fadeInUp {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Texto con degradado */
        .gradient-text {
            background: linear-gradient(to bottom, #ffffff 0%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            color: transparent;
            font-weight: 800;
            letter-spacing: -0.02em;
            line-height: 1.1;
        }

        .subtitle-text {
            color: #cbd5e1 !important;
            font-size: 1.1rem;
            font-weight: 300;
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.6;
        }

        /* Forzar color de texto claro en TODA la app para máxima legibilidad */
        .main p, .main h1, .main h2, .main h3, .main h4, .main label, .main span, .main div, .main a {
            color: #e2e8f0 !important;
        }
        
        /* Sidebar oscura y elegante */
        section[data-testid="stSidebar"] {
            background-color: #0a0a0a !important;
            border-right: 1px solid #1e293b;
        }
        section[data-testid="stSidebar"] * {
            color: #e2e8f0 !important;
        }

        /* Glassmorphism para contenedores de archivos y alertas */
        .stFileUploader > div, .stAlert {
            background: rgba(15, 23, 42, 0.4) !important;
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
        }

        /* Botón principal estilo "Debug now" pero corporativo */
        .stButton>button {
            background: #ffffff !important;
            color: #050505 !important;
            font-weight: 600;
            border: none;
            border-radius: 9999px; /* rounded-full */
            padding: 0.75rem 2rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(255, 255, 255, 0.1);
        }
        .stButton>button:hover {
            background: #e2e8f0 !important;
            box-shadow: 0 10px 15px -3px rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        /* Inputs y Text Areas */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: rgba(15, 23, 42, 0.6) !important;
            color: #f8fafc !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
        }
        
        /* Ocultar elementos por defecto */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none;}
    </style>
    
    <!-- Contenedor del Aurora Background -->
    <div class="aurora-container">
        <div class="aurora-blob blob-1"></div>
        <div class="aurora-blob blob-2"></div>
        <div class="aurora-blob blob-3"></div>
    </div>
    """, unsafe_allow_html=True)

    # 🌟 HERO SECTION CON ANIMACIÓN DE ENTRADA (Fade In Up)
    st.markdown("""
    <div class="fade-in-up" style="text-align: center; padding: 3rem 1rem 2rem 1rem; position: relative; z-index: 2;">
        <h1 class="gradient-text" style="font-size: 3rem; margin-bottom: 1rem;">
            Orquestador Estratégico <br /> Multiagente PRO
        </h1>
        <p class="subtitle-text fade-in-up fade-in-up-delay-1">
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

    st.markdown('<div class="fade-in-up fade-in-up-delay-2" style="position: relative; z-index: 2; padding: 0 1rem;">', unsafe_allow_html=True)
    
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
