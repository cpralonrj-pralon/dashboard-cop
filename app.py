import datetime
import hashlib
import traceback
import io
import pandas as pd
import numpy as np
import streamlit as st
from src.auth import (
    ensure_users_initialized, show_login_page, show_change_password_page,
    save_uploaded_file, load_saved_files_to_session, saved_files_exist,
    AUTH_ADMIN_ID, reset_non_admin_passwords, reset_user_password,
    list_missing_tracked_ids,
    get_upload_timestamp,
)
from src.config import PRALON_ID as _PRALON_ID
from src.config import EVANDRO_ID as _EVANDRO_ID
from src.config import EVANDRO_ANALYSTS, EVANDRO_ANALYSTS_MAP
from src.config import name_for_login as _name_for_login
from src import storage as _storage

from src.config import (
    BASE_EQUIPE, EQUIPE_IDS, LIDERES_IDS, VOL_COLS,
    COORD_IDS, COORD_ANALYSTS_MAP, COORD_ANALYSTS_NAMES, COORD_TURNOS_MAP, PRALON_ANALYSTS,
    SUB_ADMIN_EMP_IDS,
    ALL_TRACKED_IDS,
    VOL_COLS_RESIDENCIAL, VOL_COLS_EMPRESARIAL, VOL_COLS_AMBOS,
    REGIONAL_FILTRO,
    COL_LOGIN, COL_NOME, COL_BASE, COL_DATA, COL_MES, COL_ANOMES,
    COL_VOL_TOTAL, COL_DPA_RESULTADO,
    COR_PRIMARIA, COR_SUCESSO, COR_ALERTA, COR_PERIGO, COR_INFO,
    # ETIT
    ETIT_COL_LOGIN, ETIT_COL_DEMANDA, ETIT_COL_VOLUME,
    ETIT_COL_STATUS, ETIT_COL_TIPO, ETIT_COL_CAUSA,
    ETIT_COL_REGIONAL, ETIT_COL_GRUPO, ETIT_COL_TURNO, ETIT_COL_TMA, ETIT_COL_TMR,
    ETIT_COL_DT_ACIONAMENTO, ETIT_COL_ANOMES, ETIT_COL_INDICADOR_VAL,
    ETIT_COL_NOTA, ETIT_COL_AREA, ETIT_COL_CIDADE, ETIT_COL_UF,
    # Residencial Indicadores
    RES_INDICADORES_FILTRO, RES_IND_LABELS, RES_IND_COLORS,
    RES_IND_INVERTIDOS, RES_IND_ETIT_FIBRA_HFC, RES_IND_ETIT_GPON,
    RES_IND_REPROG_GPON, RES_IND_LOG_REPROG_GPON, RES_IND_ASSERT_FIBRA_HFC, RES_IND_ASSERT_GPON,
    RES_COL_INDICADOR_NOME, RES_COL_VOLUME, RES_COL_INDICADOR_VAL as RES_COL_IND_VAL,
    RES_COL_STATUS, RES_COL_REGIONAL as RES_REGIONAL, RES_COL_GRUPO,
    RES_COL_DT_INICIO, RES_COL_TMA as RES_TMA, RES_COL_TMR as RES_TMR,
    RES_COL_SOLUCAO, RES_COL_IMPACTO, RES_COL_NATUREZA, RES_COL_SERVICO,
    RES_COL_CIDADE, RES_COL_UF as RES_UF, RES_COL_ANOMES as RES_ANOMES,
    RES_COL_ID_MOSTRA, RES_COL_LOGIN as RES_LOGIN, RES_COL_TURNO,
    # DPA Ocupação
    DPA_THRESHOLD_OK, DPA_THRESHOLD_ALERTA,
    # Indicadores TOA
    TOA_IND_CANCELADAS, TOA_IND_VALIDACAO, TOA_IND_LABELS, TOA_IND_COLORS,
    TOA_INDICADORES_FILTRO, TOA_AGING_ORDER,
    # Fechamento TOA x SIR
    FECH_SIR_COR, FECH_SIR_COL_LOGIN, FECH_SIR_COL_ANOMES, FECH_SIR_COL_VOLUME,
    FECH_SIR_COL_ASSERTIVO, FECH_SIR_COL_NAO_ASSER, FECH_SIR_COL_CAUSA_TOA,
    FECH_SIR_COL_CAUSA_SIR, FECH_SIR_COL_REGIONAL, FECH_SIR_COL_GRUPO, FECH_SIR_COL_DEMANDA,
    FECH_SIR_COL_DIA, FECH_SIR_TURNO_MADRUGADA,
    # Chat TOA
    CHAT_TOA_COR, CHAT_TOA_COL_LOGIN, CHAT_TOA_COL_ANOMES,
    CHAT_TMA_LIMITE_MIN,
)
from src.processors import (
    load_produtividade, resumo_mensal, resumo_geral,
    evolucao_diaria, composicao_volume, primeiro_nome,
    # ETIT
    load_etit, etit_resumo_analista, etit_por_demanda,
    etit_por_tipo, etit_por_causa, etit_por_regional,
    etit_por_turno, etit_evolucao_diaria,
    etit_aderencia_ral_rec_por_analista,
    # Residencial Indicadores
    load_residencial_indicadores,
    res_kpis_por_indicador, res_por_regional,
    res_por_analista, res_por_natureza, res_por_solucao, res_por_impacto,
    res_evolucao_diaria,
    # DPA Ocupação
    load_dpa_ocupacao, dpa_ranking, dpa_comparativo,
    # Indicadores TOA
    load_toa_indicadores, toa_resumo_por_indicador,
    toa_canceladas_por_analista, toa_canceladas_por_tipo,
    toa_canceladas_por_aging, toa_canceladas_por_rede, toa_canceladas_por_regional,
    toa_canceladas_evolucao,
    toa_validacao_por_analista, toa_validacao_por_tipo,
    toa_validacao_por_rede, toa_validacao_por_regional,
    toa_validacao_evolucao,
    # Fechamento TOA x SIR
    load_fechamento_toa_sir, fech_sir_resumo_analista,
    fech_sir_por_causa_toa, fech_sir_por_causa_sir,
    fech_sir_por_regional, fech_sir_por_grupo, fech_sir_por_demanda, fech_sir_por_dia,
    # Chat TOA
    load_chat_toa, chat_toa_kpis_gerais, chat_toa_por_analista,
    chat_toa_por_hora, chat_toa_por_fila, chat_toa_evolucao_diaria,
    chat_toa_por_tipo_fila,
    # Analistas externos por aba
    load_fora_equipe_fech_sir, load_fora_equipe_fech_sir_coord, fora_equipe_resumo_por_login,
    load_fora_equipe_etit, fora_equipe_resumo_etit,
    fora_equipe_resumo_res_por_indicador_adm, fora_equipe_resumo_res_por_indicador_coord,
    load_fora_equipe_toa, fora_equipe_resumo_toa_por_indicador,
    load_fora_equipe_dpa,
)

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Produtividade COP Rede",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# FUNÇÕES DE PROCESSAMENTO COM CACHE
# Evitam re-parsear os arquivos Excel a cada rerun do Streamlit.
# O cache é invalidado automaticamente quando os bytes do arquivo mudam.
# =====================================================
@st.cache_data(show_spinner="Carregando e processando dados de produtividade...")
def _parse_produtividade(b: bytes) -> pd.DataFrame:
    return load_produtividade(io.BytesIO(b))

@st.cache_data(show_spinner="Carregando dados ETIT POR EVENTO...")
def _parse_etit(b: bytes) -> pd.DataFrame:
    return load_etit(io.BytesIO(b))

@st.cache_data(show_spinner="Carregando Indicadores Residencial...")
def _parse_res_ind(b: bytes) -> pd.DataFrame:
    return load_residencial_indicadores(io.BytesIO(b))

@st.cache_data(show_spinner="Carregando Ocupação DPA...")
def _parse_dpa(b: bytes):
    return load_dpa_ocupacao(io.BytesIO(b))

@st.cache_data(show_spinner="Carregando Indicadores TOA...")
def _parse_toa(b: bytes) -> pd.DataFrame:
    return load_toa_indicadores(io.BytesIO(b))

@st.cache_data(show_spinner="Carregando Fechamento TOA x SIR...")
def _parse_fech_sir(b: bytes, team_ids_key: tuple | None = None, turnos_key: tuple | None = None) -> pd.DataFrame:
    team_ids = set(team_ids_key) if team_ids_key else None
    turnos = set(turnos_key) if turnos_key else None
    return load_fechamento_toa_sir(b, team_ids=team_ids, turnos=turnos)

@st.cache_data(show_spinner="Carregando Chat TOA...")
def _parse_chat_toa(b: bytes) -> pd.DataFrame:
    return load_chat_toa(io.BytesIO(b))

@st.cache_data(show_spinner="Carregando analistas externos — Madrugada...")
def _parse_fora_equipe_fech_sir(b: bytes) -> pd.DataFrame:
    return load_fora_equipe_fech_sir(b)

@st.cache_data(show_spinner="Carregando analistas externos — Madrugada (coord)...")
def _parse_fora_equipe_fech_sir_coord(b: bytes) -> pd.DataFrame:
    return load_fora_equipe_fech_sir_coord(b)

@st.cache_data(show_spinner="Carregando analistas externos — ETIT...")
def _parse_fora_equipe_etit(b: bytes) -> pd.DataFrame:
    return load_fora_equipe_etit(io.BytesIO(b))

@st.cache_data(show_spinner="Carregando analistas externos — TOA...")
def _parse_fora_equipe_toa(b: bytes) -> pd.DataFrame:
    return load_fora_equipe_toa(io.BytesIO(b))

@st.cache_data(show_spinner="Carregando analistas externos — DPA...")
def _parse_fora_equipe_dpa(b: bytes) -> pd.DataFrame:
    return load_fora_equipe_dpa(io.BytesIO(b))

# =====================================================
# DESIGN SYSTEM — Light / Dark Mode
# =====================================================
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
if "cop_page" not in st.session_state:
    st.session_state["cop_page"] = "dashboard"

def _build_css(dark: bool) -> str:
    if dark:
        bg_page, bg_surface, bg_card, bg_card_alt = "#0A0A0A", "#121212", "#1C1C1C", "#222222"
        border, border_subtle = "#2A2A2A", "rgba(255,255,255,0.05)"
        text1, text2, text3   = "#FFFFFF", "#B0B0B0", "#666666"
        shadow    = "0 2px 16px rgba(0,0,0,0.5)"
        shadow_lg = "0 8px 32px rgba(0,0,0,0.6)"
        glass, glass_border   = "rgba(28,28,28,0.85)", "rgba(255,255,255,0.07)"
        sidebar_bg, header_bg = "#0D0D0D", "#0D0D0D"
        upload_bg, upload_bd, upload_hv = "#1C1C1C", "#333333", "#252525"
        tab_inact, tab_hv     = "#171717", "#222222"
        inp_bg, inp_bd        = "#1C1C1C", "#2A2A2A"
        success_bg  = "rgba(46,204,113,0.12)";  success_c  = "#2ECC71"
        warning_bg  = "rgba(230,126,34,0.12)";  warning_c  = "#E67E22"
        danger_bg   = "rgba(231,76,60,0.12)";   danger_c   = "#E74C3C"
        info_bg     = "rgba(93,173,226,0.12)";  info_c     = "#5DADE2"
        gold_bg     = "rgba(241,196,15,0.12)";  gold_c     = "#F1C40F"
        purple_bg   = "rgba(142,68,173,0.12)";  purple_c   = "#9B59B6"
        success_bd  = "rgba(46,204,113,0.22)";  danger_bd  = "rgba(231,76,60,0.22)"
        info_bd     = "rgba(93,173,226,0.22)";  gold_bd    = "rgba(241,196,15,0.22)"
        rank_bg     = "#222222"
    else:
        bg_page, bg_surface, bg_card, bg_card_alt = "#F2F2F2", "#FFFFFF", "#FFFFFF", "#F7F7F7"
        border, border_subtle = "#E0E0E0", "rgba(0,0,0,0.06)"
        text1, text2, text3   = "#000000", "#333333", "#888888"
        shadow    = "0 2px 12px rgba(0,0,0,0.08)"
        shadow_lg = "0 8px 28px rgba(0,0,0,0.14)"
        glass, glass_border   = "rgba(255,255,255,0.90)", "rgba(255,255,255,0.95)"
        sidebar_bg, header_bg = "#FFFFFF", "#FFFFFF"
        upload_bg, upload_bd, upload_hv = "#FAFAFA", "#D0D0D0", "#F2F2F2"
        tab_inact, tab_hv     = "#E6E6E6", "#DCDCDC"
        inp_bg, inp_bd        = "#FFFFFF", "#D0D0D0"
        success_bg  = "rgba(39,174,96,0.10)";   success_c  = "#219653"
        warning_bg  = "rgba(230,126,34,0.10)";  warning_c  = "#C0651A"
        danger_bg   = "rgba(231,76,60,0.10)";   danger_c   = "#C0392B"
        info_bg     = "rgba(41,128,185,0.10)";  info_c     = "#2980B9"
        gold_bg     = "rgba(243,156,18,0.10)";  gold_c     = "#B7770D"
        purple_bg   = "rgba(142,68,173,0.10)";  purple_c   = "#7D3C98"
        success_bd  = "rgba(39,174,96,0.25)";   danger_bd  = "rgba(231,76,60,0.25)"
        info_bd     = "rgba(41,128,185,0.25)";  gold_bd    = "rgba(243,156,18,0.25)"
        rank_bg     = "#ECECEC"

    return f"""<style>
/* ═══════════ DESIGN SYSTEM ═══════════ */
:root {{
    --claro-red:       #ED1C24;
    --claro-red-hover: #C8161D;
    --claro-red-light: rgba(237,28,36,0.12);
    --claro-red-bd:    rgba(237,28,36,0.30);
    --bg-page:    {bg_page};    --bg-surface: {bg_surface};
    --bg-card:    {bg_card};    --bg-card-alt:{bg_card_alt};
    --border:     {border};     --border-sub: {border_subtle};
    --text1: {text1}; --text2: {text2}; --text3: {text3};
    --shadow: {shadow}; --shadow-lg: {shadow_lg};
    --glass: {glass}; --glass-bd: {glass_border};
    --sidebar-bg: {sidebar_bg}; --header-bg: {header_bg};
    --upload-bg: {upload_bg}; --upload-bd: {upload_bd}; --upload-hv: {upload_hv};
    --tab-inact: {tab_inact}; --tab-hv: {tab_hv};
    --inp-bg: {inp_bg}; --inp-bd: {inp_bd};
    --success: {success_c}; --success-bg: {success_bg}; --success-bd: {success_bd};
    --warning: {warning_c}; --warning-bg: {warning_bg};
    --danger:  {danger_c};  --danger-bg:  {danger_bg};  --danger-bd:  {danger_bd};
    --info:    {info_c};    --info-bg:    {info_bg};    --info-bd:    {info_bd};
    --gold:    {gold_c};    --gold-bg:    {gold_bg};    --gold-bd:    {gold_bd};
    --purple:  {purple_c};  --purple-bg:  {purple_bg};
    --rank-bg: {rank_bg};
    --r-sm: 8px; --r-md: 12px; --r-lg: 16px; --r-xl: 20px;
    --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
}}

/* ── Base ── */
html, body, [class*="css"] {{ font-family: var(--font) !important; }}
.stApp, [data-testid="stAppViewContainer"] {{ background: var(--bg-page) !important; }}
section.main {{ background: var(--bg-page) !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; height: 0 !important; padding: 0 !important; min-height: 0 !important; }}
section.main > div.block-container {{ padding-top: 0.25rem !important; padding-bottom: 2rem !important; max-width: 100% !important; }}
div[data-testid="stDecoration"] {{ display: none !important; }}

/* ── UNIVERSAL TEXT OVERRIDES (apply to Streamlit's own React components) ── */
/* General text content */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] b,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em,
[data-testid="stText"] p {{ color: var(--text2) !important; }}
/* Headings */
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5 {{ color: var(--text1) !important; font-weight: 700 !important; }}
/* Widget labels */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
[data-testid="stWidgetLabel"] label {{ color: var(--text2) !important; }}
/* Captions */
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] span {{ color: var(--text3) !important; font-size: 0.82rem !important; }}
/* Alert text */
[data-testid="stAlert"] p,
[data-testid="stNotificationContainer"] p {{ color: var(--text1) !important; }}
/* Checkbox and radio */
[data-testid="stCheckbox"] span,
[data-testid="stRadio"] p,
[data-testid="stRadio"] span {{ color: var(--text2) !important; }}
/* Expander summary */
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {{ color: var(--text1) !important; font-weight: 600 !important; }}
/* Expander body */
.streamlit-expanderContent p,
.streamlit-expanderContent span {{ color: var(--text2) !important; }}
.streamlit-expanderContent {{ background: var(--bg-card) !important; }}
/* Inputs */
.stTextInput input, .stNumberInput input, .stTextArea textarea {{
    color: var(--text1) !important; background-color: var(--inp-bg) !important; border-color: var(--inp-bd) !important;
}}
/* Selectbox value display */
.stSelectbox [data-baseweb="select"] {{ background-color: var(--inp-bg) !important; }}
.stSelectbox [data-baseweb="select"] span {{ color: var(--text1) !important; }}
/* Dropdown popover and options */
[data-baseweb="popover"], [data-baseweb="menu"] {{ background-color: var(--bg-card) !important; border: 1px solid var(--border) !important; }}
[data-baseweb="list-item"], [data-baseweb="option"] {{ background-color: var(--bg-card) !important; color: var(--text1) !important; }}
[data-baseweb="list-item"]:hover {{ background-color: var(--bg-card-alt) !important; }}
/* File uploader text */
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzoneInstructions"] span {{ color: var(--text3) !important; }}
[data-testid="stFileUploaderDropzone"] button span {{ color: var(--claro-red) !important; }}
/* Metric component */
[data-testid="stMetricValue"] {{ color: var(--text1) !important; }}
[data-testid="stMetricLabel"] {{ color: var(--text2) !important; }}
[data-testid="stMetricDelta"] {{ color: var(--text3) !important; }}
/* Success/warning/info box backgrounds */
div[data-testid="stAlert"][kind="success"] {{ background: var(--success-bg) !important; border-color: var(--success) !important; }}
div[data-testid="stAlert"][kind="warning"] {{ background: var(--warning-bg) !important; border-color: var(--warning) !important; }}
div[data-testid="stAlert"][kind="info"]    {{ background: var(--info-bg) !important;    border-color: var(--info)    !important; }}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{ background: var(--sidebar-bg) !important; border-right: 1px solid var(--border) !important; }}
[data-testid="stSidebar"] > div {{ background: var(--sidebar-bg) !important; }}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{ color: var(--text2) !important; }}
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {{ color: var(--text1) !important; }}
[data-testid="stSidebar"] .stSelectbox > div > div {{ background: var(--bg-card) !important; border-color: var(--border) !important; color: var(--text1) !important; border-radius: var(--r-sm) !important; }}
[data-testid="stSidebar"] .stButton > button {{ background: var(--bg-card) !important; color: var(--text2) !important; border: 1px solid var(--border) !important; border-radius: var(--r-sm) !important; font-weight: 500 !important; transition: all 0.2s !important; }}
[data-testid="stSidebar"] .stButton > button:hover {{ border-color: var(--claro-red) !important; color: var(--claro-red) !important; }}
.sidebar-brand {{ background: linear-gradient(135deg, var(--claro-red) 0%, #A50E14 100%); border-radius: var(--r-md); padding: 1rem 1.1rem; margin-bottom: 0.9rem; position: relative; overflow: hidden; box-shadow: 0 4px 16px rgba(237,28,36,0.3); }}
.sidebar-brand::after {{ content: ''; position: absolute; top: -20px; right: -20px; width: 80px; height: 80px; border-radius: 50%; background: rgba(255,255,255,0.08); }}
.sidebar-brand-logo {{ font-size: 1.35rem; font-weight: 900; color: white !important; letter-spacing: -0.5px; }}
.sidebar-brand-sub {{ font-size: 0.7rem; color: rgba(255,255,255,0.72) !important; margin-top: 2px; letter-spacing: 0.3px; }}
.sidebar-user-card {{ background: var(--bg-card); border: 1px solid var(--border); border-left: 3px solid var(--claro-red); border-radius: var(--r-md); padding: 0.8rem 1rem; margin-bottom: 0.75rem; }}
.sidebar-user-name {{ font-weight: 700; font-size: 0.95rem; color: var(--text1) !important; }}
.sidebar-user-role {{ font-size: 0.72rem; color: var(--claro-red) !important; font-weight: 600; margin-top: 2px; }}
.sidebar-section {{ font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--text3) !important; margin: 0.9rem 0 0.4rem 0; }}

/* ── BUTTONS ── */
.stButton > button {{ font-family: var(--font) !important; font-weight: 600 !important; border-radius: var(--r-sm) !important; transition: all 0.2s ease !important; }}
.stButton > button[kind="primary"] {{ background: var(--claro-red) !important; border: none !important; color: white !important; }}
.stButton > button[kind="primary"]:hover {{ background: var(--claro-red-hover) !important; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(237,28,36,0.35) !important; }}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{ background: var(--tab-inact) !important; border-radius: var(--r-md) !important; padding: 4px !important; gap: 2px !important; border-bottom: none !important; }}
.stTabs [data-baseweb="tab"] {{ background: transparent !important; border-radius: var(--r-sm) !important; color: var(--text3) !important; font-weight: 500 !important; font-size: 0.82rem !important; padding: 0.42rem 0.9rem !important; transition: all 0.2s ease !important; border: none !important; }}
.stTabs [data-baseweb="tab"]:hover {{ background: var(--tab-hv) !important; color: var(--text2) !important; }}
.stTabs [aria-selected="true"] {{ background: var(--bg-surface) !important; color: var(--claro-red) !important; font-weight: 700 !important; box-shadow: var(--shadow) !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none !important; }}

/* ── INPUTS / SELECTS ── */
.stSelectbox > div > div, .stMultiSelect > div > div {{ background: var(--inp-bg) !important; border-color: var(--inp-bd) !important; border-radius: var(--r-sm) !important; color: var(--text1) !important; }}
.stSelectbox label, .stMultiSelect label {{ color: var(--text2) !important; font-size: 0.79rem !important; font-weight: 500 !important; }}

/* ── FILE UPLOADER (upload cards) ── */
.stFileUploader {{ background: var(--upload-bg) !important; border: 1.5px dashed var(--upload-bd) !important; border-radius: var(--r-md) !important; transition: all 0.2s ease !important; }}
.stFileUploader:hover {{ border-color: var(--claro-red) !important; background: var(--upload-hv) !important; }}
.stFileUploader label {{ color: var(--text2) !important; font-size: 0.78rem !important; font-weight: 600 !important; }}
[data-testid="stFileUploaderDropzone"] {{ background: transparent !important; border: none !important; }}
[data-testid="stFileUploaderDropzoneInstructions"] {{ color: var(--text3) !important; font-size: 0.72rem !important; }}

/* ── DATAFRAME ── */
.dataframe {{ font-size: 0.82rem !important; font-family: var(--font) !important; }}
[data-testid="stDataFrame"] {{ border-radius: var(--r-md) !important; overflow: hidden !important; border: 1px solid var(--border) !important; }}

/* ── EXPANDER ── */
[data-testid="stExpander"] {{ background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; overflow: hidden !important; }}
[data-testid="stExpander"] summary {{ color: var(--text1) !important; font-weight: 600 !important; }}

/* ── METRICS ── */
[data-testid="stMetric"] {{ background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; padding: 1rem !important; }}
[data-testid="stMetricValue"] {{ color: var(--text1) !important; font-weight: 800 !important; }}
[data-testid="stMetricLabel"] {{ color: var(--text2) !important; }}

/* ── ALERTS ── */
.stSuccess {{ background: var(--success-bg) !important; border-left-color: var(--success) !important; border-radius: var(--r-sm) !important; }}
.stWarning {{ background: var(--warning-bg) !important; border-left-color: var(--warning) !important; border-radius: var(--r-sm) !important; }}
.stInfo    {{ background: var(--info-bg) !important;    border-left-color: var(--info)    !important; border-radius: var(--r-sm) !important; }}
hr {{ border-color: var(--border) !important; opacity: 1 !important; }}

/* ═══════ COMPONENT LIBRARY ═══════ */

/* Main page header */
.main-header {{ background: linear-gradient(135deg, var(--claro-red) 0%, #A50E14 100%); padding: 1.4rem 2rem; border-radius: var(--r-xl); margin-bottom: 1.5rem; box-shadow: 0 4px 22px rgba(237,28,36,0.28); position: relative; overflow: hidden; }}
.main-header::before {{ content: ''; position: absolute; top: -30px; right: -30px; width: 130px; height: 130px; border-radius: 50%; background: rgba(255,255,255,0.07); pointer-events: none; }}
.main-header::after  {{ content: ''; position: absolute; bottom: -45px; right: 70px; width: 190px; height: 190px; border-radius: 50%; background: rgba(255,255,255,0.04); pointer-events: none; }}
.main-header h1 {{ color: #fff !important; margin: 0 !important; font-size: 1.7rem !important; font-weight: 800 !important; letter-spacing: -0.3px; }}
.main-header p  {{ color: rgba(255,255,255,0.78) !important; margin: 0.3rem 0 0 0 !important; font-size: 0.88rem !important; }}

/* ═══════════ UPLOAD PAGE ═══════════ */
.upload-page-hero {{ background: linear-gradient(135deg, var(--claro-red) 0%, #A50E14 100%); border-radius: var(--r-xl); padding: 2rem 2.5rem; margin-bottom: 2rem; box-shadow: 0 6px 28px rgba(237,28,36,0.3); position: relative; overflow: hidden; }}
.upload-page-hero::before {{ content: ''; position: absolute; top: -40px; right: -40px; width: 180px; height: 180px; border-radius: 50%; background: rgba(255,255,255,0.07); pointer-events: none; }}
.upload-page-hero::after  {{ content: ''; position: absolute; bottom: -50px; right: 80px; width: 220px; height: 220px; border-radius: 50%; background: rgba(255,255,255,0.04); pointer-events: none; }}
.upload-page-hero h2 {{ color: white !important; font-size: 1.8rem; font-weight: 800; margin: 0; }}
.upload-page-hero p  {{ color: rgba(255,255,255,0.80) !important; margin: 0.4rem 0 0; font-size: 0.95rem; }}
.upload-card {{ background: var(--bg-card); border: 1.5px solid var(--border); border-radius: var(--r-lg); padding: 1.5rem 1.4rem; height: 100%; transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease; position: relative; overflow: hidden; }}
.upload-card:hover {{ border-color: var(--claro-red); box-shadow: var(--shadow-lg); transform: translateY(-3px); }}
.upload-card-icon {{ font-size: 2rem; line-height: 1; margin-bottom: 0.75rem; }}
.upload-card-title {{ font-size: 1rem; font-weight: 700; color: var(--text1); margin-bottom: 0.25rem; }}
.upload-card-desc {{ font-size: 0.78rem; color: var(--text3); margin-bottom: 1rem; line-height: 1.45; }}
.upload-card-status-ok  {{ display: inline-flex; align-items: center; gap: 5px; background: var(--success-bg); color: var(--success); border: 1px solid var(--success-bd); border-radius: 20px; padding: 3px 10px; font-size: 0.72rem; font-weight: 700; margin-bottom: 0.85rem; }}
.upload-card-status-no  {{ display: inline-flex; align-items: center; gap: 5px; background: var(--bg-card-alt); color: var(--text3); border: 1px solid var(--border); border-radius: 20px; padding: 3px 10px; font-size: 0.72rem; font-weight: 600; margin-bottom: 0.85rem; }}
.upload-stats-bar {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-md); padding: 1.2rem 1.5rem; margin-top: 1.5rem; display: flex; align-items: center; justify-content: space-between; }}
.upload-stats-item {{ text-align: center; }}
.upload-stats-val  {{ font-size: 1.6rem; font-weight: 800; color: var(--claro-red); }}
.upload-stats-lbl  {{ font-size: 0.7rem; color: var(--text3); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
/* Upload section header (inline, legacy) */
.upload-section-hdr {{ display: none; }}

/* KPI card — glassmorphism */
.kpi-card {{ background: var(--glass) !important; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid var(--glass-bd) !important; border-radius: var(--r-lg) !important; padding: 1.2rem 1rem !important; border-left: 4px solid !important; text-align: center; box-shadow: var(--shadow); transition: transform 0.2s ease, box-shadow 0.2s ease; }}
.kpi-card:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-lg); }}
.kpi-card .kpi-value {{ font-size: 1.85rem; font-weight: 800; margin: 0.25rem 0; line-height: 1; color: var(--text1); }}
.kpi-card .kpi-label {{ font-size: 0.7rem; color: var(--text3); text-transform: uppercase; letter-spacing: 0.8px; font-weight: 700; }}
.kpi-card .kpi-delta {{ font-size: 0.78rem; margin-top: 0.25rem; font-weight: 500; }}

/* Section header */
.section-header {{ font-size: 0.95rem; font-weight: 700; color: var(--claro-red); border-bottom: 2px solid rgba(237,28,36,0.18); padding-bottom: 0.4rem; margin: 1.5rem 0 1rem 0; text-transform: uppercase; letter-spacing: 0.5px; }}

/* Performance cards */
.perf-card {{ padding: 0.85rem 1rem; border-radius: var(--r-md); border-left: 4px solid; margin-bottom: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-sub); border-left: 4px solid; transition: transform 0.15s ease; }}
.perf-card:hover {{ transform: translateX(3px); }}
.perf-best  {{ border-left-color: var(--success) !important; background: var(--success-bg) !important; }}
.perf-worst {{ border-left-color: var(--danger)  !important; background: var(--danger-bg)  !important; }}
.perf-dpa   {{ border-left-color: var(--info)    !important; background: var(--info-bg)    !important; }}
.perf-card .p-title  {{ font-size: 0.72rem; font-weight: 700; margin-bottom: 0.2rem; color: var(--text3); text-transform: uppercase; letter-spacing: 0.4px; }}
.perf-card .p-name   {{ font-size: 1.05rem; font-weight: 800; color: var(--text1); }}
.perf-card .p-detail {{ font-size: 0.78rem; color: var(--text3); margin-top: 0.15rem; }}

/* Insight card */
.insight-card {{ background: var(--bg-card); border: 1px solid var(--border-sub); border-left: 3px solid var(--claro-red); border-radius: var(--r-md); padding: 0.85rem 1rem; margin-bottom: 0.6rem; transition: box-shadow 0.2s ease; }}
.insight-card:hover {{ box-shadow: var(--shadow); }}

/* Tags / Badges */
.tag-green {{ background: var(--success-bg); color: var(--success); padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; display: inline-block; margin: 1px 2px; border: 1px solid var(--success-bd); }}
.tag-red   {{ background: var(--danger-bg);  color: var(--danger);  padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; display: inline-block; margin: 1px 2px; border: 1px solid var(--danger-bd); }}
.sector-badge {{ background: var(--info-bg); color: var(--info); padding: 2px 8px; border-radius: 8px; font-size: 0.7rem; font-weight: 600; margin-left: 6px; border: 1px solid var(--info-bd); }}
.rank-pill {{ background: var(--rank-bg); border: 1px solid var(--border); padding: 2px 8px; border-radius: 8px; font-size: 0.7rem; color: var(--text3); margin-left: 3px; }}

/* Leader card */
.leader-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--r-md); padding: 1rem 1.2rem; border-top: 3px solid var(--gold); margin-bottom: 0.75rem; box-shadow: var(--shadow); transition: transform 0.2s ease; }}
.leader-card:hover {{ transform: translateY(-2px); }}
.leader-card .l-name  {{ font-size: 1rem; font-weight: 700; color: var(--text1); }}
.leader-card .l-badge {{ background: var(--gold-bg); color: var(--gold); padding: 2px 8px; border-radius: 8px; font-size: 0.7rem; font-weight: 700; margin-left: 6px; border: 1px solid var(--gold-bd); }}
.leader-card .l-stat  {{ font-size: 0.8rem; color: var(--text2); margin-top: 0.3rem; }}
.leader-card .l-vol   {{ font-size: 1.35rem; font-weight: 800; color: var(--claro-red); }}

/* Sector badges */
.sector-header {{ display: inline-block; padding: 0.3rem 0.9rem; border-radius: var(--r-sm); font-weight: 700; font-size: 0.8rem; margin-bottom: 0.6rem; text-transform: uppercase; letter-spacing: 0.5px; }}
.sector-res {{ background: var(--info-bg);    color: var(--info);    border: 1px solid var(--info-bd); }}
.sector-emp {{ background: var(--warning-bg); color: var(--warning); }}

/* ETIT card */
.etit-card {{ background: var(--bg-card); border: 1px solid var(--border); border-left: 4px solid var(--purple); border-radius: var(--r-md); padding: 1rem 1.2rem; margin-bottom: 0.6rem; }}

/* Residencial Indicator cards */
.res-ind-card {{ background: var(--glass); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); border: 1px solid var(--glass-bd); border-radius: var(--r-lg); padding: 1.2rem; border-top: 3px solid; margin-bottom: 0.6rem; box-shadow: var(--shadow); transition: transform 0.2s ease; }}
.res-ind-card:hover {{ transform: translateY(-2px); }}
.res-ind-card .ri-title  {{ font-size: 0.68rem; font-weight: 700; color: var(--text3); text-transform: uppercase; letter-spacing: 0.9px; margin-bottom: 0.4rem; }}
.res-ind-card .ri-vol    {{ font-size: 1.65rem; font-weight: 800; line-height: 1; color: var(--text1); }}
.res-ind-card .ri-pct    {{ font-size: 1rem; font-weight: 600; margin-top: 0.2rem; }}
.res-ind-card .ri-detail {{ font-size: 0.75rem; color: var(--text3); margin-top: 0.3rem; }}

/* DPA cards */
.dpa-card {{ background: var(--bg-card); border: 1px solid var(--border); border-left: 4px solid #16A085; border-radius: var(--r-md); padding: 1rem 1.2rem; margin-bottom: 0.5rem; transition: transform 0.15s ease; }}
.dpa-card:hover {{ transform: translateX(3px); }}
.dpa-card .dpa-nome  {{ font-size: 0.95rem; font-weight: 700; color: var(--text1); }}
.dpa-card .dpa-val   {{ font-size: 1.35rem; font-weight: 800; }}
.dpa-card .dpa-setor {{ font-size: 0.72rem; color: var(--text3); margin-top: 0.15rem; }}
.dpa-semaforo-verde    {{ color: var(--success); }}
/* ═══════════ ANALYST COCKPIT STYLES ═══════════ */
.analyst-hero-banner {
    background: linear-gradient(135deg, rgba(237,28,36,0.12) 0%, rgba(165,14,20,0.22) 100%);
    border: 1px solid var(--claro-red-bd);
    border-radius: var(--r-xl);
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: var(--shadow);
}
.analyst-greeting { font-size: 1.4rem; font-weight: 800; color: var(--text1); margin: 0; }
.analyst-subgreeting { font-size: 0.84rem; color: var(--text3); margin-top: 0.2rem; }
.analyst-badge-row { display: flex; align-items: center; gap: 8px; margin-top: 0.6rem; flex-wrap: wrap; }
.analyst-pill {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 5px;
}
.analyst-pill-setor { background: var(--info-bg); color: var(--info); border: 1px solid var(--info-bd); }
.analyst-pill-cert-ok { background: var(--success-bg); color: var(--success); border: 1px solid var(--success-bd); }
.analyst-pill-cert-alert { background: var(--warning-bg); color: var(--warning); border: 1px solid var(--warning-bg); }
.analyst-pill-cert-danger { background: var(--danger-bg); color: var(--danger); border: 1px solid var(--danger-bd); }

/* Responsive */
@media (max-width: 768px) {{
    .main-header h1 {{ font-size: 1.3rem !important; }}
    section.main > div.block-container {{ padding-left: 1rem !important; padding-right: 1rem !important; }}
    .analyst-hero-banner {{ flex-direction: column; align-items: flex-start; gap: 0.8rem; }}
}}
</style>"""

_dark = st.session_state["dark_mode"]
st.markdown(_build_css(_dark), unsafe_allow_html=True)


# =====================================================
# HELPERS
# =====================================================
def kpi_card(label, value, color, delta=None, suffix=""):
    delta_html = ""
    if delta is not None:
        delta_color = COR_SUCESSO if delta >= 0 else COR_PERIGO
        delta_icon = "▲" if delta >= 0 else "▼"
        delta_html = f'<div class="kpi-delta" style="color:{delta_color}">{delta_icon} {abs(delta):.1f}{suffix}</div>'
    return f"""
    <div class="kpi-card" style="border-left-color: {color};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color: {color};">{value}{suffix}</div>
        {delta_html}
    </div>
    """


def _dpa_color(pct):
    if pct is None or (isinstance(pct, float) and np.isnan(pct)):
        return COR_INFO
    if pct >= DPA_THRESHOLD_OK:
        return COR_SUCESSO
    if pct >= DPA_THRESHOLD_ALERTA:
        return COR_ALERTA
    return COR_PERIGO


def _dpa_semaforo(pct):
    if pct is None:
        return "—"
    if pct >= DPA_THRESHOLD_OK:
        return "🟢"
    if pct >= DPA_THRESHOLD_ALERTA:
        return "🟡"
    return "🔴"


def _dpa_equipe_pct(df):
    """Média das médias por setor — cada setor pesa igual, independente do tamanho.

    Para escopos com ambos os setores, retorna (média Empresarial + média Residencial) / 2.
    Para escopos com apenas um setor presente, retorna a média desse setor.
    Se não houver coluna 'Setor' ou setor identificável, cai na média simples.
    """
    if df is None or df.empty or "DPA_Pct_Oficial" not in df.columns:
        return None
    if "Setor" in df.columns:
        _df = df.dropna(subset=["DPA_Pct_Oficial"])
        _df = _df[_df["Setor"].isin(["EMPRESARIAL", "RESIDENCIAL"])]
        if not _df.empty:
            return float(_df.groupby("Setor")["DPA_Pct_Oficial"].mean().mean())
    _serie = df["DPA_Pct_Oficial"].dropna()
    return float(_serie.mean()) if not _serie.empty else None


def _fmt_hms(val):
    """Converte horas decimais para string HH:MM:SS."""
    if val is None or (isinstance(val, float) and (np.isnan(val) or val < 0)):
        return "—"
    total_sec = round(float(val) * 3600)
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_sector_vol_cols(setor, available_cols):
    cols = {}
    if setor in ("Todos", "RESIDENCIAL"):
        cols.update(VOL_COLS_RESIDENCIAL)
    if setor in ("Todos", "EMPRESARIAL"):
        cols.update(VOL_COLS_EMPRESARIAL)
    cols.update(VOL_COLS_AMBOS)
    return {k: v for k, v in cols.items() if k in available_cols}


def build_insights(resumo_df, setor_filter):
    data = []
    for _, row in resumo_df.sort_values(COL_VOL_TOTAL, ascending=False).iterrows():
        nome = primeiro_nome(row[COL_NOME])
        setor = row["Setor"]
        peers = resumo_df[resumo_df["Setor"] == setor]
        n_peers = len(peers)
        if n_peers < 2:
            continue
        if setor == "RESIDENCIAL":
            relevant = {**VOL_COLS_RESIDENCIAL, **VOL_COLS_AMBOS}
        else:
            relevant = {**VOL_COLS_EMPRESARIAL, **VOL_COLS_AMBOS}
        vol_keys_r = [k for k in relevant if k in resumo_df.columns]
        strengths, weaknesses = [], []
        for k in vol_keys_r:
            val = row.get(k, 0)
            if pd.isna(val) or val == 0:
                continue
            rank = int((peers[k].fillna(0) > val).sum() + 1)
            if rank == 1:
                strengths.append(relevant[k])
            elif rank >= n_peers:
                weaknesses.append(relevant[k])
        avg_vol = peers[COL_VOL_TOTAL].mean()
        vol_diff = ((row[COL_VOL_TOTAL] / avg_vol - 1) * 100) if avg_vol > 0 else 0
        vol_rank = int((peers[COL_VOL_TOTAL].fillna(0) > row[COL_VOL_TOTAL]).sum() + 1)
        dpa_val = row.get("DPA_Media", None)
        data.append({
            "nome": nome, "setor": setor, "login": row[COL_LOGIN],
            "vol_total": row[COL_VOL_TOTAL], "media_diaria": row.get("Media_Diaria", 0),
            "dias": row.get("Dias_Trabalhados", 0), "vol_diff": vol_diff,
            "vol_rank": vol_rank, "dpa": dpa_val,
            "strengths": strengths[:4], "weaknesses": weaknesses[:4], "n_peers": n_peers,
        })
    return data


def render_insight_cards(insights_list):
    col_l, col_r = st.columns(2)
    for i, ins in enumerate(insights_list):
        target = col_l if i % 2 == 0 else col_r
        vol_color = "#2ECC71" if ins["vol_diff"] >= 0 else "#E74C3C"
        vol_icon = "▲" if ins["vol_diff"] >= 0 else "▼"
        border = "#2ECC71" if ins["vol_diff"] >= 10 else ("#E74C3C" if ins["vol_diff"] < -10 else "#5DADE2")
        dpa_str = f"{ins['dpa']:.1f}%" if pd.notna(ins["dpa"]) else "—"
        str_tags = "".join(f'<span class="tag-green">{s}</span>' for s in ins["strengths"])
        weak_tags = "".join(f'<span class="tag-red">{w}</span>' for w in ins["weaknesses"])
        if not str_tags:
            str_tags = '<span style="opacity:0.35;font-size:0.73rem;">—</span>'
        if not weak_tags:
            weak_tags = '<span style="opacity:0.35;font-size:0.73rem;">—</span>'
        with target:
            st.markdown(f"""<div class="insight-card" style="border-left-color:{border};">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <strong>{ins['nome']}</strong>
                        <span class="sector-badge">{ins['setor'][:3]}</span>
                        <span class="rank-pill">#{ins['vol_rank']}/{ins['n_peers']}</span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-weight:700;">{ins['vol_total']:,.0f}</span>
                        <span style="color:{vol_color};font-size:0.82rem;margin-left:3px;">{vol_icon}{abs(ins['vol_diff']):.0f}%</span>
                        <span style="opacity:0.5;font-size:0.78rem;margin-left:6px;">DPA:{dpa_str}</span>
                    </div>
                </div>
                <div style="margin-top:0.4rem;">
                    <span style="font-size:0.78rem;opacity:0.5;">Forte:</span> {str_tags}
                    <span style="font-size:0.78rem;opacity:0.5;margin-left:8px;">Atenção:</span> {weak_tags}
                </div>
            </div>""", unsafe_allow_html=True)


def _cap_pt(texto):
    """Capitaliza a primeira letra de uma frase em pt-BR sem alterar o restante."""
    return texto[:1].upper() + texto[1:] if texto else texto


# Leitura qualitativa por TEMA — interpreta o padrão que os indicadores revelam,
# sem citar números. Cada tema agrupa um conjunto de indicadores e tem frases para
# os cenários forte / misto / atenção, além de uma sugestão de conversa/ação.
# Ordem da lista = prioridade na narrativa.
_HL_TEMAS = [
    {
        "key": "produtividade",
        "forte":   "produtividade alta e ritmo de entrega acima da média da equipe",
        "misto":   "produção em bom patamar, com espaço para ganhar regularidade",
        "atencao": "o ritmo de produção indica espaço para ganhar consistência e previsibilidade nas entregas",
        "sugestao": "organizar a rotina de produção, com metas diárias claras, para dar mais regularidade às entregas",
    },
    {
        "key": "qualidade",
        "forte":   "boa qualidade operacional, sustentando a aderência nos processos críticos",
        "misto":   "qualidade operacional sólida na maior parte das frentes, com pontos a alinhar",
        "atencao": "a aderência aos processos críticos pede atenção para sustentar a qualidade das tratativas",
        "sugestao": "revisar com a liderança os critérios de processo, usando casos reais como referência, para fortalecer a aderência",
    },
    {
        "key": "jornada",
        "forte":   "bom aproveitamento da jornada, com ocupação equilibrada ao longo do dia",
        "misto":   "aproveitamento da jornada razoável, com oscilações ao longo do dia",
        "atencao": "o aproveitamento da jornada sugere necessidade de revisar gestão de tempo, pausas e priorização",
        "sugestao": "conversar sobre organização da jornada, pausas e priorização para recuperar previsibilidade na entrega",
    },
    {
        "key": "atendimento",
        "forte":   "agilidade no atendimento via chat, dentro dos tempos esperados",
        "misto":   "atendimento via chat em bom ritmo, com margem para ganhar agilidade",
        "atencao": "o tempo de atendimento no chat aponta oportunidade de ganhar agilidade sem perder qualidade",
        "sugestao": "padronizar respostas frequentes e organizar os atendimentos simultâneos para ganhar agilidade no chat",
    },
    {
        "key": "controle",
        "forte":   "controle operacional consistente, com baixo retrabalho",
        "misto":   "controle operacional adequado, com algum retrabalho a observar",
        "atencao": "o nível de retrabalho operacional pede acompanhamento para reduzir cancelamentos e reaberturas",
        "sugestao": "mapear os motivos mais frequentes de cancelamento para reduzir o retrabalho operacional",
    },
]
_HL_TEMAS_BY_KEY = {t["key"]: t for t in _HL_TEMAS}


def _hl_tema_do_indicador(label):
    """Classifica um indicador (pelo rótulo) em um tema de leitura qualitativa.

    Usa palavras-chave para ser tolerante a variações de rótulo entre planilhas.
    Retorna a chave do tema ou None (rótulos puramente informativos/volume).
    """
    lab = (label or "").lower()
    if "cancel" in lab:
        return "controle"
    if "chat" in lab and "tma" in lab:                 # tempo de atendimento no chat
        return "atendimento"
    if "dpa" in lab or "ocupa" in lab:
        return "jornada"
    if any(k in lab for k in (
        "ader", "etit", "assert", "fech", "formul", "validaç", "validac", "sir",
    )):
        return "qualidade"
    if any(k in lab for k in (
        "vol", "média", "media", "produt", "primeiro int", "dia", "evento",
    )):
        return "produtividade"
    return None


def build_highlight_feedback(items):
    """Lê uma lista de (label, valor_str, cor) e devolve uma leitura QUALITATIVA do
    desempenho — interpreta o padrão que os indicadores formam por tema (produtividade,
    qualidade, aproveitamento de jornada, atendimento, controle), sem citar números.

    A cor já classifica cada indicador: COR_SUCESSO = bom; COR_ALERTA/COR_PERIGO =
    atenção; COR_INFO = informativo (não pesa na leitura). Tom construtivo — quem lê
    é o próprio analista sobre o seu desempenho.

    Retorna dict: resumo, ponto_forte, ponto_atencao, sugestao.
    """
    # Agrega o status de cada indicador por tema: contagem de bons x atenções.
    agg = {}  # key -> {"bom": int, "aten": int}
    for label, _valor_str, cor in items:
        tema = _hl_tema_do_indicador(label)
        if tema is None:
            continue
        if cor not in (COR_SUCESSO, COR_ALERTA, COR_PERIGO):
            continue  # COR_INFO e afins: informativo, não entra na leitura
        d = agg.setdefault(tema, {"bom": 0, "aten": 0})
        if cor == COR_SUCESSO:
            d["bom"] += 1
        else:
            d["aten"] += 1

    # Classifica cada tema avaliado em forte / misto / atenção, preservando a
    # ordem de prioridade definida em _HL_TEMAS.
    fortes, mistos, atencoes = [], [], []
    for tema in _HL_TEMAS:
        d = agg.get(tema["key"])
        if not d:
            continue
        if d["aten"] == 0:
            fortes.append(tema)
        elif d["bom"] == 0:
            atencoes.append(tema)
        else:
            mistos.append(tema)

    n_temas = len(fortes) + len(mistos) + len(atencoes)
    # Temas com algo a evoluir (atenção primeiro, depois mistos) para foco da leitura.
    a_evoluir = atencoes + mistos

    # ── Resumo geral (perfil do analista no período) ──
    if n_temas == 0:
        resumo = (
            "Ainda não há indicadores suficientes para uma leitura do seu desempenho "
            "neste período — assim que os dados forem carregados, a análise aparece aqui."
        )
    elif not a_evoluir:
        resumo = (
            "Analista consistente, com desempenho equilibrado e sob controle em todas as "
            "frentes avaliadas — um período sólido do começo ao fim."
        )
    elif not fortes and not mistos:
        resumo = (
            "Período de ajustes: as principais frentes pedem atenção, mas o quadro é "
            "totalmente recuperável com foco em poucos pontos de cada vez."
        )
    else:
        resumo = (
            "Analista com bons fundamentos e algumas frentes em desenvolvimento neste "
            "período — o equilíbrio está ao alcance com ajustes pontuais na rotina."
        )

    # ── Ponto Forte (padrão positivo que os números revelam) ──
    destaques = ([t["forte"] for t in fortes] + [t["misto"] for t in mistos])[:3]
    if destaques:
        primeiro = destaques[0]
        if len(destaques) == 1:
            ponto_forte = _cap_pt(f"analista que demonstra {primeiro}.")
        else:
            extras = destaques[1:]
            # une os destaques extras com vírgulas e "e" antes do último, para fluir bem
            if len(extras) == 1:
                resto = extras[0]
            else:
                resto = ", ".join(extras[:-1]) + " e " + extras[-1]
            ponto_forte = _cap_pt(
                f"analista consistente, com {primeiro}. Além disso, demonstra {resto}."
            )
    else:
        ponto_forte = (
            "Mesmo sem uma frente totalmente consolidada, há base para evoluir rápido: "
            "escolher um único foco por semana costuma destravar os demais indicadores."
        )

    # ── Ponto de Atenção (padrão que pede cuidado) ──
    if a_evoluir:
        frases_at = [t["atencao"] for t in a_evoluir]
        ponto_atencao = _cap_pt("; ".join(frases_at)) + "."
    else:
        ponto_atencao = (
            "Nenhuma frente exige atenção neste período. O cuidado agora é manter a "
            "constância para preservar esse bom patamar."
        )

    # ── Sugestão (conversa/ação ancorada na frente prioritária) ──
    if a_evoluir:
        sugs = []
        for t in a_evoluir[:2]:
            sugs.append(t["sugestao"])
        sugestao = _cap_pt(sugs[0])
        if len(sugs) > 1:
            sugestao += f". Em paralelo, {sugs[1]}"
        sugestao += "."
    else:
        sugestao = (
            "Seguir mantendo a rotina atual e compartilhar com a equipe o que está "
            "funcionando — isso fortalece o time e reforça a sua referência técnica."
        )

    return {
        "resumo": resumo,
        "ponto_forte": ponto_forte,
        "ponto_atencao": ponto_atencao,
        "sugestao": sugestao,
    }


def render_sector_table(resumo_df, sector_name, sector_vol, sector_cmap):
    df_sec = resumo_df[resumo_df["Setor"] == sector_name].copy()
    if df_sec.empty:
        return
    all_vol = {**sector_vol, **VOL_COLS_AMBOS}
    vol_keys = [k for k in all_vol if k in df_sec.columns]
    css_cls = "sector-res" if sector_name == "RESIDENCIAL" else "sector-emp"
    icon = "🏠" if sector_name == "RESIDENCIAL" else "🏢"
    st.markdown(f'<span class="sector-header {css_cls}">{icon} {sector_name}</span>', unsafe_allow_html=True)
    base = [COL_NOME, COL_VOL_TOTAL, "Dias_Trabalhados", "Media_Diaria", "DPA_Media"]
    base_avail = [c for c in base if c in df_sec.columns]
    detail = df_sec[base_avail + vol_keys].copy()
    detail["Nome"] = detail[COL_NOME].apply(primeiro_nome)
    avg_vol = detail[COL_VOL_TOTAL].mean()
    detail["vs Média"] = ((detail[COL_VOL_TOTAL] / avg_vol - 1) * 100).round(1) if avg_vol > 0 else 0.0
    disp_cols = ["Nome", COL_VOL_TOTAL, "Dias_Trabalhados", "Media_Diaria", "vs Média", "DPA_Media"] + vol_keys
    disp_cols = [c for c in disp_cols if c in detail.columns]
    disp = detail[disp_cols].copy()
    rename = {
        "Nome": "Analista", COL_VOL_TOTAL: "Vol. Total",
        "Dias_Trabalhados": "Dias", "Media_Diaria": "Média/Dia", "DPA_Media": "DPA %",
    }
    rename.update({k: all_vol[k] for k in vol_keys})
    disp = disp.rename(columns=rename)
    disp = disp.sort_values("Vol. Total", ascending=False).reset_index(drop=True)
    disp.index += 1; disp.index.name = "#"
    fmt = {"DPA %": "{:.1f}", "Média/Dia": "{:.1f}", "vs Média": "{:+.1f}"}
    styled = disp.style.format(fmt, na_rep="—")
    _sv_max = disp["Vol. Total"].max()
    _sv_vmax = float(_sv_max) if pd.notna(_sv_max) and _sv_max > 0 else 1.0
    styled = styled.background_gradient(cmap=sector_cmap, subset=["Vol. Total"], vmin=0, vmax=_sv_vmax)
    if disp["vs Média"].notna().any():
        styled = styled.background_gradient(cmap="RdYlGn", subset=["vs Média"], vmin=-50, vmax=50)
    if "DPA %" in disp.columns and disp["DPA %"].notna().any():
        styled = styled.background_gradient(cmap="RdYlGn", subset=["DPA %"], vmin=50, vmax=100)
    for vl in [all_vol[k] for k in vol_keys]:
        if vl in disp.columns and disp[vl].notna().any():
            _col_max = disp[vl].max()
            _col_vmax = float(_col_max) if pd.notna(_col_max) and _col_max > 0 else 1.0
            styled = styled.background_gradient(cmap=sector_cmap, subset=[vl], vmin=0, vmax=_col_vmax)
    st.dataframe(styled, use_container_width=True)
    if len(disp) >= 2:
        best = disp.iloc[0]; worst = disp.iloc[-1]; best_dpa_row = None
        if "DPA %" in disp.columns:
            dpa_v = disp.dropna(subset=["DPA %"])
            if not dpa_v.empty:
                best_dpa_row = dpa_v.sort_values("DPA %", ascending=False).iloc[0]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="perf-card perf-best">
                <div class="p-title">🏆 Maior Volume</div>
                <div class="p-name" style="color:#2ECC71;">{best['Analista']}</div>
                <div class="p-detail">Vol: {best['Vol. Total']:,.0f} · Média: {best['Média/Dia']:.1f}/dia</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="perf-card perf-worst">
                <div class="p-title">⚠️ Menor Volume</div>
                <div class="p-name" style="color:#E74C3C;">{worst['Analista']}</div>
                <div class="p-detail">Vol: {worst['Vol. Total']:,.0f} · Média: {worst['Média/Dia']:.1f}/dia</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            if best_dpa_row is not None:
                st.markdown(f"""<div class="perf-card perf-dpa">
                    <div class="p-title">📊 Melhor DPA</div>
                    <div class="p-name" style="color:#5DADE2;">{best_dpa_row['Analista']}</div>
                    <div class="p-detail">DPA: {best_dpa_row['DPA %']:.1f}%</div>
                </div>""", unsafe_allow_html=True)
    st.markdown("")


def render_fora_equipe_madrugada(
    resumo_df: "pd.DataFrame",
    expanded: bool = False,
    ganhos_label: str = "Ganhos",
    perdas_label: str = "Perdas",
    pct_label: str = "Aderência %",
    caption: str = "Analistas que aparecem nesta planilha mas **não fazem parte da equipe monitorada**.",
) -> None:
    """Renderiza a seção de analistas externos em qualquer aba (admin only)."""
    if resumo_df is None or resumo_df.empty:
        return
    total_vol = int(resumo_df["Volume"].sum())
    total_ganhos = int(resumo_df["Ganhos"].sum())
    total_perdas = int(resumo_df["Perdas"].sum())
    n_logins = len(resumo_df)
    total_pct = (total_ganhos / total_vol * 100) if total_vol > 0 else 0.0
    with st.expander(
        f"👥 Analistas Externos — {n_logins} login(s) · "
        f"Vol: {total_vol:,} · {ganhos_label}: {total_ganhos:,} · {perdas_label}: {total_perdas:,} · "
        f"{pct_label}: {total_pct:.1f}%",
        expanded=expanded,
    ):
        st.caption(caption)
        ke1, ke2, ke3, ke4, ke5 = st.columns(5)
        with ke1:
            st.markdown(kpi_card("Logins", str(n_logins), "#8E44AD"), unsafe_allow_html=True)
        with ke2:
            st.markdown(kpi_card("Volume Total", f"{total_vol:,}", COR_INFO), unsafe_allow_html=True)
        with ke3:
            st.markdown(kpi_card(ganhos_label, f"{total_ganhos:,}", COR_SUCESSO), unsafe_allow_html=True)
        with ke4:
            st.markdown(kpi_card(perdas_label, f"{total_perdas:,}", COR_PERIGO), unsafe_allow_html=True)
        with ke5:
            pct_color = COR_SUCESSO if total_pct >= 90 else (COR_ALERTA if total_pct >= 70 else COR_PERIGO)
            st.markdown(kpi_card(pct_label, f"{total_pct:.1f}%", pct_color), unsafe_allow_html=True)
        tbl = resumo_df.copy()
        tbl.index = range(1, len(tbl) + 1)
        tbl.index.name = "#"
        tbl.columns = ["Login", "Volume", ganhos_label, perdas_label, pct_label]
        tbl["Login"] = tbl["Login"].map(_name_for_login)
        st.dataframe(
            tbl.style
                .format({pct_label: "{:.1f}"}, na_rep="—")
                .background_gradient(cmap="RdYlGn", subset=[pct_label], vmin=0, vmax=100)
                .background_gradient(cmap="Purples", subset=["Volume"])
                .background_gradient(cmap="Greens", subset=[ganhos_label])
                .background_gradient(cmap="Reds", subset=[perdas_label]),
            use_container_width=True,
        )


def render_fora_equipe_dpa(df_dpa_ext: "pd.DataFrame", expanded: bool = False) -> None:
    """Renderiza a seção de analistas externos na aba DPA (Login + DPA %)."""
    if df_dpa_ext is None or df_dpa_ext.empty:
        return
    n_logins = len(df_dpa_ext)
    avg_dpa = df_dpa_ext["DPA_Pct"].mean()
    with st.expander(
        f"👥 Analistas Externos — DPA · {n_logins} login(s) · Média DPA: {avg_dpa:.1f}%",
        expanded=expanded,
    ):
        st.caption("Analistas que aparecem na planilha DPA mas **não fazem parte da equipe monitorada**.")
        ke1, ke2 = st.columns(2)
        with ke1:
            st.markdown(kpi_card("Logins", str(n_logins), "#8E44AD"), unsafe_allow_html=True)
        with ke2:
            dpa_c = COR_SUCESSO if avg_dpa >= 80 else (COR_ALERTA if avg_dpa >= 60 else COR_PERIGO)
            st.markdown(kpi_card("DPA Médio", f"{avg_dpa:.1f}%", dpa_c), unsafe_allow_html=True)
        tbl = df_dpa_ext[["Login", "DPA_Pct"]].copy()
        tbl.columns = ["Login", "DPA %"]
        tbl["Login"] = tbl["Login"].map(_name_for_login)
        tbl.index = range(1, len(tbl) + 1)
        tbl.index.name = "#"
        st.dataframe(
            tbl.style
                .format({"DPA %": "{:.1f}"}, na_rep="—")
                .background_gradient(cmap="RdYlGn", subset=["DPA %"], vmin=50, vmax=100),
            use_container_width=True,
        )


# =====================================================
# HEADER
# =====================================================
st.markdown(f"""
<div class="main-header">
    <h1>📊 Dashboard de Produtividade — COP Rede</h1>
    <p>Análise de produtividade da equipe · Regional <strong>{REGIONAL_FILTRO}</strong></p>
</div>
""", unsafe_allow_html=True)


# =====================================================
# AUTENTICAÇÃO
# =====================================================
if not st.session_state.get("_users_initialized"):
    ensure_users_initialized(ALL_TRACKED_IDS)
    st.session_state["_users_initialized"] = True

if not st.session_state.get("authenticated"):
    show_login_page()
    st.stop()

if st.session_state.get("must_change_password"):
    show_change_password_page(st.session_state["user_matricula"])
    st.stop()

# ── Flash messages (one-shot after rerun) ────────────────────────────────
_flash = st.session_state.pop("_flash_success", None)
if _flash:
    st.success(_flash)

_auth_user      = st.session_state["user_matricula"]   # matricula UPPER
_is_super_admin = (_auth_user == AUTH_ADMIN_ID)
_is_coord       = (_auth_user in COORD_IDS)
_is_admin       = _is_super_admin or _is_coord

# Determinar nome e matricula canônica do usuário
from src.config import LOGIN_ALIASES as _LOGIN_ALIASES
_user_canonical = _LOGIN_ALIASES.get(_auth_user, _auth_user)  # resolve alias

# ─── Pralon: super-observador com escopo próprio ──────────────────────────
_is_pralon = (_auth_user == _PRALON_ID)

# ─── Evandro: super-observador das 3 equipes empresariais ─────────────────
_is_evandro = (_auth_user == _EVANDRO_ID)

# ─── Sub-admins Empresariais (veem ETIT, não veem Indicadores Residencial) ─
_is_sub_admin_emp = (_auth_user in SUB_ADMIN_EMP_IDS)
_sub_admin_emp_team_ids = {
    m.upper()
    for aid in SUB_ADMIN_EMP_IDS
    for m in COORD_ANALYSTS_MAP.get(aid, set())
}
_is_sub_admin_emp_member = (_auth_user in _sub_admin_emp_team_ids)

# Todos os usuários carregam os arquivos salvos do R2/disco ao iniciar a sessão.
# Para o super admin (ADMIN) isso evita ter que re-fazer o upload após fechar
# e reabrir o portal — o session_state é volátil, mas o R2/disco persiste.
# O spinner só aparece na primeira carga da sessão (quando ainda não há dados);
# nas demais interações `load_saved_files_to_session` retorna rapidamente sem rede.
if "uploaded_bytes" not in st.session_state:
    with st.spinner("Carregando seus dados..."):
        load_saved_files_to_session()
else:
    load_saved_files_to_session()

if _is_pralon:
    # Após carregar do R2, eleva para super-admin (acesso a upload e visão gerencial).
    # Os dados serão filtrados para PRALON_ANALYSTS logo adiante.
    _is_super_admin  = True
    _is_coord        = False
    _is_admin        = True
_is_pralon_todos = _is_pralon  # sinaliza para pular o filtro de Madrugada

if _is_evandro:
    # Evandro: super-observador das equipes empresariais.
    # Eleva para super-admin; dados serão filtrados por escopo logo adiante.
    _is_super_admin = True
    _is_coord       = False
    _is_admin       = True
# ──────────────────────────────────────────────────────────────────────────

if not _is_admin:
    # Identifica nome do analista
    _user_row = BASE_EQUIPE[BASE_EQUIPE["Matricula"].str.upper() == _user_canonical.upper()]
    if not _user_row.empty:
        _user_nome = primeiro_nome(_user_row.iloc[0]["Nome"])
    else:
        _coord_name = COORD_ANALYSTS_NAMES.get(_user_canonical.upper())
        _user_nome = primeiro_nome(_coord_name) if _coord_name else _auth_user

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand banner
    st.markdown("""<div class="sidebar-brand">
        <div class="sidebar-brand-logo">COP Rede</div>
        <div class="sidebar-brand-sub">Dashboard de Produtividade · Claro</div>
    </div>""", unsafe_allow_html=True)

    # User card
    if _is_pralon:
        st.markdown("""<div class="sidebar-user-card">
            <div class="sidebar-user-name">Pralon</div>
            <div class="sidebar-user-role">Super Admin · Luiz + Vinícius + Nelson (Residencial)</div>
        </div>""", unsafe_allow_html=True)
    elif _is_evandro:
        st.markdown("""<div class="sidebar-user-card">
            <div class="sidebar-user-name">Evandro</div>
            <div class="sidebar-user-role">Super Admin · Alexandre + Patrick + Thiago Paroli + Nelson (Empresarial)</div>
        </div>""", unsafe_allow_html=True)
    elif _is_super_admin:
        st.markdown("""<div class="sidebar-user-card">
            <div class="sidebar-user-name">Nelson</div>
            <div class="sidebar-user-role">Admin · Visão Madrugada · equipe fixa</div>
        </div>""", unsafe_allow_html=True)
    elif _is_sub_admin_emp:
        st.markdown(f"""<div class="sidebar-user-card">
            <div class="sidebar-user-name">Admin Empresarial</div>
            <div class="sidebar-user-role">{_auth_user} · Visão da equipe · sem Residencial</div>
        </div>""", unsafe_allow_html=True)
    elif _is_coord:
        st.markdown(f"""<div class="sidebar-user-card">
            <div class="sidebar-user-name">Coordenador</div>
            <div class="sidebar-user-role">{_auth_user} · Visão da equipe</div>
        </div>""", unsafe_allow_html=True)
    else:
        _setor_label = _user_row.iloc[0]["Setor"] if not _user_row.empty else ""
        st.markdown(f"""<div class="sidebar-user-card">
            <div class="sidebar-user-name">👤 {_user_nome}</div>
            <div class="sidebar-user-role">{_auth_user} · {_setor_label}</div>
        </div>""", unsafe_allow_html=True)

    # Theme toggle
    _theme_icon = "☀️ Modo Claro" if st.session_state["dark_mode"] else "🌙 Modo Escuro"
    if st.button(_theme_icon, use_container_width=True, key="btn_theme"):
        st.session_state["dark_mode"] = not st.session_state["dark_mode"]
        st.rerun()

    # Admin navigation: Gerenciar Dados
    if _is_admin:
        _upload_label = "📊 Dashboard" if st.session_state["cop_page"] == "upload" else "📥 Gerenciar Dados"
        if st.button(_upload_label, use_container_width=True, key="btn_upload_nav"):
            st.session_state["cop_page"] = "dashboard" if st.session_state["cop_page"] == "upload" else "upload"
            st.rerun()

    # Logout
    if st.button("🚪 Sair", use_container_width=True, key="btn_logout"):
        for _k in ["authenticated", "user_matricula", "must_change_password"]:
            st.session_state.pop(_k, None)
        st.rerun()
    st.markdown("---")

# =====================================================
# UPLOAD — Página Exclusiva (admin only)
# =====================================================
if _is_admin and st.session_state["cop_page"] == "upload":

    # Aviso quando R2 não está configurado (arquivos e senhas serão perdidos no próximo deploy)
    if not _storage.r2_available():
        st.warning(
            "⚠️ **Armazenamento em nuvem (R2) não configurado.** "
            "Arquivos enviados e senhas serão perdidos após cada atualização/redeploy. "
            "Configure as variáveis `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID` e `R2_SECRET_ACCESS_KEY` "
            "no painel do Streamlit Cloud (Secrets) ou Railway para persistência permanente.",
            icon="⚠️",
        )

    # ── Hero header ──────────────────────────────────────────────────────────
    _ld = {k: k in st.session_state for k in [
        "uploaded_bytes", "uploaded_etit_bytes", "uploaded_res_ind_bytes",
        "uploaded_toa_bytes", "uploaded_dpa_bytes", "uploaded_fech_sir_bytes",
        "uploaded_chat_toa_bytes",
    ]}
    _loaded_n = sum(_ld.values())
    _n_emp = len(BASE_EQUIPE[BASE_EQUIPE["Setor"] == "EMPRESARIAL"])
    _n_res = len(BASE_EQUIPE[BASE_EQUIPE["Setor"] == "RESIDENCIAL"])

    st.markdown(
        f'<div class="upload-page-hero">'
        f'<h2>📥 Gerenciamento de Dados</h2>'
        f'<p>{_loaded_n} de 6 planilhas carregadas &nbsp;·&nbsp; '
        f'Equipe: {len(EQUIPE_IDS)} analistas ({_n_emp} Emp. · {_n_res} Res.)</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Go to dashboard button (only when main file loaded) ──────────────────
    if _ld["uploaded_bytes"]:
        if st.button("📊 Ir para o Dashboard →", type="primary"):
            st.session_state["cop_page"] = "dashboard"
            st.rerun()
        st.markdown("")

    # ── Upload cards — row 1 ──────────────────────────────────────────────────
    _c1, _c2, _c3 = st.columns(3)

    def _status_html(key: str, name: str) -> str:
        if key in st.session_state:
            fname = st.session_state.get(key + "_name", "arquivo carregado")
            return (f'<div class="upload-card-status-ok">✅ {fname}</div>')
        return f'<div class="upload-card-status-no">⬜ Aguardando upload</div>'

    with _c1:
        st.markdown(
            '<div class="upload-card">'
            '<div class="upload-card-icon">📊</div>'
            '<div class="upload-card-title">Produtividade</div>'
            '<div class="upload-card-desc">Analítico de Produtividade COP Rede — base principal do dashboard.</div>'
            + _status_html("uploaded_bytes", "uploaded_bytes") +
            '</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Selecionar arquivo", type=["xlsx", "xls"], key="upload_prod", label_visibility="collapsed")

    with _c2:
        if _is_super_admin or _is_sub_admin_emp:
            st.markdown(
                '<div class="upload-card">'
                '<div class="upload-card-icon">🏢</div>'
                '<div class="upload-card-title">ETIT Empresarial</div>'
                '<div class="upload-card-desc">Analítico Empresarial — ETIT POR EVENTO. Opcional.</div>'
                + _status_html("uploaded_etit_bytes", "uploaded_etit_bytes") +
                '</div>', unsafe_allow_html=True)
            uploaded_etit = st.file_uploader(
                "Selecionar arquivo", type=["xlsx", "xls"], key="upload_etit", label_visibility="collapsed")
        else:
            uploaded_etit = None

    with _c3:
        st.markdown(
            '<div class="upload-card">'
            '<div class="upload-card-icon">🏠</div>'
            '<div class="upload-card-title">Indicadores Residencial</div>'
            '<div class="upload-card-desc">ETIT Fibra HFC, ETIT GPON, Reprog. GPON, Assertividade. Opcional.</div>'
            + _status_html("uploaded_res_ind_bytes", "uploaded_res_ind_bytes") +
            '</div>', unsafe_allow_html=True)
        uploaded_res_ind = st.file_uploader(
            "Selecionar arquivo", type=["xlsx", "xls"], key="upload_res_ind", label_visibility="collapsed")

    # ── Upload cards — row 2 ──────────────────────────────────────────────────
    st.markdown("")
    _c4, _c5, _c6 = st.columns(3)

    with _c4:
        st.markdown(
            '<div class="upload-card">'
            '<div class="upload-card-icon">📋</div>'
            '<div class="upload-card-title">Indicadores TOA</div>'
            '<div class="upload-card-desc">Tarefas Canceladas e Tempo de Validação do Formulário. Opcional.</div>'
            + _status_html("uploaded_toa_bytes", "uploaded_toa_bytes") +
            '</div>', unsafe_allow_html=True)
        uploaded_toa = st.file_uploader(
            "Selecionar arquivo", type=["xlsx", "xls"], key="upload_toa", label_visibility="collapsed")

    with _c5:
        st.markdown(
            '<div class="upload-card">'
            '<div class="upload-card-icon">📈</div>'
            '<div class="upload-card-title">Ocupação DPA 2026</div>'
            '<div class="upload-card-desc">Planilha DPA com abas Consolidado e Analistas. Mês detectado automaticamente. Opcional.</div>'
            + _status_html("uploaded_dpa_bytes", "uploaded_dpa_bytes") +
            '</div>', unsafe_allow_html=True)
        uploaded_dpa = st.file_uploader(
            "Selecionar arquivo", type=["xlsx", "xls"], key="upload_dpa", label_visibility="collapsed")

    with _c6:
        st.markdown(
            '<div class="upload-card">'
            '<div class="upload-card-icon">🔗</div>'
            '<div class="upload-card-title">Fechamento TOA × SIR</div>'
            '<div class="upload-card-desc">Assertividade de fechamentos — Madrugada, mês mais recente detectado automaticamente. Opcional.</div>'
            + _status_html("uploaded_fech_sir_bytes", "uploaded_fech_sir_bytes") +
            '</div>', unsafe_allow_html=True)
        uploaded_fech_sir = st.file_uploader(
            "Selecionar arquivo", type=["xlsx", "xls"], key="upload_fech_sir", label_visibility="collapsed")

    # ── Upload cards — row 3 ──────────────────────────────────────────────────
    st.markdown("")
    _c7, _c8, _c9 = st.columns(3)

    with _c7:
        st.markdown(
            '<div class="upload-card">'
            '<div class="upload-card-icon">💬</div>'
            '<div class="upload-card-title">Chat TOA</div>'
            '<div class="upload-card-desc">Analítico Chat TOA — TMA (meta ≤ 10 min). Mês detectado automaticamente. Opcional.</div>'
            + _status_html("uploaded_chat_toa_bytes", "uploaded_chat_toa_bytes") +
            '</div>', unsafe_allow_html=True)
        uploaded_chat_toa = st.file_uploader(
            "Selecionar arquivo", type=["xlsx", "xls"], key="upload_chat_toa", label_visibility="collapsed")

    with _c8:
        st.markdown('<div class="upload-card"><div class="upload-card-desc" style="color:var(--text3);font-style:italic;">— slot reservado —</div></div>', unsafe_allow_html=True)

    with _c9:
        st.markdown('<div class="upload-card"><div class="upload-card-desc" style="color:var(--text3);font-style:italic;">— slot reservado —</div></div>', unsafe_allow_html=True)

    # ── Persist to session_state + R2 ────────────────────────────────────────
    _saved_ids = st.session_state.setdefault("_r2_saved_ids", {})  # dict key→md5
    for key_name, file_obj in [
        ("uploaded_bytes",           uploaded_file),
        ("uploaded_etit_bytes",      uploaded_etit),
        ("uploaded_res_ind_bytes",   uploaded_res_ind),
        ("uploaded_toa_bytes",       uploaded_toa),
        ("uploaded_dpa_bytes",       uploaded_dpa),
        ("uploaded_fech_sir_bytes",  uploaded_fech_sir),
        ("uploaded_chat_toa_bytes",  uploaded_chat_toa),
    ]:
        if file_obj is not None:
            _bytes = file_obj.getvalue()
            _md5 = hashlib.md5(_bytes).hexdigest()
            st.session_state[key_name]           = _bytes
            st.session_state[key_name + "_name"] = file_obj.name
            if _saved_ids.get(key_name) != _md5:  # conteúdo realmente mudou
                save_uploaded_file(key_name, _bytes)
                _saved_ids[key_name] = _md5
                # Invalida cache de parse para forçar reprocessamento com código atual.
                # Necessário pois @st.cache_data é global e persiste entre sessões.
                _parse_cache_map = {
                    "uploaded_bytes":          _parse_produtividade,
                    "uploaded_etit_bytes":     _parse_etit,
                    "uploaded_res_ind_bytes":  _parse_res_ind,
                    "uploaded_toa_bytes":      _parse_toa,
                    "uploaded_dpa_bytes":      _parse_dpa,
                    "uploaded_fech_sir_bytes": _parse_fech_sir,
                    "uploaded_chat_toa_bytes": _parse_chat_toa,
                }
                if key_name in _parse_cache_map:
                    _parse_cache_map[key_name].clear()
                if key_name == "uploaded_dpa_bytes":
                    _parse_fora_equipe_dpa.clear()

    # ── Stats bar ─────────────────────────────────────────────────────────────
    st.markdown("")
    st.markdown(
        f'<div class="upload-stats-bar">'
        f'<div class="upload-stats-item"><div class="upload-stats-val">{_loaded_n}/7</div><div class="upload-stats-lbl">Planilhas</div></div>'
        f'<div class="upload-stats-item"><div class="upload-stats-val">{len(EQUIPE_IDS)}</div><div class="upload-stats-lbl">Analistas</div></div>'
        f'<div class="upload-stats-item"><div class="upload-stats-val">{_n_emp}</div><div class="upload-stats-lbl">Empresarial</div></div>'
        f'<div class="upload-stats-item"><div class="upload-stats-val">{_n_res}</div><div class="upload-stats-lbl">Residencial</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.expander("📋 Analistas monitorados"):
        st.dataframe(BASE_EQUIPE, use_container_width=True, hide_index=True)

    if not _ld["uploaded_bytes"]:
        st.info("⬆️  Faça upload da planilha de **Produtividade** para habilitar o Dashboard.")

    # ── Gerenciamento de senhas ───────────────────────────────────────────────
    # Super admin: gerencia todos. Coordenador: gerencia apenas a própria equipe.
    if _is_super_admin or _is_coord:
        @st.dialog("Confirmar Reset de Senha")
        def _confirm_reset_dialog():
            target = st.session_state.get("_confirm_reset_target")
            if not target:
                st.warning("Nenhum analista selecionado.")
                return
            st.markdown(
                f"Tem certeza de que deseja resetar a senha de "
                f"**{target['nome']}** (matrícula `{target['mat']}`)?"
            )
            st.caption("A nova senha será `claro123` e o usuário deverá trocá-la no próximo acesso.")
            _c1, _c2 = st.columns(2)
            with _c1:
                if st.button("✅ Confirmar", use_container_width=True, type="primary",
                             key="dlg_reset_confirm"):
                    reset_user_password(target["mat"])
                    st.session_state["_flash_success"] = (
                        f"✅ Senha de {target['nome']} ({target['mat']}) resetada para 'claro123'."
                    )
                    st.toast(f"Senha de {target['nome']} resetada", icon="🔑")
                    st.session_state.pop("_confirm_reset_target", None)
                    st.rerun()
            with _c2:
                if st.button("❌ Cancelar", use_container_width=True, key="dlg_reset_cancel"):
                    st.session_state.pop("_confirm_reset_target", None)
                    st.rerun()

        def _render_reset_row(mat: str, nome: str):
            _rc1, _rc2, _rc3 = st.columns([4, 2, 2])
            with _rc1:
                st.markdown(f"**{nome}**")
            with _rc2:
                st.text(mat)
            with _rc3:
                if st.button("🔑 Resetar", key=f"btn_reset_{mat}",
                             use_container_width=True):
                    st.session_state["_confirm_reset_target"] = {"mat": mat, "nome": nome}
                    _confirm_reset_dialog()

    if _is_super_admin:
        @st.dialog("Confirmar Reset em Massa")
        def _confirm_bulk_reset_dialog():
            st.markdown(
                "Esta ação vai **resetar a senha de TODOS os analistas** para `claro123`. "
                "Todos precisarão trocar a senha no próximo acesso."
            )
            st.warning("⚠️ Ação irreversível — o admin atual não é afetado.")
            _c1, _c2 = st.columns(2)
            with _c1:
                if st.button("✅ Confirmar Reset em Massa", use_container_width=True,
                             type="primary", key="dlg_bulk_reset_confirm"):
                    _n_reset = reset_non_admin_passwords(preserve_ids={"ADMIN"})
                    st.session_state["_flash_success"] = (
                        f"✅ {_n_reset} senhas resetadas para 'claro123'."
                    )
                    st.toast(f"{_n_reset} senhas resetadas", icon="🔑")
                    st.rerun()
            with _c2:
                if st.button("❌ Cancelar", use_container_width=True, key="dlg_bulk_reset_cancel"):
                    st.rerun()

        st.markdown("---")
        st.markdown("### 🔑 Gerenciamento de Senhas dos Analistas")
        _col_reset_all, _col_repair = st.columns([1, 1])
        with _col_reset_all:
            if st.button("🔄 Resetar senhas de TODOS os analistas",
                         use_container_width=True, key="btn_reset_all"):
                _confirm_bulk_reset_dialog()
        with _col_repair:
            if st.button("🛠️ Reparar inicialização de senhas",
                         use_container_width=True, key="btn_repair_init",
                         help="Cria entradas faltantes em passwords.json para toda matrícula monitorada, com senha claro123."):
                try:
                    _n_added = ensure_users_initialized(ALL_TRACKED_IDS)
                    if _n_added > 0:
                        st.success(
                            f"✅ {_n_added} matrícula(s) inicializada(s) com senha padrão `claro123`."
                        )
                    else:
                        st.info("Nenhuma matrícula estava faltando — passwords.json já está completo.")
                except RuntimeError as _e:
                    st.error(f"❌ {_e}")

        _missing = list_missing_tracked_ids(ALL_TRACKED_IDS)
        if _missing:
            st.warning(
                f"⚠️ {len(_missing)} matrícula(s) monitorada(s) sem entrada em passwords.json "
                f"(não conseguem logar). Clique em **Reparar inicialização** acima. "
                f"Faltando: {', '.join(_missing)}"
            )

        st.markdown("#### Reset individual por analista")

        # Equipe fixa (Nelson)
        with st.expander(f"Equipe Nelson ({len(BASE_EQUIPE)} analistas)", expanded=True):
            for _eq_row in BASE_EQUIPE.itertuples():
                _render_reset_row(_eq_row.Matricula, _eq_row.Nome)

        # Equipes dos coordenadores (LUIZ, VINICIUS) + sub-admins empresariais
        _COORD_LABELS = {
            "LUIZ":     "Equipe LUIZ",
            "VINICIUS": "Equipe VINICIUS",
            "N0150817": "Equipe Alexandre Sampaio (N0150817)",
            "N5768308": "Equipe Patrick Sarmento (N5768308)",
            "TPAROLI":  "Equipe Thiago Paroli (TPAROLI)",
        }
        for _coord_id, _label in _COORD_LABELS.items():
            _mats = sorted(
                COORD_ANALYSTS_MAP.get(_coord_id, set()),
                key=lambda m: COORD_ANALYSTS_NAMES.get(m, m),
            )
            if not _mats:
                continue
            with st.expander(f"{_label} ({len(_mats)} analistas)"):
                for _mat in _mats:
                    _nome = COORD_ANALYSTS_NAMES.get(_mat, _mat)
                    _render_reset_row(_mat, _nome)

    elif _is_coord:
        # Coordenador: reset individual restrito aos seus próprios analistas
        _my_mats = sorted(
            COORD_ANALYSTS_MAP.get(_auth_user, set()),
            key=lambda m: COORD_ANALYSTS_NAMES.get(m, m),
        )
        if _my_mats:
            st.markdown("---")
            st.markdown("### 🔑 Gerenciamento de Senhas da Sua Equipe")
            st.caption(
                f"Você pode resetar a senha dos {len(_my_mats)} analista(s) da sua equipe. "
                "A nova senha será `claro123` e o analista precisará trocá-la no próximo acesso."
            )
            for _mat in _my_mats:
                _nome = COORD_ANALYSTS_NAMES.get(_mat, _mat)
                _render_reset_row(_mat, _nome)

    st.stop()

elif _is_admin:
    # Dashboard mode: sem dados → redireciona para página de upload
    if "uploaded_bytes" not in st.session_state:
        st.session_state["cop_page"] = "upload"
        st.rerun()

else:
    # ── Analista: carrega dados do R2 (enviados pelo admin) ──────────────────
    if "uploaded_bytes" not in st.session_state:
        st.markdown("---")
        if not saved_files_exist():
            st.warning(
                "⏳ Os dados ainda não foram disponibilizados. "
                "Aguarde o administrador fazer o upload das planilhas."
            )
        else:
            st.error(
                "Não foi possível carregar os dados. "
                "Recarregue a página (F5) para tentar novamente."
            )
        st.stop()


# =====================================================
# PROCESSAR DADOS — Produtividade
# =====================================================
try:
    df = _parse_produtividade(st.session_state["uploaded_bytes"])
    if df.empty:
        st.error("Nenhum analista da equipe encontrado na planilha de produtividade.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao processar a planilha de produtividade: {e}")
    with st.expander("Detalhes do erro"):
        st.code(traceback.format_exc())
    st.stop()


# =====================================================
# PROCESSAR DADOS — ETIT (opcional)
# =====================================================
df_etit = pd.DataFrame()
etit_loaded = False

if "uploaded_etit_bytes" in st.session_state:
    try:
        df_etit = _parse_etit(st.session_state["uploaded_etit_bytes"])
        etit_loaded = not df_etit.empty
        if not etit_loaded:
            st.warning("Nenhum analista da equipe encontrado nos dados ETIT POR EVENTO.")
    except Exception as e:
        st.warning(f"Erro ao processar planilha ETIT: {e}")
        with st.expander("Detalhes do erro"):
            st.code(traceback.format_exc())


# =====================================================
# PROCESSAR DADOS — Indicadores Residencial (opcional)
# =====================================================
df_res_ind = pd.DataFrame()
res_ind_loaded = False

if "uploaded_res_ind_bytes" in st.session_state:
    try:
        df_res_ind = _parse_res_ind(st.session_state["uploaded_res_ind_bytes"])
        res_ind_loaded = not df_res_ind.empty
        if not res_ind_loaded:
            st.warning("Nenhum dado dos indicadores selecionados encontrado na planilha.")
    except Exception as e:
        st.warning(f"Erro ao processar planilha de Indicadores Residencial: {e}")
        with st.expander("Detalhes do erro"):
            st.code(traceback.format_exc())


# =====================================================
# PROCESSAR DADOS — Ocupação DPA (opcional)
# =====================================================
df_dpa = pd.DataFrame()
dpa_mes_info = {}
dpa_loaded = False

if "uploaded_dpa_bytes" in st.session_state:
    try:
        df_dpa, dpa_mes_info = _parse_dpa(st.session_state["uploaded_dpa_bytes"])
        dpa_loaded = not df_dpa.empty
        if not dpa_loaded:
            st.warning("Nenhum analista da equipe encontrado na planilha de Ocupação DPA.")
    except Exception as e:
        st.warning(f"Erro ao processar planilha de Ocupação DPA: {e}")
        with st.expander("Detalhes do erro"):
            st.code(traceback.format_exc())


# =====================================================
# PROCESSAR DADOS — Indicadores TOA (opcional)
# =====================================================
df_toa = pd.DataFrame()
toa_loaded = False
toa_anomes = None

if "uploaded_toa_bytes" in st.session_state:
    try:
        df_toa = _parse_toa(st.session_state["uploaded_toa_bytes"])
        toa_loaded = not df_toa.empty
        if toa_loaded and "ANOMES" in df_toa.columns:
            toa_anomes = int(df_toa["ANOMES"].max())
        if not toa_loaded:
            st.warning("Nenhum analista da equipe encontrado nos Indicadores TOA.")
    except Exception as e:
        st.warning(f"Erro ao processar planilha de Indicadores TOA: {e}")
        with st.expander("Detalhes do erro"):
            st.code(traceback.format_exc())


# =====================================================
# PROCESSAR DADOS — Fechamento TOA x SIR (opcional)
# =====================================================
df_fech_sir = pd.DataFrame()
fech_sir_loaded = False
fech_sir_anomes = None

if "uploaded_fech_sir_bytes" in st.session_state:
    try:
        if _is_evandro:
            _fech_team_ids = (
                COORD_ANALYSTS_MAP.get("N0150817", set())
                | COORD_ANALYSTS_MAP.get("N5768308", set())
                | COORD_ANALYSTS_MAP.get("TPAROLI", set())
                | EQUIPE_IDS
            )
            _fech_turnos = {"Madrugada", "Manhã", "Tarde"}
        elif _is_pralon:
            _fech_team_ids = set(PRALON_ANALYSTS)
            _fech_turnos = {"Madrugada", "Manhã", "Tarde"}
        else:
            _fech_team_ids = EQUIPE_IDS
            _fech_turnos = {"Madrugada"}
        _fech_team_key = tuple(sorted(_fech_team_ids))
        _fech_turnos_key = tuple(sorted(_fech_turnos))
        df_fech_sir = _parse_fech_sir(
            st.session_state["uploaded_fech_sir_bytes"],
            team_ids_key=_fech_team_key,
            turnos_key=_fech_turnos_key,
        )
        fech_sir_loaded = not df_fech_sir.empty
        if fech_sir_loaded and FECH_SIR_COL_ANOMES in df_fech_sir.columns:
            fech_sir_anomes = int(df_fech_sir[FECH_SIR_COL_ANOMES].max())
        if not fech_sir_loaded:
            st.warning("⚠️ Fech. TOA x SIR: nenhum analista da equipe encontrado.")
    except Exception as e:
        st.error(f"❌ Erro ao processar Fechamento TOA x SIR: {e}")
        with st.expander("Detalhes do erro Fech. TOA x SIR", expanded=True):
            st.code(traceback.format_exc())

# =====================================================
# PROCESSAR DADOS — Chat TOA (opcional)
# =====================================================
df_chat_toa = pd.DataFrame()
chat_toa_loaded = False
chat_toa_anomes = None

if "uploaded_chat_toa_bytes" in st.session_state:
    try:
        df_chat_toa = _parse_chat_toa(st.session_state["uploaded_chat_toa_bytes"])
        chat_toa_loaded = not df_chat_toa.empty
        if chat_toa_loaded and CHAT_TOA_COL_ANOMES in df_chat_toa.columns:
            chat_toa_anomes = int(df_chat_toa[CHAT_TOA_COL_ANOMES].max())
        if not chat_toa_loaded:
            st.warning("Nenhum analista da equipe encontrado no Chat TOA.")
    except Exception as e:
        st.warning(f"Erro ao processar Chat TOA: {e}")
        with st.expander("Detalhes do erro"):
            st.code(traceback.format_exc())

# =====================================================
# PROCESSAR DADOS — Analistas Externos (Madrugada) — apenas admin
# =====================================================
df_fora_equipe_madrugada = pd.DataFrame()
if _is_super_admin and not _is_evandro and "uploaded_fech_sir_bytes" in st.session_state:
    try:
        df_fora_equipe_madrugada = _parse_fora_equipe_fech_sir(
            st.session_state["uploaded_fech_sir_bytes"]
        )
    except Exception:
        df_fora_equipe_madrugada = pd.DataFrame()

# Resumo pré-computado — Fechamento TOA x SIR (aba Madrugada)
_resumo_fora_equipe = fora_equipe_resumo_por_login(df_fora_equipe_madrugada) if _is_super_admin else pd.DataFrame()

# Analistas externos para coordenadores — mesmos logins do admin, mas turnos 06:00–21:59
_resumo_fora_equipe_coord = pd.DataFrame()
if _is_coord and "uploaded_fech_sir_bytes" in st.session_state:
    try:
        _df_fora_coord_raw = _parse_fora_equipe_fech_sir_coord(
            st.session_state["uploaded_fech_sir_bytes"]
        )
        _resumo_fora_equipe_coord = fora_equipe_resumo_por_login(_df_fora_coord_raw)
    except Exception:
        _resumo_fora_equipe_coord = pd.DataFrame()

# =====================================================
# PROCESSAR DADOS EXTERNOS — por aba (apenas super admin)
# =====================================================
_resumo_fora_etit    = pd.DataFrame()
_resumo_fora_res       = {}   # dict {indicador: resumo_df}  — super admin (Madrugada)
_resumo_fora_res_coord = {}   # dict {indicador: resumo_df}  — coordenador (Diurno)
_resumo_fora_toa       = {}   # dict {indicador: resumo_df}

if _is_super_admin:
    if "uploaded_etit_bytes" in st.session_state:
        try:
            _df_fora_etit_raw = _parse_fora_equipe_etit(st.session_state["uploaded_etit_bytes"])
            _resumo_fora_etit = fora_equipe_resumo_etit(_df_fora_etit_raw)
        except Exception:
            pass

    # Residencial: analistas externos na Madrugada (22:00–05:59)
    if res_ind_loaded and not df_res_ind.empty:
        try:
            _resumo_fora_res = fora_equipe_resumo_res_por_indicador_adm(df_res_ind)
        except Exception:
            pass

    if "uploaded_toa_bytes" in st.session_state:
        try:
            _df_fora_toa_raw = _parse_fora_equipe_toa(st.session_state["uploaded_toa_bytes"])
            _resumo_fora_toa = fora_equipe_resumo_toa_por_indicador(_df_fora_toa_raw)
        except Exception:
            pass

if _is_coord:
    # Residencial: analistas da Madrugada — atividade diurna (06:00–21:59)
    if res_ind_loaded and not df_res_ind.empty:
        try:
            _resumo_fora_res_coord = fora_equipe_resumo_res_por_indicador_coord(df_res_ind)
        except Exception:
            pass

# =====================================================
# FILTRO MADRUGADA — super admin vê apenas analistas da equipe (EQUIPE_IDS)
# Os dados de analistas externos (coords) já foram capturados em _resumo_fora_*
# Pralon no modo "Todos" pula este filtro para ver todos os analistas.
# Evandro também pula: seu escopo abrange as 3 equipes empresariais + Nelson
# e é aplicado no filtro dedicado logo abaixo (FILTRO EVANDRO).
# =====================================================
if _is_super_admin and not _is_pralon_todos and not _is_evandro:
    _equipe_ids_upper = {e.upper() for e in EQUIPE_IDS}
    # Filtra dados para apenas a equipe Madrugada (EQUIPE_IDS).
    # NÃO altera as flags *_loaded para não mudar o número de abas entre renders
    # (o que causaria React error #185 — "Maximum update depth exceeded").
    if not df.empty and COL_LOGIN in df.columns:
        df = df[df[COL_LOGIN].str.upper().isin(_equipe_ids_upper)].copy()
    if etit_loaded and not df_etit.empty and ETIT_COL_LOGIN in df_etit.columns:
        df_etit = df_etit[df_etit[ETIT_COL_LOGIN].str.upper().isin(_equipe_ids_upper)].copy()
    if res_ind_loaded and not df_res_ind.empty:
        # Filtro estrito por matrícula da equipe — sem fallback por turno.
        # O fallback antigo "Turno == Madrugada" vazava analistas de Luiz/
        # Vinícius (que também trabalham Madrugada) para a visão do Nelson
        # quando o filtro por login retornava vazio em alguma fração dos dados
        # (ex.: linhas GPON com login não casando com EQUIPE_IDS).
        if RES_LOGIN in df_res_ind.columns:
            df_res_ind = df_res_ind[
                df_res_ind[RES_LOGIN].str.upper().isin(_equipe_ids_upper)
            ].copy()
        elif RES_COL_ID_MOSTRA in df_res_ind.columns:
            df_res_ind = df_res_ind[
                df_res_ind[RES_COL_ID_MOSTRA].astype(str).str.upper().isin(_equipe_ids_upper)
            ].copy()
        elif RES_COL_TURNO in df_res_ind.columns:
            df_res_ind = df_res_ind[df_res_ind[RES_COL_TURNO] == "Madrugada"].copy()
    if dpa_loaded and not df_dpa.empty and "Login" in df_dpa.columns:
        df_dpa = df_dpa[df_dpa["Login"].str.upper().isin(_equipe_ids_upper)].copy()
    if toa_loaded and not df_toa.empty and "LOGIN" in df_toa.columns:
        df_toa = df_toa[df_toa["LOGIN"].str.upper().isin(_equipe_ids_upper)].copy()
    if chat_toa_loaded and not df_chat_toa.empty and CHAT_TOA_COL_LOGIN in df_chat_toa.columns:
        df_chat_toa = df_chat_toa[df_chat_toa[CHAT_TOA_COL_LOGIN].str.upper().isin(_equipe_ids_upper)].copy()
    # df_fech_sir já filtrado pelo processador conforme escopo do perfil


# ─── Evandro: seletor de segmentação por equipe ───────────────────────────
_evandro_scope_ids: set | None = None
if _is_evandro:
    _SEG_TODOS    = "Todos (Alexandre + Patrick + Paroli + Nelson)"
    _SEG_ALEX     = "Alexandre Sampaio"
    _SEG_PATRICK  = "Patrick Sarmento"
    _SEG_THIAGO   = "Thiago Paroli"
    _SEG_NELSON   = "Nelson (Madrugada)"
    with st.sidebar:
        st.markdown('<div class="sidebar-section">Segmentação</div>', unsafe_allow_html=True)
        _evandro_seg = st.selectbox(
            "Equipe",
            options=[_SEG_TODOS, _SEG_ALEX, _SEG_PATRICK, _SEG_THIAGO, _SEG_NELSON],
            key="_evandro_seg_sel",
            label_visibility="collapsed",
        )
    _seg_key_map = {
        _SEG_ALEX:    "N0150817",
        _SEG_PATRICK: "N5768308",
        _SEG_THIAGO:  "TPAROLI",
        _SEG_NELSON:  "ADMIN",
    }
    if _evandro_seg in _seg_key_map:
        _evandro_scope_ids = {m.upper() for m in EVANDRO_ANALYSTS_MAP[_seg_key_map[_evandro_seg]]}
    else:
        _evandro_scope_ids = {m.upper() for m in EVANDRO_ANALYSTS}
# ──────────────────────────────────────────────────────────────────────────

# =====================================================
# CAPTURA DADOS DA EQUIPE (antes do filtro por matrícula)
# Usado para calcular médias de comparação para o usuário não-admin
# =====================================================
if not _is_admin:
    _df_team_full        = df.copy()
    _df_etit_team_full   = df_etit.copy()   if etit_loaded      else pd.DataFrame()
    _df_fech_sir_team_full = df_fech_sir.copy() if fech_sir_loaded else pd.DataFrame()
    _df_toa_team_full    = df_toa.copy()    if toa_loaded       else pd.DataFrame()
    _df_dpa_team_full    = df_dpa.copy()    if dpa_loaded       else pd.DataFrame()
    _df_chat_toa_team_full = df_chat_toa.copy() if chat_toa_loaded else pd.DataFrame()
else:
    _df_team_full = _df_etit_team_full = _df_fech_sir_team_full = None
    _df_toa_team_full = _df_dpa_team_full = _df_chat_toa_team_full = None

# =====================================================
# FILTRO POR LISTA DE ANALISTAS — coordenadores veem apenas sua equipe
# =====================================================
if _is_coord:
    _coord_mats = COORD_ANALYSTS_MAP.get(_auth_user.upper(), set())
    if _coord_mats:
        _coord_mats_upper = {m.upper() for m in _coord_mats}
        if not df.empty and COL_LOGIN in df.columns:
            df = df[df[COL_LOGIN].str.upper().isin(_coord_mats_upper)].copy()
        if etit_loaded and not df_etit.empty and ETIT_COL_LOGIN in df_etit.columns:
            df_etit = df_etit[df_etit[ETIT_COL_LOGIN].str.upper().isin(_coord_mats_upper)].copy()
            etit_loaded = not df_etit.empty
        if res_ind_loaded and not df_res_ind.empty:
            # Filtro estrito por matrícula do coord — sem fallback por turno.
            # Antes, o fallback (ex.: COORD_TURNOS_MAP[LUIZ] = {Manhã, Tarde})
            # incluía analistas de OUTROS coords que compartilham o mesmo
            # turno, vazando dados entre escopos. Filtragem por login é a
            # única forma confiável de garantir que cada coord só veja sua
            # equipe.
            if RES_LOGIN in df_res_ind.columns:
                df_res_ind = df_res_ind[
                    df_res_ind[RES_LOGIN].str.upper().isin(_coord_mats_upper)
                ].copy()
            elif RES_COL_ID_MOSTRA in df_res_ind.columns:
                df_res_ind = df_res_ind[
                    df_res_ind[RES_COL_ID_MOSTRA].astype(str).str.upper().isin(_coord_mats_upper)
                ].copy()
            res_ind_loaded = not df_res_ind.empty
        if dpa_loaded and not df_dpa.empty and "Login" in df_dpa.columns:
            df_dpa = df_dpa[df_dpa["Login"].str.upper().isin(_coord_mats_upper)].copy()
            dpa_loaded = not df_dpa.empty
        if toa_loaded and not df_toa.empty and "LOGIN" in df_toa.columns:
            df_toa = df_toa[df_toa["LOGIN"].str.upper().isin(_coord_mats_upper)].copy()
            toa_loaded = not df_toa.empty
        if fech_sir_loaded and not df_fech_sir.empty and FECH_SIR_COL_LOGIN in df_fech_sir.columns:
            df_fech_sir = df_fech_sir[df_fech_sir[FECH_SIR_COL_LOGIN].str.upper().isin(_coord_mats_upper)].copy()
            fech_sir_loaded = not df_fech_sir.empty
        if chat_toa_loaded and not df_chat_toa.empty and CHAT_TOA_COL_LOGIN in df_chat_toa.columns:
            df_chat_toa = df_chat_toa[df_chat_toa[CHAT_TOA_COL_LOGIN].str.upper().isin(_coord_mats_upper)].copy()
            chat_toa_loaded = not df_chat_toa.empty

# =====================================================
# FILTRO PRALON — restringe aos analistas do escopo de Pralon e desativa
# as abas de ETIT Empresarial e Fechamento TOA x SIR
# =====================================================
if _is_pralon:
    _pralon_ids_upper = {m.upper() for m in PRALON_ANALYSTS}
    if not df.empty and COL_LOGIN in df.columns:
        df = df[df[COL_LOGIN].str.upper().isin(_pralon_ids_upper)].copy()
    if res_ind_loaded and not df_res_ind.empty:
        if RES_LOGIN in df_res_ind.columns:
            df_res_ind = df_res_ind[df_res_ind[RES_LOGIN].str.upper().isin(_pralon_ids_upper)].copy()
        elif RES_COL_ID_MOSTRA in df_res_ind.columns:
            df_res_ind = df_res_ind[
                df_res_ind[RES_COL_ID_MOSTRA].astype(str).str.upper().isin(_pralon_ids_upper)
            ].copy()
        res_ind_loaded = not df_res_ind.empty
    if dpa_loaded and not df_dpa.empty and "Login" in df_dpa.columns:
        df_dpa = df_dpa[df_dpa["Login"].str.upper().isin(_pralon_ids_upper)].copy()
        dpa_loaded = not df_dpa.empty
    if toa_loaded and not df_toa.empty and "LOGIN" in df_toa.columns:
        df_toa = df_toa[df_toa["LOGIN"].str.upper().isin(_pralon_ids_upper)].copy()
        toa_loaded = not df_toa.empty
    if chat_toa_loaded and not df_chat_toa.empty and CHAT_TOA_COL_LOGIN in df_chat_toa.columns:
        df_chat_toa = df_chat_toa[df_chat_toa[CHAT_TOA_COL_LOGIN].str.upper().isin(_pralon_ids_upper)].copy()
        chat_toa_loaded = not df_chat_toa.empty
    # Pralon não vê ETIT Empresarial (equipes Residenciais)
    etit_loaded      = False
    df_etit          = pd.DataFrame()
    # Fechamento TOA x SIR — filtra pelos analistas do escopo de Pralon
    if fech_sir_loaded and not df_fech_sir.empty and FECH_SIR_COL_LOGIN in df_fech_sir.columns:
        df_fech_sir = df_fech_sir[
            df_fech_sir[FECH_SIR_COL_LOGIN].str.upper().isin(_pralon_ids_upper)
        ].copy()
        fech_sir_loaded = not df_fech_sir.empty

# =====================================================
# FILTRO EVANDRO — restringe ao escopo selecionado e desativa Indicadores Residencial
# =====================================================
if _is_evandro and _evandro_scope_ids is not None:
    if not df.empty and COL_LOGIN in df.columns:
        df = df[df[COL_LOGIN].str.upper().isin(_evandro_scope_ids)].copy()
    if etit_loaded and not df_etit.empty and ETIT_COL_LOGIN in df_etit.columns:
        df_etit = df_etit[df_etit[ETIT_COL_LOGIN].str.upper().isin(_evandro_scope_ids)].copy()
        etit_loaded = not df_etit.empty
    if dpa_loaded and not df_dpa.empty and "Login" in df_dpa.columns:
        df_dpa = df_dpa[df_dpa["Login"].str.upper().isin(_evandro_scope_ids)].copy()
        dpa_loaded = not df_dpa.empty
    if toa_loaded and not df_toa.empty and "LOGIN" in df_toa.columns:
        df_toa = df_toa[df_toa["LOGIN"].str.upper().isin(_evandro_scope_ids)].copy()
        toa_loaded = not df_toa.empty
    if fech_sir_loaded and not df_fech_sir.empty and FECH_SIR_COL_LOGIN in df_fech_sir.columns:
        df_fech_sir = df_fech_sir[df_fech_sir[FECH_SIR_COL_LOGIN].str.upper().isin(_evandro_scope_ids)].copy()
        fech_sir_loaded = not df_fech_sir.empty
    if chat_toa_loaded and not df_chat_toa.empty and CHAT_TOA_COL_LOGIN in df_chat_toa.columns:
        df_chat_toa = df_chat_toa[df_chat_toa[CHAT_TOA_COL_LOGIN].str.upper().isin(_evandro_scope_ids)].copy()
        chat_toa_loaded = not df_chat_toa.empty
    # Evandro não vê Indicadores Residencial (equipes empresariais)
    res_ind_loaded = False
    df_res_ind     = pd.DataFrame()

# =====================================================
# FILTRO SUB-ADMIN EMPRESARIAL — desativa a aba/dados de Indicadores Residencial
# para os sub-admins empresariais e para seus líderes e analistas
# =====================================================
if _is_sub_admin_emp or _is_sub_admin_emp_member:
    res_ind_loaded = False
    df_res_ind     = pd.DataFrame()

# =====================================================
# FILTRO POR MATRÍCULA — usuários não-admin veem apenas seus próprios dados
# =====================================================
if not _is_admin:
    _mat_up = _user_canonical.upper()

    # Produtividade
    if not df.empty and COL_LOGIN in df.columns:
        df = df[df[COL_LOGIN].str.upper() == _mat_up].copy()

    # ETIT
    if etit_loaded and not df_etit.empty and ETIT_COL_LOGIN in df_etit.columns:
        df_etit = df_etit[df_etit[ETIT_COL_LOGIN].str.upper() == _mat_up].copy()
        etit_loaded = not df_etit.empty

    # Residencial Indicadores — filtra por login unificado (RES_LOGIN)
    if res_ind_loaded and not df_res_ind.empty:
        if RES_LOGIN in df_res_ind.columns:
            df_res_ind = df_res_ind[df_res_ind[RES_LOGIN] == _mat_up].copy()
        elif RES_COL_ID_MOSTRA in df_res_ind.columns:
            df_res_ind = df_res_ind[df_res_ind[RES_COL_ID_MOSTRA].str.upper() == _mat_up].copy()
        elif "Nome" in df_res_ind.columns and not _user_row.empty:
            _nome_full = _user_row.iloc[0]["Nome"]
            df_res_ind = df_res_ind[df_res_ind["Nome"] == _nome_full].copy()
        res_ind_loaded = not df_res_ind.empty

    # DPA — filtra pela coluna Login
    if dpa_loaded and not df_dpa.empty and "Login" in df_dpa.columns:
        df_dpa = df_dpa[df_dpa["Login"].str.upper() == _mat_up].copy()
        dpa_loaded = not df_dpa.empty

    # TOA
    if toa_loaded and not df_toa.empty and "LOGIN" in df_toa.columns:
        df_toa = df_toa[df_toa["LOGIN"].str.upper() == _mat_up].copy()
        toa_loaded = not df_toa.empty

    # Fechamento TOA x SIR
    if fech_sir_loaded and not df_fech_sir.empty and FECH_SIR_COL_LOGIN in df_fech_sir.columns:
        df_fech_sir = df_fech_sir[df_fech_sir[FECH_SIR_COL_LOGIN].str.upper() == _mat_up].copy()
        fech_sir_loaded = not df_fech_sir.empty

    # Chat TOA
    if chat_toa_loaded and not df_chat_toa.empty and CHAT_TOA_COL_LOGIN in df_chat_toa.columns:
        df_chat_toa = df_chat_toa[df_chat_toa[CHAT_TOA_COL_LOGIN].str.upper() == _mat_up].copy()
        chat_toa_loaded = not df_chat_toa.empty

    if df.empty:
        st.warning("Nenhum dado encontrado para sua matrícula. Verifique com o administrador.")
        st.stop()

# =====================================================
# SIDEBAR - FILTROS
# =====================================================
with st.sidebar:
    st.markdown('<div class="sidebar-section">Filtros</div>', unsafe_allow_html=True)

    meses_disponiveis = sorted(df[COL_ANOMES].dropna().unique().tolist())
    meses_labels = df.drop_duplicates(COL_ANOMES).set_index(COL_ANOMES)[COL_MES].to_dict()

    # Inclui meses presentes nas outras bases (ETIT, Residencial) — eventos do
    # fim de mes podem ter ANOMES no mes seguinte e ficariam invisiveis se o
    # dropdown viesse so da produtividade.
    _MES_PT = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
    }
    def _label_anomes(v: int) -> str:
        s = str(int(v))
        if len(s) == 6:
            try:
                return f"{_MES_PT[int(s[4:6])]} ({s})"
            except (KeyError, ValueError):
                pass
        return s

    _extra_anomes: set[int] = set()
    for _src_df, _src_col in (
        (df_etit, ETIT_COL_ANOMES),
        (df_res_ind, RES_ANOMES),
    ):
        if not _src_df.empty and _src_col in _src_df.columns:
            _vals = pd.to_numeric(_src_df[_src_col], errors="coerce").dropna()
            for _v in _vals.unique():
                _extra_anomes.add(int(_v))

    _existing_ints = {int(m) for m in meses_disponiveis if pd.notna(m)}
    for _v in sorted(_extra_anomes - _existing_ints):
        meses_disponiveis.append(_v)
        meses_labels.setdefault(_v, _label_anomes(_v).split(" (")[0])
    meses_disponiveis = sorted(meses_disponiveis)

    # Default = mes vigente, restrito aos meses presentes na Produtividade —
    # essa e a base que alimenta a aba Ranking. Se cairmos num mes que so
    # existe em ETIT/Residencial, df_filtrado fica vazio e o Ranking some.
    _opcoes_periodo = ["Todos"] + meses_disponiveis
    _default_idx = 0
    _meses_prod = sorted({int(m) for m in df[COL_ANOMES].dropna().unique().tolist()})
    if _meses_prod:
        _hoje = datetime.date.today()
        _candidatos = (
            _hoje.year * 100 + _hoje.month,
            f"{_hoje.year:04d}{_hoje.month:02d}",
        )
        _alvo = next((c for c in _candidatos if c in _meses_prod), _meses_prod[-1])
        if _alvo in _opcoes_periodo:
            _default_idx = _opcoes_periodo.index(_alvo)

    mes_selecionado = st.selectbox(
        "Período",
        options=_opcoes_periodo,
        index=_default_idx,
        format_func=lambda x: "Todos os meses" if x == "Todos" else f"{meses_labels.get(x, x)} ({x})",
    )

    # Setor: coords de segmento único (Luiz/Vinícius → Residencial;
    # Alexandre/Patrick/Paroli → Empresarial) não precisam do seletor.
    _coord_setor_unico: str | None = None
    if _is_coord and not _is_super_admin:
        if _auth_user in {"LUIZ", "VINICIUS"}:
            _coord_setor_unico = "RESIDENCIAL"
        elif _auth_user in SUB_ADMIN_EMP_IDS:
            _coord_setor_unico = "EMPRESARIAL"

    if _coord_setor_unico is not None:
        setor_selecionado = _coord_setor_unico
        st.caption(f"Setor: **{_coord_setor_unico}**")
    else:
        setor_selecionado = st.selectbox(
            "Setor",
            options=["Todos", "EMPRESARIAL", "RESIDENCIAL"],
        )

    st.markdown("---")
    if _is_super_admin and st.button("🗑️ Limpar dados carregados", use_container_width=True):
        for key in [
            "uploaded_bytes", "uploaded_bytes_name",
            "uploaded_etit_bytes", "uploaded_etit_bytes_name",
            "uploaded_res_ind_bytes", "uploaded_res_ind_bytes_name",
            "uploaded_toa_bytes", "uploaded_toa_bytes_name",
            "uploaded_dpa_bytes", "uploaded_dpa_bytes_name",
            "uploaded_fech_sir_bytes", "uploaded_fech_sir_bytes_name",
            "uploaded_chat_toa_bytes", "uploaded_chat_toa_bytes_name",
        ]:
            st.session_state.pop(key, None)
        st.rerun()

    if _is_admin:
        st.markdown("---")
        st.markdown('<div class="sidebar-section">Equipe</div>', unsafe_allow_html=True)
        analistas_options = df[[COL_LOGIN, COL_NOME]].drop_duplicates().sort_values(COL_NOME)
        analista_selecionado = st.selectbox(
            "Detalhe individual",
            options=["Todos"] + analistas_options[COL_LOGIN].tolist(),
            format_func=lambda x: "Visão Geral" if x == "Todos" else
                analistas_options[analistas_options[COL_LOGIN]==x][COL_NOME].iloc[0]
                if len(analistas_options[analistas_options[COL_LOGIN]==x]) > 0 else x,
        )
    else:
        analista_selecionado = "Todos"

    st.markdown("---")
    st.markdown('<div class="sidebar-section">Status dos Dados</div>', unsafe_allow_html=True)
    _upload_ts = get_upload_timestamp("produtividade.xlsx")
    if _upload_ts:
        st.info(f"📅 Dados de **{_upload_ts}**")
    if etit_loaded and (_is_super_admin or _is_sub_admin_emp):
        st.success(f"✅ ETIT: {len(df_etit)} eventos")
    if res_ind_loaded:
        st.success(f"✅ Ind. Residencial: {len(df_res_ind):,} registros")
    if toa_loaded:
        anomes_str = str(toa_anomes) if toa_anomes else "?"
        n_canc = len(df_toa[df_toa["INDICADOR_NOME"] == "TAREFAS CANCELADAS"]) if toa_loaded else 0
        n_val  = len(df_toa[df_toa["INDICADOR_NOME"] == "TEMPO DE VALIDAÇÃO DO FORMULÁRIO"]) if toa_loaded else 0
        st.success(f"✅ TOA {anomes_str}: {n_canc} canceladas · {n_val} validações")
    if dpa_loaded:
        mes_label = dpa_mes_info.get("mes_nome", "?")
        dpa_geral = _dpa_equipe_pct(df_dpa)
        dpa_g_str = f" · {dpa_geral:.1f}%" if dpa_geral else ""
        st.success(f"✅ Ocup. DPA: {len(df_dpa)} analistas · {mes_label}{dpa_g_str}")
    if fech_sir_loaded:
        _n_asser = int(df_fech_sir['ASSERTIVO'].sum())
        _n_total = int(df_fech_sir[FECH_SIR_COL_VOLUME].sum())
        _pct_sir = (_n_asser / _n_total * 100) if _n_total > 0 else 0
        st.success(
            f"✅ Fech. TOA x SIR {fech_sir_anomes} 🌙: "
            f"{_n_total} tarefas · {_pct_sir:.1f}% assertivo"
        )
    elif "uploaded_fech_sir_bytes" in st.session_state:
        st.warning("⚠️ Fech. TOA x SIR: carregado mas sem dados da equipe")
    if chat_toa_loaded:
        _anomes_str_ct = str(chat_toa_anomes) if chat_toa_anomes else "?"
        _ct_kpis = chat_toa_kpis_gerais(df_chat_toa)
        st.success(
            f"✅ Chat TOA {_anomes_str_ct}: "
            f"{_ct_kpis.get('vol_tma', 0):,} chats · "
            f"TMA {_ct_kpis.get('tma_pct', 0):.1f}%"
        )

    # Filtro Indicadores Residencial
    if res_ind_loaded:
        st.markdown('<div class="sidebar-section">Indicadores Residencial</div>', unsafe_allow_html=True)
        res_ind_selecionado = st.selectbox(
            "Indicador",
            options=["Todos"] + RES_INDICADORES_FILTRO,
            format_func=lambda x: "Todos os indicadores" if x == "Todos" else RES_IND_LABELS.get(x, x),
            key="res_ind_filter",
        )
        if RES_ANOMES in df_res_ind.columns:
            res_meses = sorted(df_res_ind[RES_ANOMES].dropna().unique().tolist())
            res_mes_sel = st.selectbox(
                "Período (Indicadores)",
                options=["Todos"] + res_meses,
                format_func=lambda x: "Todos" if x == "Todos" else str(x),
                key="res_mes_filter",
            )
        else:
            res_mes_sel = "Todos"
        if RES_COL_TURNO in df_res_ind.columns:
            _turnos_disp = sorted(df_res_ind[RES_COL_TURNO].dropna().unique().tolist())
            res_turno_sel = st.selectbox(
                "Turno",
                options=["Todos"] + _turnos_disp,
                key="res_turno_filter",
            )
        else:
            res_turno_sel = "Todos"
    else:
        res_ind_selecionado = "Todos"
        res_mes_sel = "Todos"
        res_turno_sel = "Todos"


# =====================================================
# APLICAR FILTROS
# =====================================================
df_filtrado = df.copy()
if mes_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado[COL_ANOMES] == mes_selecionado]
if setor_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Setor"] == setor_selecionado]

df_etit_filtrado = df_etit.copy()
if etit_loaded:
    if mes_selecionado != "Todos" and ETIT_COL_ANOMES in df_etit_filtrado.columns:
        try:
            _mes_int = int(float(str(mes_selecionado)))
            _an_num = pd.to_numeric(df_etit_filtrado[ETIT_COL_ANOMES], errors="coerce")
            df_etit_filtrado = df_etit_filtrado[_an_num == _mes_int]
        except (ValueError, TypeError):
            df_etit_filtrado = df_etit_filtrado[df_etit_filtrado[ETIT_COL_ANOMES].astype(str) == str(mes_selecionado)]
    if setor_selecionado != "Todos":
        df_etit_filtrado = df_etit_filtrado[df_etit_filtrado["Setor"] == setor_selecionado]
    if analista_selecionado != "Todos":
        df_etit_filtrado = df_etit_filtrado[df_etit_filtrado[ETIT_COL_LOGIN] == analista_selecionado]

df_res_filtrado = df_res_ind.copy()
if res_ind_loaded:
    if res_mes_sel != "Todos" and RES_ANOMES in df_res_filtrado.columns:
        df_res_filtrado = df_res_filtrado[df_res_filtrado[RES_ANOMES] == str(res_mes_sel).split(".")[0]]
    if res_ind_selecionado != "Todos":
        df_res_filtrado = df_res_filtrado[df_res_filtrado[RES_COL_INDICADOR_NOME] == res_ind_selecionado]
    if res_turno_sel != "Todos" and RES_COL_TURNO in df_res_filtrado.columns:
        df_res_filtrado = df_res_filtrado[df_res_filtrado[RES_COL_TURNO] == res_turno_sel]

# DPA não precisa de filtro — já é o mês mais recente detectado automaticamente
df_dpa_filtrado = df_dpa.copy()
if dpa_loaded and setor_selecionado != "Todos":
    df_dpa_filtrado = df_dpa_filtrado[df_dpa_filtrado["Setor"] == setor_selecionado]


# =====================================================
# ESTATÍSTICAS DA EQUIPE PARA COMPARAÇÃO (somente não-admin)
# =====================================================
_user_setor       = (_user_row.iloc[0]["Setor"] if not _user_row.empty else None) if not _is_admin else None
_tm_vol_medio     = None
_tm_media_diaria  = None
_tm_n             = 0
_tm_etit_ader_pct = None
_tm_ral_ader_pct  = None
_tm_rec_ader_pct  = None
_tm_ral_ader_avg  = None
_tm_ral_nader_avg = None
_tm_rec_ader_avg  = None
_tm_rec_nader_avg = None
_tm_toa_canc_avg       = None
_tm_toa_val_pct_avg    = None
_tm_toa_val_tmr_avg    = None
_tm_fech_sir_asser_avg = None

if not _is_admin and _df_team_full is not None:
    # ── Produtividade ──────────────────────────────────────────────────────
    _df_tm = _df_team_full.copy()
    if mes_selecionado != "Todos":
        _df_tm = _df_tm[_df_tm[COL_ANOMES] == mes_selecionado]
    if _user_setor:
        _df_tm = _df_tm[_df_tm["Setor"] == _user_setor]
    if not _df_tm.empty:
        _tm_res = resumo_geral(_df_tm)
        _tm_eq  = _tm_res[~_tm_res[COL_LOGIN].isin(LIDERES_IDS)] if not _tm_res.empty else pd.DataFrame()
        if not _tm_eq.empty:
            _tm_vol_medio    = _tm_eq[COL_VOL_TOTAL].mean()
            _tm_media_diaria = _tm_eq["Media_Diaria"].mean()
            _tm_n            = len(_tm_eq)

    # ── ETIT ──────────────────────────────────────────────────────────────
    if etit_loaded and not _df_etit_team_full.empty:
        _df_etit_tm = _df_etit_team_full.copy()
        if mes_selecionado != "Todos" and ETIT_COL_ANOMES in _df_etit_tm.columns:
            try:
                _mes_int_tm = int(float(str(mes_selecionado)))
                _an_num_tm = pd.to_numeric(_df_etit_tm[ETIT_COL_ANOMES], errors="coerce")
                _df_etit_tm = _df_etit_tm[_an_num_tm == _mes_int_tm]
            except (ValueError, TypeError):
                _df_etit_tm = _df_etit_tm[_df_etit_tm[ETIT_COL_ANOMES].astype(str) == str(mes_selecionado)]
        if _user_setor:
            _df_etit_tm = _df_etit_tm[_df_etit_tm["Setor"] == _user_setor]
        _etit_tm_res = etit_resumo_analista(_df_etit_tm)
        if not _etit_tm_res.empty:
            _etit_tm_eq = _etit_tm_res[~_etit_tm_res[ETIT_COL_LOGIN].isin(LIDERES_IDS)]
            if not _etit_tm_eq.empty:
                _tm_etit_ader_pct = _etit_tm_eq["Aderencia_Pct"].mean()
        _ral_rec_tm = etit_aderencia_ral_rec_por_analista(_df_etit_tm)
        if not _ral_rec_tm.empty:
            _ral_rec_tm_eq = _ral_rec_tm[~_ral_rec_tm[ETIT_COL_LOGIN].isin(LIDERES_IDS)]
            for _dem in ["RAL", "REC"]:
                _a_col  = f"{_dem}_Aderentes"
                _na_col = f"{_dem}_Nao_Aderentes"
                if _a_col in _ral_rec_tm_eq.columns and _na_col in _ral_rec_tm_eq.columns:
                    _tot_dem  = (_ral_rec_tm_eq[_a_col] + _ral_rec_tm_eq[_na_col]).replace(0, np.nan)
                    _pcts_dem = (_ral_rec_tm_eq[_a_col] / _tot_dem * 100).mean()
                    if _dem == "RAL":
                        _tm_ral_ader_pct  = _pcts_dem
                        _tm_ral_ader_avg  = _ral_rec_tm_eq[_a_col].mean()
                        _tm_ral_nader_avg = _ral_rec_tm_eq[_na_col].mean()
                    else:
                        _tm_rec_ader_pct  = _pcts_dem
                        _tm_rec_ader_avg  = _ral_rec_tm_eq[_a_col].mean()
                        _tm_rec_nader_avg = _ral_rec_tm_eq[_na_col].mean()

    # ── TOA ──────────────────────────────────────────────────────────────
    if toa_loaded and not _df_toa_team_full.empty:
        _df_toa_tm2 = _df_toa_team_full.copy()
        if "Setor" in _df_toa_tm2.columns and _user_setor:
            _df_toa_tm2 = _df_toa_tm2[_df_toa_tm2["Setor"] == _user_setor]
        _toa_canc_tm = toa_canceladas_por_analista(_df_toa_tm2)
        if not _toa_canc_tm.empty and "Login" in _toa_canc_tm.columns:
            _toa_canc_eq = _toa_canc_tm[
                ~_toa_canc_tm["Login"].str.upper().isin({l.upper() for l in LIDERES_IDS})
            ]
            if not _toa_canc_eq.empty:
                _tm_toa_canc_avg = _toa_canc_eq["Canceladas"].mean()
        _toa_val_tm = toa_validacao_por_analista(_df_toa_tm2)
        if not _toa_val_tm.empty and "Login" in _toa_val_tm.columns:
            _toa_val_eq = _toa_val_tm[
                ~_toa_val_tm["Login"].str.upper().isin({l.upper() for l in LIDERES_IDS})
            ]
            if not _toa_val_eq.empty:
                _tm_toa_val_pct_avg = _toa_val_eq["Aderencia_Pct"].mean()
                _tm_toa_val_tmr_avg = _toa_val_eq["TMR_Medio_min"].mean()

    # ── Fechamento TOA x SIR ─────────────────────────────────────────────
    if fech_sir_loaded and not _df_fech_sir_team_full.empty:
        _fech_tm2 = fech_sir_resumo_analista(_df_fech_sir_team_full)
        if not _fech_tm2.empty and "Login" in _fech_tm2.columns:
            _fech_eq_tm2 = _fech_tm2[
                ~_fech_tm2["Login"].str.upper().isin({l.upper() for l in LIDERES_IDS})
            ]
            if not _fech_eq_tm2.empty:
                _tm_fech_sir_asser_avg = _fech_eq_tm2["Assertividade_Pct"].mean()


# =====================================================
# KPIs GERAIS — somente admins
# =====================================================
n_analistas = df_filtrado[COL_LOGIN].nunique()
if _is_admin:
    st.markdown('<div class="section-header">📈 Indicadores Gerais da Equipe</div>', unsafe_allow_html=True)

    total_vol = df_filtrado[COL_VOL_TOTAL].sum()
    media_diaria_equipe = df_filtrado.groupby(COL_LOGIN)[COL_VOL_TOTAL].sum().mean()
    dpa_valid = df_filtrado[(df_filtrado[COL_DPA_RESULTADO] >= 0) & (df_filtrado[COL_DPA_RESULTADO] <= 120)]
    dpa_media = dpa_valid[COL_DPA_RESULTADO].mean() if not dpa_valid.empty else None
    data_min = df_filtrado[COL_DATA].min()
    data_max = df_filtrado[COL_DATA].max()

    # KPI de DPA Oficial — média das médias setoriais (cada setor com peso igual),
    # consistente com a "Média do setor" exibida abaixo.
    dpa_oficial_geral = _dpa_equipe_pct(df_dpa_filtrado) if dpa_loaded else None

    n_kpi_cols = 5 if dpa_loaded else 4
    kpi_cols = st.columns(n_kpi_cols)

    with kpi_cols[0]:
        st.markdown(kpi_card("Volume Total", f"{total_vol:,.0f}", COR_PRIMARIA), unsafe_allow_html=True)
    with kpi_cols[1]:
        st.markdown(kpi_card("Analistas Ativos", f"{n_analistas}", COR_INFO), unsafe_allow_html=True)
    with kpi_cols[2]:
        st.markdown(kpi_card("Média/Analista", f"{media_diaria_equipe:,.0f}", COR_SUCESSO), unsafe_allow_html=True)
    with kpi_cols[3]:
        periodo_str = f"{data_min.strftime('%d/%m')}" if pd.notna(data_min) else "—"
        periodo_str += f" a {data_max.strftime('%d/%m')}" if pd.notna(data_max) else ""
        st.markdown(kpi_card("Período", periodo_str, COR_INFO), unsafe_allow_html=True)
    if dpa_loaded:
        with kpi_cols[4]:
            mes_nome = dpa_mes_info.get("mes_nome") or "?"
            dpa_of_display = f"{dpa_oficial_geral:.1f}" if dpa_oficial_geral else "—"
            dpa_of_color = _dpa_color(dpa_oficial_geral)
            st.markdown(
                kpi_card(f"DPA Oficial ({mes_nome[:3]})", dpa_of_display, dpa_of_color, suffix="%"),
                unsafe_allow_html=True,
            )
else:
    # Calcula variáveis usadas mais à frente mesmo sem exibir os KPIs
    total_vol = df_filtrado[COL_VOL_TOTAL].sum()
    dpa_valid = df_filtrado[(df_filtrado[COL_DPA_RESULTADO] >= 0) & (df_filtrado[COL_DPA_RESULTADO] <= 120)]
    dpa_media = dpa_valid[COL_DPA_RESULTADO].mean() if not dpa_valid.empty else None
    data_min = df_filtrado[COL_DATA].min()
    data_max = df_filtrado[COL_DATA].max()
    dpa_oficial_geral = _dpa_equipe_pct(_df_dpa_team_full) if dpa_loaded else None


# =====================================================
# VISÃO INDIVIDUAL
# =====================================================
if analista_selecionado != "Todos":
    df_analista = df_filtrado[df_filtrado[COL_LOGIN] == analista_selecionado]
    if not df_analista.empty:
        nome_analista = df_analista[COL_NOME].iloc[0]
        st.markdown(f'<div class="section-header">👤 Detalhe: {nome_analista}</div>', unsafe_allow_html=True)

        ca1, ca2, ca3, ca4 = st.columns(4)
        vol_ind = df_analista[COL_VOL_TOTAL].sum()
        dias_ind = len(df_analista)
        media_ind = vol_ind / dias_ind if dias_ind > 0 else 0

        with ca1:
            st.markdown(kpi_card("Volume Total", f"{vol_ind:,.0f}", COR_PRIMARIA), unsafe_allow_html=True)
        with ca2:
            st.markdown(kpi_card("Dias Trabalhados", f"{dias_ind}", COR_INFO), unsafe_allow_html=True)
        with ca3:
            st.markdown(kpi_card("Média Diária", f"{media_ind:.1f}", COR_SUCESSO), unsafe_allow_html=True)
        with ca4:
            if dpa_loaded:
                dpa_row = df_dpa[df_dpa["Login"] == analista_selecionado]
                dpa_of_ind = dpa_row["DPA_Pct_Oficial"].iloc[0] if not dpa_row.empty else None
                dpa_of_str = f"{dpa_of_ind:.1f}" if dpa_of_ind else "—"
                mes_nome = (dpa_mes_info.get("mes_nome") or "")[:3]
                st.markdown(
                    kpi_card(f"DPA Oficial ({mes_nome})", dpa_of_str, _dpa_color(dpa_of_ind), suffix="%"),
                    unsafe_allow_html=True,
                )

        daily_ind = df_analista.groupby(COL_DATA)[COL_VOL_TOTAL].sum().reset_index()
        daily_ind.columns = ["Data", "Volume"]
        st.bar_chart(daily_ind.set_index("Data"), color=COR_INFO, height=250)

        vol_breakdown = {}
        for col, label in VOL_COLS.items():
            if col in df_analista.columns:
                v = df_analista[col].sum()
                if v > 0:
                    vol_breakdown[label] = v
        if vol_breakdown:
            comp_df = pd.DataFrame(list(vol_breakdown.items()), columns=["Atividade", "Volume"])
            comp_df = comp_df.sort_values("Volume", ascending=True)
            st.bar_chart(comp_df.set_index("Atividade"), horizontal=True, color=COR_PRIMARIA, height=300)

        if _is_super_admin and etit_loaded and not df_etit_filtrado.empty:
            st.markdown("##### ⚡ ETIT POR EVENTO — Este Analista")
            etit_ind = df_etit_filtrado[df_etit_filtrado[ETIT_COL_LOGIN] == analista_selecionado]
            if not etit_ind.empty:
                ei1, ei2, ei3, ei4 = st.columns(4)
                etit_total = etit_ind[ETIT_COL_VOLUME].sum()
                etit_ader = etit_ind[ETIT_COL_INDICADOR_VAL].sum()
                etit_pct = (etit_ader / etit_total * 100) if etit_total > 0 else 0
                etit_tma = etit_ind[ETIT_COL_TMA].mean()
                with ei1:
                    st.markdown(kpi_card("Eventos ETIT", f"{etit_total:,.0f}", "#8E44AD"), unsafe_allow_html=True)
                with ei2:
                    st.markdown(kpi_card("Aderentes", f"{etit_ader:,.0f}", COR_SUCESSO), unsafe_allow_html=True)
                with ei3:
                    ad_color = COR_SUCESSO if etit_pct >= 90 else (COR_ALERTA if etit_pct >= 70 else COR_PERIGO)
                    st.markdown(kpi_card("Aderência", f"{etit_pct:.1f}", ad_color, suffix="%"), unsafe_allow_html=True)
                with ei4:
                    st.markdown(kpi_card("TMA Médio", _fmt_hms(etit_tma), COR_INFO), unsafe_allow_html=True)
            else:
                st.caption("Nenhum evento ETIT encontrado para este analista no período.")

        st.markdown("---")


# =====================================================
# TABS PRINCIPAIS
# =====================================================
if _is_admin:
    tab_labels = [
        "🏆 Ranking",
        "👑 Líderes",
    ]
    # Sub-admins empresariais (N0150817, N5768308, TPAROLI) veem ETIT Empresarial;
    # coords clássicos (LUIZ/VINICIUS) continuam sem a aba.
    _etit_tab_visible = etit_loaded and (_is_super_admin or _is_sub_admin_emp)
    if _etit_tab_visible:
        tab_labels.append("⚡ ETIT por Evento")
    if res_ind_loaded:
        tab_labels.append("🏠 Indicadores Residencial")
    if toa_loaded:
        tab_labels.append("📋 Indicadores TOA")
    if dpa_loaded:
        tab_labels.append("📊 Ocupação DPA")
    if fech_sir_loaded:
        tab_labels.append("🌙 Fechamento TOA x SIR")
    if chat_toa_loaded:
        tab_labels.append("💬 Chat TOA")
    tab_labels.append("✅ Analista Certificado")
    tabs = st.tabs(tab_labels)
    _base_tabs = 2
    _tab_etit_idx  = _base_tabs if _etit_tab_visible else None
    _tab_res_idx   = (_base_tabs + (1 if _etit_tab_visible else 0)) if res_ind_loaded else None
    _tab_toa_idx   = (
        _base_tabs + (1 if _etit_tab_visible else 0) + (1 if res_ind_loaded else 0)
    ) if toa_loaded else None
    _tab_dpa_idx   = (
        _base_tabs + (1 if _etit_tab_visible else 0) + (1 if res_ind_loaded else 0) + (1 if toa_loaded else 0)
    ) if dpa_loaded else None
    _tab_fech_sir_idx = (
        _base_tabs
        + (1 if _etit_tab_visible else 0)
        + (1 if res_ind_loaded else 0)
        + (1 if toa_loaded else 0)
        + (1 if dpa_loaded else 0)
    ) if fech_sir_loaded else None
    _tab_chat_toa_idx = (
        _base_tabs
        + (1 if _etit_tab_visible else 0)
        + (1 if res_ind_loaded else 0)
        + (1 if toa_loaded else 0)
        + (1 if dpa_loaded else 0)
        + (1 if fech_sir_loaded else 0)
    ) if chat_toa_loaded else None
    _tab_cert_idx = (
        _base_tabs
        + (1 if _etit_tab_visible else 0)
        + (1 if res_ind_loaded else 0)
        + (1 if toa_loaded else 0)
        + (1 if dpa_loaded else 0)
        + (1 if fech_sir_loaded else 0)
        + (1 if chat_toa_loaded else 0)
    )
else:
    # Não-admin: visão consolidada (Cockpit do Analista)
    _u_labels = ["🚀 Meu Painel"]
    _u_i = 1
    _u_etit_idx = None; _u_res_idx = None; _u_toa_idx = None
    _u_dpa_idx = None;  _u_fech_sir_idx = None; _u_chat_toa_idx = None; _u_highlights_idx = None
    if etit_loaded:
        _u_labels.append("⚡ ETIT por Evento");  _u_etit_idx = _u_i; _u_i += 1
    if res_ind_loaded:
        _u_labels.append("🏠 Indicadores Residencial"); _u_res_idx = _u_i; _u_i += 1
    if toa_loaded:
        _u_labels.append("📋 Indicadores TOA");  _u_toa_idx = _u_i; _u_i += 1
    if dpa_loaded:
        _u_labels.append("📊 Ocupação DPA");     _u_dpa_idx = _u_i; _u_i += 1
    if fech_sir_loaded:
        _u_labels.append("🌙 Fechamento TOA x SIR"); _u_fech_sir_idx = _u_i; _u_i += 1
    if chat_toa_loaded:
        _u_labels.append("💬 Chat TOA"); _u_chat_toa_idx = _u_i; _u_i += 1
    _u_labels.append("⭐ Highlights"); _u_highlights_idx = _u_i
    tabs = st.tabs(_u_labels)

# Unified tab indices — make admin-side variables point to the correct tab for each user type
if not _is_admin:
    _tab_etit_idx     = _u_etit_idx
    _tab_res_idx      = _u_res_idx
    _tab_toa_idx      = _u_toa_idx
    _tab_dpa_idx      = _u_dpa_idx
    _tab_fech_sir_idx = _u_fech_sir_idx
    _tab_chat_toa_idx = _u_chat_toa_idx
    _tab_cert_idx     = None


# ---- TAB 1: RANKING ----
with tabs[0]:
  if not _is_admin:
    # ── Visão do analista: Cockpit Pessoal ──
    _resumo_user = resumo_geral(df_filtrado)
    if not _resumo_user.empty:
        _user_row_res = _resumo_user.iloc[0]
        _u_vol   = _user_row_res[COL_VOL_TOTAL]
        _u_dias  = _user_row_res.get("Dias_Trabalhados", 0)
        _u_media = _user_row_res.get("Media_Diaria", 0)
        _u_dpa   = _user_row_res.get("DPA_Media", None)
        _u_nome_display = _user_nome or _mat_up or "Analista"
        setor_label = _user_setor or "—"
        _setor_icon = "🏠" if setor_label == "RESIDENCIAL" else "🏢"

        # ── HERO BANNER ──────────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="analyst-hero-banner">
            <div>
                <div class="analyst-greeting">👋 Bem-vindo ao seu Painel, {_u_nome_display}!</div>
                <div class="analyst-subgreeting">Acompanhe seus resultados individuais e seu desempenho em relação às metas do setor.</div>
                <div class="analyst-badge-row">
                    <span class="analyst-pill analyst-pill-setor">{_setor_icon} Setor {setor_label}</span>
                    <span class="analyst-pill analyst-pill-setor">🔑 Matrícula: {_mat_up}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── KPI CARDS COMPARATIVOS (Você vs Média da Equipe) ─────────────────
        st.markdown('<div class="section-header">📊 Seu Desempenho no Período</div>', unsafe_allow_html=True)

        _cmp_cols = st.columns(4)
        with _cmp_cols[0]:
            _vol_delta = (_u_vol - _tm_vol_medio) if _tm_vol_medio else None
            st.markdown(kpi_card("Seu Volume Total", f"{_u_vol:,.0f}", COR_PRIMARIA, delta=_vol_delta), unsafe_allow_html=True)
        with _cmp_cols[1]:
            _c_media = COR_SUCESSO if (_tm_media_diaria and _u_media >= _tm_media_diaria) else COR_ALERTA
            _media_delta = (_u_media - _tm_media_diaria) if _tm_media_diaria else None
            st.markdown(kpi_card("Sua Média Diária", f"{_u_media:,.1f}", _c_media, delta=_media_delta), unsafe_allow_html=True)
        with _cmp_cols[2]:
            _tm_v_str = f"{_tm_vol_medio:,.0f}" if _tm_vol_medio else "—"
            st.markdown(kpi_card("Média Vol. Equipe", _tm_v_str, COR_INFO), unsafe_allow_html=True)
        with _cmp_cols[3]:
            _tm_md_str = f"{_tm_media_diaria:,.1f}" if _tm_media_diaria else "—"
            st.markdown(kpi_card("Média/Dia Equipe", _tm_md_str, COR_INFO), unsafe_allow_html=True)

        # ── VISUALIZAÇÕES GRÁFICAS LADO A LADO ─────────────────────────────
        st.markdown("")
        _cg1, _cg2 = st.columns(2)
        with _cg1:
            st.markdown("##### 📈 Sua Evolução Diária de Volume")
            daily_ind = df_filtrado.groupby(COL_DATA)[COL_VOL_TOTAL].sum().reset_index()
            daily_ind.columns = ["Data", "Volume"]
            st.bar_chart(daily_ind.set_index("Data"), color=COR_INFO, height=270)
        with _cg2:
            st.markdown("##### 🧩 Sua Composição de Atividades")
            vol_breakdown = {}
            for col, label in VOL_COLS.items():
                if col in df_filtrado.columns:
                    v = df_filtrado[col].sum()
                    if v > 0:
                        vol_breakdown[label] = v
            if vol_breakdown:
                comp_df = pd.DataFrame(list(vol_breakdown.items()), columns=["Atividade", "Quantidade"])
                comp_df = comp_df.sort_values("Quantidade", ascending=True)
                st.bar_chart(comp_df.set_index("Atividade"), horizontal=True, color=COR_PRIMARIA, height=270)
            else:
                st.info("Sem dados de composição de atividades para o período.")

        # ── TABELAS DETALHADAS E DOWNLOAD ──────────────────────────────────────
        st.markdown("---")
        st.markdown("##### 📋 Seus Registros Detalhados por Período")
        _disp_cols_u = [COL_NOME, "Setor", "Dias_Trabalhados", COL_VOL_TOTAL, "Media_Diaria"]
        _disp_labels_u = ["Analista", "Setor", "Dias", "Vol. Total", "Média/Dia"]
        _sv_u = get_sector_vol_cols(setor_selecionado, _resumo_user.columns)
        _vk_u = list(_sv_u.keys()); _vl_u = list(_sv_u.values())
        _avail_u = [c for c in _disp_cols_u if c in _resumo_user.columns]
        _det_u = _resumo_user[_avail_u + _vk_u].copy()
        _det_u.columns = _disp_labels_u[:len(_avail_u)] + _vl_u
        _det_u = _det_u.sort_values("Vol. Total", ascending=False).reset_index(drop=True)
        _det_u.index += 1; _det_u.index.name = "#"
        st.dataframe(_det_u, use_container_width=True)

        st.markdown("---")
        st.markdown("##### 📅 Seu Histórico Diário Completo")
        _raw_cols_u = [COL_DATA, COL_MES, COL_VOL_TOTAL, COL_DPA_RESULTADO]
        _vol_raw_u = [c for c in VOL_COLS.keys() if c in df_filtrado.columns]
        _raw_cols_u += _vol_raw_u
        _raw_avail_u = [c for c in _raw_cols_u if c in df_filtrado.columns]
        st.dataframe(
            df_filtrado[_raw_avail_u].sort_values([COL_DATA]),
            use_container_width=True, height=320,
        )
        _csv_u = df_filtrado[_raw_avail_u].to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar meus dados (CSV)", _csv_u, "meus_dados_produtividade.csv", "text/csv")
  else:
    resumo = resumo_geral(df_filtrado)
    if not resumo.empty:
        resumo_equipe = resumo[~resumo[COL_LOGIN].isin(LIDERES_IDS)].copy()

        col_rank1, col_rank2 = st.columns(2)
        with col_rank1:
            st.markdown("#### 📦 Ranking por Volume Total")
            rank_vol = resumo_equipe[[COL_LOGIN, COL_NOME, "Setor", COL_VOL_TOTAL, "Dias_Trabalhados", "Media_Diaria"]].copy()
            rank_vol["Nome"] = rank_vol[COL_NOME].apply(primeiro_nome)
            rank_vol = rank_vol.sort_values(COL_VOL_TOTAL, ascending=False).reset_index(drop=True)
            rank_vol.index += 1; rank_vol.index.name = "#"
            display_vol = rank_vol[["Nome", "Setor", COL_VOL_TOTAL, "Dias_Trabalhados", "Media_Diaria"]].copy()
            display_vol.columns = ["Analista", "Setor", "Vol. Total", "Dias", "Média/Dia"]
            for _nc in ["Vol. Total", "Dias", "Média/Dia"]:
                display_vol[_nc] = pd.to_numeric(display_vol[_nc], errors="coerce")
            display_vol = display_vol.replace([np.inf, -np.inf], np.nan)
            _vol_max = display_vol["Vol. Total"].max()
            _vol_vmax = float(_vol_max) if pd.notna(_vol_max) and _vol_max > 0 else 1.0
            st.dataframe(
                display_vol.style
                    .format({"Média/Dia": "{:.1f}", "Dias": "{:.0f}"}, na_rep="—")
                    .background_gradient(cmap="Blues", subset=["Vol. Total"], vmin=0, vmax=_vol_vmax),
                use_container_width=True, height=500,
            )

        with col_rank2:
            st.markdown("#### ⏱️ Ranking por DPA Oficial")

            if dpa_loaded and not df_dpa_filtrado.empty:
                rank_dpa_of = dpa_ranking(df_dpa_filtrado)
                rank_dpa_of = rank_dpa_of[~rank_dpa_of["Login"].isin(LIDERES_IDS)].reset_index(drop=True)
                rank_dpa_of.index += 1; rank_dpa_of.index.name = "#"
                _mes_label = dpa_mes_info.get("mes_nome") or "?"
                _geral_pct = _dpa_equipe_pct(df_dpa_filtrado)
                _geral_str = f"{_geral_pct:.1f}" if _geral_pct is not None else "—"
                st.caption(f"📌 DPA Oficial — {_mes_label} (média geral da equipe: {_geral_str}%)")

                rank_dpa_of["Status"] = rank_dpa_of["DPA %"].apply(_dpa_semaforo)
                rank_dpa_of = rank_dpa_of[["Status", "Analista", "Setor", "DPA %"]]
                st.dataframe(
                    rank_dpa_of.style
                        .format({"DPA %": "{:.1f}"})
                        .background_gradient(cmap="RdYlGn", subset=["DPA %"], vmin=50, vmax=100),
                    use_container_width=True, height=500,
                )
            else:
                st.info("Carregue a planilha de Ocupação DPA para ver o ranking.")

        st.markdown("#### 📊 Ranking por Média Diária")
        rank_media = resumo_equipe[[COL_NOME, "Media_Diaria"]].copy()
        rank_media["Nome"] = rank_media[COL_NOME].apply(primeiro_nome)
        # Desambigua nomes iguais gerados por primeiro_nome (ex: dois "Lucas Silva")
        _seen: dict = {}
        _nomes_unicos = []
        for _n in rank_media["Nome"]:
            if _n in _seen:
                _seen[_n] += 1
                _nomes_unicos.append(f"{_n} ({_seen[_n]})")
            else:
                _seen[_n] = 0
                _nomes_unicos.append(_n)
        rank_media["Nome"] = _nomes_unicos
        chart_data = rank_media[["Nome", "Media_Diaria"]].set_index("Nome").sort_values("Media_Diaria")
        st.bar_chart(chart_data, horizontal=True, color=COR_PRIMARIA, height=500)

        st.markdown("---")
        st.markdown("#### 📋 Análise Detalhada por Setor")
        if setor_selecionado in ("Todos", "RESIDENCIAL"):
            render_sector_table(resumo_equipe, "RESIDENCIAL", VOL_COLS_RESIDENCIAL, "Blues")
        if setor_selecionado in ("Todos", "EMPRESARIAL"):
            render_sector_table(resumo_equipe, "EMPRESARIAL", VOL_COLS_EMPRESARIAL, "Oranges")

        st.markdown("---")
        st.markdown("#### 💡 Insights — Pontos Fortes e Oportunidades")
        insights = build_insights(resumo_equipe, setor_selecionado)
        render_insight_cards(insights)

        st.markdown("---")
        st.markdown("#### 📋 Dados Detalhados")
        st.markdown("##### Resumo por Analista")
        resumo_det = resumo_geral(df_filtrado)
        if not resumo_det.empty:
            display_cols = [COL_NOME, "Setor", "Dias_Trabalhados", COL_VOL_TOTAL, "Media_Diaria"]
            display_labels = ["Analista", "Setor", "Dias", "Vol. Total", "Média/Dia"]
            sector_vol = get_sector_vol_cols(setor_selecionado, resumo_det.columns)
            vol_keys = list(sector_vol.keys()); vol_labels = list(sector_vol.values())
            available_base = [c for c in display_cols if c in resumo_det.columns]
            available_labels = display_labels[:len(available_base)]
            det = resumo_det[available_base + vol_keys].copy()
            det.columns = available_labels + vol_labels
            det = det.sort_values("Vol. Total", ascending=False).reset_index(drop=True)
            det.index += 1; det.index.name = "#"
            st.dataframe(det, use_container_width=True)

        st.markdown("##### Dados Brutos (Filtrados)")
        cols_to_show = [COL_LOGIN, COL_NOME, "Setor", COL_DATA, COL_MES, COL_VOL_TOTAL, COL_DPA_RESULTADO]
        vol_cols_existing = [c for c in VOL_COLS.keys() if c in df_filtrado.columns]
        cols_to_show += vol_cols_existing
        cols_existing = [c for c in cols_to_show if c in df_filtrado.columns]
        st.dataframe(df_filtrado[cols_existing].sort_values([COL_NOME, COL_DATA]),
                     use_container_width=True, height=500)
        csv = df_filtrado[cols_existing].to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar dados filtrados (CSV)", csv, "produtividade_equipe.csv", "text/csv")


# ---- TAB LÍDERES (apenas admin) ----
if _is_admin:
    with tabs[1]:
        resumo_full = resumo_geral(df_filtrado)
        resumo_lid = resumo_full[resumo_full[COL_LOGIN].isin(LIDERES_IDS)].copy()
        resumo_equipe_all = resumo_full[~resumo_full[COL_LOGIN].isin(LIDERES_IDS)].copy()

        if not resumo_lid.empty:
            st.markdown("#### 👑 Visão dos Líderes")
            st.caption("Comparação entre os líderes e as médias das suas equipes.")

            _lid_sorted = list(resumo_lid.sort_values(COL_VOL_TOTAL, ascending=False).iterrows())
            _n_lid      = len(_lid_sorted)
            _per_row    = 4 if _n_lid > 6 else max(1, min(_n_lid, 4))
            _chunks     = [_lid_sorted[i:i + _per_row] for i in range(0, _n_lid, _per_row)]

            for _chunk in _chunks:
                cols_lid = st.columns(_per_row)
                for idx, (_, lrow) in enumerate(_chunk):
                    nome_l = primeiro_nome(lrow[COL_NOME])
                    setor_l = lrow["Setor"]
                    vol_l = lrow[COL_VOL_TOTAL]
                    media_l = lrow.get("Media_Diaria", 0)
                    dias_l = lrow.get("Dias_Trabalhados", 0)

                    dpa_of_l = None
                    if dpa_loaded:
                        dpa_row = df_dpa[df_dpa["Login"] == lrow[COL_LOGIN]]
                        if not dpa_row.empty:
                            dpa_of_l = dpa_row["DPA_Pct_Oficial"].iloc[0]

                    dpa_l_str = f"{dpa_of_l:.1f}%" if dpa_of_l is not None and pd.notna(dpa_of_l) else "—"

                    team = resumo_equipe_all[resumo_equipe_all["Setor"] == setor_l]
                    team_avg_vol = team[COL_VOL_TOTAL].mean() if not team.empty else 0
                    team_avg_media = team["Media_Diaria"].mean() if not team.empty else 0
                    diff_vol = ((vol_l / team_avg_vol - 1) * 100) if team_avg_vol > 0 else 0
                    diff_media = ((media_l / team_avg_media - 1) * 100) if team_avg_media > 0 else 0
                    badge_setor = "RES" if setor_l == "RESIDENCIAL" else "EMP"
                    diff_vol_color = "#2ECC71" if diff_vol >= 0 else "#E74C3C"
                    diff_vol_icon = "▲" if diff_vol >= 0 else "▼"

                    with cols_lid[idx]:
                        st.markdown(f"""<div class="leader-card">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <div>
                                    <span class="l-name">{nome_l}</span>
                                    <span class="l-badge">{badge_setor}</span>
                                </div>
                            </div>
                            <div class="l-vol">{vol_l:,.0f}</div>
                            <div class="l-stat">Média: {media_l:.1f}/dia · Dias: {dias_l:.0f} · DPA: {dpa_l_str}</div>
                            <div class="l-stat" style="margin-top:0.2rem;">
                                vs Equipe: <span style="color:{diff_vol_color};font-weight:600;">{diff_vol_icon}{abs(diff_vol):.0f}% vol</span>
                                · <span style="color:{diff_vol_color};font-weight:600;">{diff_vol_icon}{abs(diff_media):.0f}% média</span>
                        </div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 📊 Comparação Detalhada")
            sector_vol_lid = get_sector_vol_cols(setor_selecionado, resumo_lid.columns)
            vol_keys_lid = list(sector_vol_lid.keys())
            base_cols_lid = [COL_NOME, "Setor", COL_VOL_TOTAL, "Dias_Trabalhados", "Media_Diaria"]
            avail_lid = [c for c in base_cols_lid if c in resumo_lid.columns]
            det_lid = resumo_lid[avail_lid + vol_keys_lid].copy()
            det_lid[COL_NOME] = det_lid[COL_NOME].apply(primeiro_nome)
            rename_lid = {
                COL_NOME: "Líder", "Setor": "Setor", COL_VOL_TOTAL: "Vol. Total",
                "Dias_Trabalhados": "Dias", "Media_Diaria": "Média/Dia",
            }
            rename_lid.update(sector_vol_lid)
            det_lid = det_lid.rename(columns=rename_lid)
            det_lid = det_lid.sort_values("Vol. Total", ascending=False).reset_index(drop=True)
            det_lid.index += 1; det_lid.index.name = "#"
            fmt_lid = {"Média/Dia": "{:.1f}"}
            styled_lid = det_lid.style.format(fmt_lid, na_rep="—")
            styled_lid = styled_lid.background_gradient(cmap="YlOrBr", subset=["Vol. Total"])
            st.dataframe(styled_lid, use_container_width=True)

            st.markdown("---")
            st.markdown("#### 💡 Insights dos Líderes")
            lid_insights = build_insights(resumo_full, setor_selecionado)
            lid_insights = [i for i in lid_insights if i["login"] in LIDERES_IDS]
            render_insight_cards(lid_insights)

            if fech_sir_loaded and not df_fech_sir.empty:
                _fech_lid = df_fech_sir[df_fech_sir[FECH_SIR_COL_LOGIN].isin({l.upper() for l in LIDERES_IDS})].copy()
                if not _fech_lid.empty:
                    st.markdown("---")
                    st.markdown(f"#### 🌙 Fechamento TOA x SIR — Madrugada ({fech_sir_anomes}) — Líderes")
                    _fl = fech_sir_resumo_analista(_fech_lid)
                    if not _fl.empty:
                        _fl["Analista"] = _fl["Nome"].apply(primeiro_nome)
                        _fl_show = _fl[["Analista", "Setor", "Volume", "Assertivos", "Assertividade_Pct"]].copy()
                        _fl_show.columns = ["Analista", "Setor", "Tarefas", "Assertivos", "Assertividade %"]
                        _fl_show = _fl_show.reset_index(drop=True)
                        _fl_show.index += 1; _fl_show.index.name = "#"
                        st.dataframe(
                            _fl_show.style
                                .format({"Assertividade %": "{:.1f}", "Tarefas": "{:.0f}", "Assertivos": "{:.0f}"}, na_rep="—")
                                .background_gradient(cmap="RdYlGn", subset=["Assertividade %"], vmin=50, vmax=100),
                            use_container_width=True,
                        )
        else:
            st.info("Nenhum líder encontrado nos dados filtrados.")




# ---- TAB 5: ETIT POR EVENTO ----
if etit_loaded and _tab_etit_idx is not None:
    with tabs[_tab_etit_idx]:
        st.markdown("#### ⚡ ETIT POR EVENTO — Análise da Equipe")
        if df_etit_filtrado.empty:
            st.warning("Nenhum dado ETIT POR EVENTO encontrado com os filtros atuais.")
            if not df_etit.empty and ETIT_COL_ANOMES in df_etit.columns:
                _anomes_presentes = sorted(
                    pd.to_numeric(df_etit[ETIT_COL_ANOMES], errors="coerce")
                    .dropna().astype(int).unique().tolist()
                )
                if _anomes_presentes:
                    st.caption(
                        f"💡 Períodos com dados ETIT: {', '.join(str(a) for a in _anomes_presentes)}. "
                        f"Selecione um destes no filtro 'Período' à esquerda."
                    )
        else:
            etit_total_eventos = df_etit_filtrado[ETIT_COL_VOLUME].sum()
            etit_total_ader = df_etit_filtrado[ETIT_COL_INDICADOR_VAL].sum()
            etit_pct_ader = (etit_total_ader / etit_total_eventos * 100) if etit_total_eventos > 0 else 0
            etit_n_analistas = df_etit_filtrado[ETIT_COL_LOGIN].nunique()
            etit_tma_geral = df_etit_filtrado[ETIT_COL_TMA].mean()
            etit_tmr_geral = df_etit_filtrado[ETIT_COL_TMR].mean()

            ek1, ek2, ek3, ek4, ek5, ek6 = st.columns(6)
            with ek1:
                st.markdown(kpi_card("Total Eventos", f"{etit_total_eventos:,.0f}", "#8E44AD"), unsafe_allow_html=True)
            with ek2:
                st.markdown(kpi_card("Aderentes", f"{etit_total_ader:,.0f}", COR_SUCESSO), unsafe_allow_html=True)
            with ek3:
                ad_c = COR_SUCESSO if etit_pct_ader >= 90 else (COR_ALERTA if etit_pct_ader >= 70 else COR_PERIGO)
                st.markdown(kpi_card("Aderência", f"{etit_pct_ader:.1f}", ad_c, suffix="%"), unsafe_allow_html=True)
            with ek4:
                st.markdown(kpi_card("Analistas", f"{etit_n_analistas}", COR_INFO), unsafe_allow_html=True)
            with ek5:
                st.markdown(kpi_card("TMA Médio", _fmt_hms(etit_tma_geral), COR_PRIMARIA), unsafe_allow_html=True)
            with ek6:
                st.markdown(kpi_card("TMR Médio", _fmt_hms(etit_tmr_geral), COR_ALERTA), unsafe_allow_html=True)

            st.markdown("##### 🏆 Ranking ETIT por Analista")
            resumo_etit = etit_resumo_analista(df_etit_filtrado)
            if not resumo_etit.empty:
                disp_etit = resumo_etit.copy()
                disp_etit["Nome"] = disp_etit["Nome"].apply(primeiro_nome)
                disp_cols_etit = ["Nome", "Setor", "Total_Eventos", "Eventos_Aderentes",
                                  "Aderencia_Pct", "RAL_Count", "REC_Count", "TMA_Medio", "TMR_Medio"]
                disp_cols_etit = [c for c in disp_cols_etit if c in disp_etit.columns]
                tbl_etit = disp_etit[disp_cols_etit].copy()
                tbl_etit.columns = [
                    c.replace("Total_Eventos","Eventos").replace("Eventos_Aderentes","Aderentes")
                     .replace("Aderencia_Pct","Aderência %").replace("RAL_Count","RAL")
                     .replace("REC_Count","REC").replace("TMA_Medio","TMA").replace("TMR_Medio","TMR")
                    for c in disp_cols_etit
                ]
                tbl_etit = tbl_etit.reset_index(drop=True); tbl_etit.index += 1; tbl_etit.index.name = "#"
                styled_etit = tbl_etit.style.format({"Aderência %": "{:.1f}", "TMA": _fmt_hms, "TMR": _fmt_hms}, na_rep="—")
                styled_etit = styled_etit.background_gradient(cmap="Purples", subset=["Eventos"])
                if "Aderência %" in tbl_etit.columns and tbl_etit["Aderência %"].notna().any():
                    styled_etit = styled_etit.background_gradient(cmap="RdYlGn", subset=["Aderência %"], vmin=50, vmax=100)
                st.dataframe(styled_etit, use_container_width=True)

            # Para não-admin: renomeia o título do ranking
            if not _is_admin:
                st.markdown("##### 📊 Comparação com a Equipe")
                _cmp_etit_cols = st.columns(3)
                with _cmp_etit_cols[0]:
                    _u_ader_pct = df_etit_filtrado[ETIT_COL_INDICADOR_VAL].sum() / df_etit_filtrado[ETIT_COL_VOLUME].sum() * 100 if df_etit_filtrado[ETIT_COL_VOLUME].sum() > 0 else 0
                    _tm_ader_str = f"{_tm_etit_ader_pct:.1f}%" if _tm_etit_ader_pct else "—"
                    _c = COR_SUCESSO if (_tm_etit_ader_pct and _u_ader_pct >= _tm_etit_ader_pct) else COR_ALERTA
                    st.markdown(kpi_card("Sua Aderência", f"{_u_ader_pct:.1f}", _c, suffix="%"), unsafe_allow_html=True)
                with _cmp_etit_cols[1]:
                    st.markdown(kpi_card("Média Aderência Equipe", _tm_ader_str, COR_INFO), unsafe_allow_html=True)
                with _cmp_etit_cols[2]:
                    if _tm_ral_ader_pct:
                        st.markdown(kpi_card("Média RAL Ader. Equipe", f"{_tm_ral_ader_pct:.1f}", COR_INFO, suffix="%"), unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("##### 📋 Aderentes e Não Aderentes — RAL e REC" if not _is_admin else "##### 📋 Aderentes e Não Aderentes por Analista — RAL e REC")
            _tbl_ral_rec = etit_aderencia_ral_rec_por_analista(df_etit_filtrado)
            if not _tbl_ral_rec.empty:
                _disp_rr = _tbl_ral_rec.copy()
                _disp_rr["Nome"] = _disp_rr["Nome"].apply(primeiro_nome)
                _rename_rr = {"Nome": "Analista"}
                for _dem in ["RAL", "REC"]:
                    if f"{_dem}_Aderentes" in _disp_rr.columns:
                        _rename_rr[f"{_dem}_Aderentes"] = f"{_dem} Ader."
                    if f"{_dem}_Nao_Aderentes" in _disp_rr.columns:
                        _rename_rr[f"{_dem}_Nao_Aderentes"] = f"{_dem} N. Ader."
                _disp_rr = _disp_rr.drop(columns=[ETIT_COL_LOGIN], errors="ignore").rename(columns=_rename_rr)

                _green_rr = [c for c in _disp_rr.columns if "Ader." in c and "N." not in c]
                _red_rr   = [c for c in _disp_rr.columns if "N. Ader." in c]

                # % separados por RAL e REC para cada analista
                for _dem in ["RAL", "REC"]:
                    _a = f"{_dem} Ader."
                    _n = f"{_dem} N. Ader."
                    if _a in _disp_rr.columns and _n in _disp_rr.columns:
                        _tot = _disp_rr[_a] + _disp_rr[_n]
                        _disp_rr[f"% {_dem} Ader."]   = (_disp_rr[_a] / _tot * 100).round(1)
                        _disp_rr[f"% {_dem} N. Ader."] = (_disp_rr[_n] / _tot * 100).round(1)

                _pct_green = [c for c in _disp_rr.columns if c.startswith("% ") and "N." not in c]
                _pct_red   = [c for c in _disp_rr.columns if c.startswith("% ") and "N." in c]

                # Médias de referência da equipe (RAL/REC aderente e não aderente)
                if not _is_admin and (_tm_ral_ader_pct or _tm_rec_ader_pct):
                    _ref_items = []
                    if _tm_ral_ader_pct:
                        _ref_items.append(("% RAL Ader. (média equipe)", f"{_tm_ral_ader_pct:.1f}%"))
                    if _tm_ral_ader_avg is not None:
                        _ref_items.append(("RAL Aderentes (média equipe)", f"{_tm_ral_ader_avg:.1f}"))
                    if _tm_ral_nader_avg is not None:
                        _ref_items.append(("RAL N. Ader. (média equipe)", f"{_tm_ral_nader_avg:.1f}"))
                    if _tm_rec_ader_pct:
                        _ref_items.append(("% REC Ader. (média equipe)", f"{_tm_rec_ader_pct:.1f}%"))
                    if _tm_rec_ader_avg is not None:
                        _ref_items.append(("REC Aderentes (média equipe)", f"{_tm_rec_ader_avg:.1f}"))
                    if _tm_rec_nader_avg is not None:
                        _ref_items.append(("REC N. Ader. (média equipe)", f"{_tm_rec_nader_avg:.1f}"))
                    if _ref_items:
                        _mc_cols = st.columns(min(len(_ref_items), 3))
                        for _i, (_lbl, _val) in enumerate(_ref_items):
                            with _mc_cols[_i % 3]:
                                st.metric(_lbl, _val)
                elif _is_admin:
                    _abs_med_cols = _green_rr + _red_rr
                    if _abs_med_cols:
                        _mc_cols = st.columns(len(_abs_med_cols))
                        for _i, _col in enumerate(_abs_med_cols):
                            with _mc_cols[_i]:
                                st.metric(f"Média Equipe — {_col}", f"{_disp_rr[_col].mean():.1f}")

                _disp_rr = _disp_rr.reset_index(drop=True)
                _disp_rr.index += 1; _disp_rr.index.name = "#"
                _fmt_rr = {c: "{:.0f}" for c in _green_rr + _red_rr}
                for _c in _pct_green + _pct_red:
                    _fmt_rr[_c] = "{:.1f}%"
                _styled_rr = _disp_rr.style.format(_fmt_rr, na_rep="—")
                if _green_rr:
                    _styled_rr = _styled_rr.background_gradient(cmap="Greens", subset=_green_rr)
                if _red_rr:
                    _styled_rr = _styled_rr.background_gradient(cmap="Reds", subset=_red_rr)
                for _c in _pct_green:
                    _styled_rr = _styled_rr.background_gradient(cmap="RdYlGn", subset=[_c], vmin=50, vmax=100)
                for _c in _pct_red:
                    _styled_rr = _styled_rr.background_gradient(cmap="RdYlGn_r", subset=[_c], vmin=0, vmax=50)
                st.dataframe(_styled_rr, use_container_width=True)

            st.markdown("---")
            col_dem, col_tipo = st.columns(2)
            with col_dem:
                st.markdown("**Por Demanda (RAL/REC)**")
                dem = etit_por_demanda(df_etit_filtrado)
                if not dem.empty:
                    dem["Aderência %"] = (dem["Aderentes"] / dem["Eventos"] * 100).round(1)
                    st.dataframe(
                        dem.rename(columns={"TMA_Medio": "TMA", "TMR_Medio": "TMR"})
                           .style.format({"Aderência %": "{:.1f}", "TMA": _fmt_hms, "TMR": _fmt_hms}, na_rep="—"),
                        use_container_width=True, hide_index=True,
                    )
            with col_tipo:
                st.markdown("**Por Tipo**")
                tipo = etit_por_tipo(df_etit_filtrado)
                if not tipo.empty:
                    tipo["Aderência %"] = (tipo["Aderentes"] / tipo["Eventos"] * 100).round(1)
                    st.dataframe(
                        tipo.style.format({"Aderência %": "{:.1f}"}, na_rep="—")
                            .background_gradient(cmap="Purples", subset=["Eventos"]),
                        use_container_width=True, hide_index=True,
                    )

            _etit_eq = df_etit_filtrado[
                ~df_etit_filtrado[ETIT_COL_LOGIN].str.upper().isin({l.upper() for l in LIDERES_IDS})
            ].copy()

            col_causa, col_reg = st.columns(2)
            with col_causa:
                st.markdown("**Por Causa**")
                causa = etit_por_causa(df_etit_filtrado)
                if not causa.empty:
                    causa["Aderência %"] = (causa["Aderentes"] / causa["Eventos"] * 100).round(1)
                    st.dataframe(
                        causa.head(15).style.format({"Aderência %": "{:.1f}"}, na_rep="—")
                            .background_gradient(cmap="Purples", subset=["Eventos"]),
                        use_container_width=True, hide_index=True,
                    )
            with col_reg:
                st.markdown(f"**Por Grupo (IN_GRUPO) — Regional {REGIONAL_FILTRO}**")
                if ETIT_COL_GRUPO in _etit_eq.columns:
                    _gg_geral = _etit_eq.groupby(ETIT_COL_GRUPO).agg(
                        Eventos=(ETIT_COL_VOLUME, "sum"),
                        Aderentes=(ETIT_COL_INDICADOR_VAL, "sum"),
                    ).reset_index().rename(columns={ETIT_COL_GRUPO: "Grupo"})
                    _gg_geral["Aderência %"] = (_gg_geral["Aderentes"] / _gg_geral["Eventos"] * 100).round(1)
                    _gg_geral = _gg_geral.sort_values("Eventos", ascending=False).reset_index(drop=True)
                    if not _gg_geral.empty:
                        if _is_admin:
                            _bg_e = _gg_geral.loc[_gg_geral["Aderência %"].idxmax()]
                            _bw_e = _gg_geral.loc[_gg_geral["Aderência %"].idxmin()]
                            st.caption(
                                f"🟢 Melhor: **{_bg_e['Grupo']}** ({_bg_e['Aderência %']:.1f}%) · "
                                f"🔴 Pior: **{_bw_e['Grupo']}** ({_bw_e['Aderência %']:.1f}%)"
                            )
                        st.dataframe(
                            _gg_geral.style.format({"Aderência %": "{:.1f}"}, na_rep="—")
                                .background_gradient(cmap="RdYlGn", subset=["Aderência %"], vmin=50, vmax=100)
                                .background_gradient(cmap="Purples", subset=["Eventos"]),
                            use_container_width=True, hide_index=True,
                        )

            st.markdown("**Por Turno**")
            turno = etit_por_turno(df_etit_filtrado)
            if not turno.empty:
                turno["Aderência %"] = (turno["Aderentes"] / turno["Eventos"] * 100).round(1)
                col_t1, col_t2 = st.columns([1, 2])
                with col_t1:
                    st.dataframe(turno.style.format({"Aderência %": "{:.1f}"}, na_rep="—"),
                                 use_container_width=True, hide_index=True)
                with col_t2:
                    st.bar_chart(turno[["Turno", "Eventos"]].set_index("Turno"), color="#8E44AD", height=250)

            if _is_admin:
                st.markdown("---")
                st.markdown("#### 💡 Insights — ETIT por Evento")
                _etit_insights = []
                _ader_cor = "🟢" if etit_pct_ader >= 90 else ("🟡" if etit_pct_ader >= 70 else "🔴")
                _etit_insights.append(
                    f"- {_ader_cor} **Aderência média da equipe:** {etit_pct_ader:.1f}% "
                    f"em **{int(etit_total_eventos):,} eventos** ({etit_n_analistas} analistas)."
                )
                if not resumo_etit.empty and "Aderencia_Pct" in resumo_etit.columns:
                    _r_ord = resumo_etit.sort_values("Aderencia_Pct", ascending=False)
                    _best = _r_ord.iloc[0]
                    _worst = _r_ord.iloc[-1]
                    _etit_insights.append(
                        f"- 🏅 **Melhor aderência:** {primeiro_nome(_best['Nome'])} "
                        f"({_best['Aderencia_Pct']:.1f}%)."
                    )
                    _etit_insights.append(
                        f"- ⚠️ **Menor aderência:** {primeiro_nome(_worst['Nome'])} "
                        f"({_worst['Aderencia_Pct']:.1f}%)."
                    )
                    _abaixo = _r_ord[_r_ord["Aderencia_Pct"] < 70]
                    if not _abaixo.empty:
                        _nomes_ab = ", ".join(primeiro_nome(n) for n in _abaixo["Nome"].tolist())
                        _etit_insights.append(
                            f"- 🔴 **Abaixo de 70%:** {len(_abaixo)} analistas — {_nomes_ab}."
                        )
                    else:
                        _etit_insights.append("- ✅ **Nenhum analista abaixo de 70%** no período.")
                if pd.notna(etit_tma_geral) and pd.notna(etit_tmr_geral):
                    _etit_insights.append(
                        f"- ⏱️ **TMA médio:** {_fmt_hms(etit_tma_geral)} · **TMR médio:** {_fmt_hms(etit_tmr_geral)}."
                    )
                if not resumo_etit.empty and "RAL_Count" in resumo_etit.columns:
                    _ral_total = int(resumo_etit["RAL_Count"].sum())
                    if _ral_total > 0:
                        _etit_insights.append(f"- 📌 **Total de RAL no período:** {_ral_total}.")
                for _ins in _etit_insights:
                    st.markdown(_ins)

            st.markdown("---")
            etit_show_cols = [
                ETIT_COL_LOGIN, "Nome", "Setor", ETIT_COL_DEMANDA, ETIT_COL_NOTA,
                ETIT_COL_STATUS, ETIT_COL_TIPO, ETIT_COL_CAUSA,
                ETIT_COL_REGIONAL, ETIT_COL_CIDADE, ETIT_COL_UF,
                ETIT_COL_TURNO, ETIT_COL_TMA, ETIT_COL_TMR,
                ETIT_COL_DT_ACIONAMENTO, ETIT_COL_ANOMES,
            ]
            etit_show_cols = [c for c in etit_show_cols if c in df_etit_filtrado.columns]
            st.dataframe(
                df_etit_filtrado[etit_show_cols].sort_values(
                    [ETIT_COL_DT_ACIONAMENTO] if ETIT_COL_DT_ACIONAMENTO in df_etit_filtrado.columns else ["Nome"],
                    ascending=False,
                ),
                use_container_width=True, height=500,
            )
            csv_etit = df_etit_filtrado[etit_show_cols].to_csv(index=False).encode("utf-8")
            st.download_button("📥 Baixar ETIT filtrado (CSV)", csv_etit, "etit_por_evento_equipe.csv", "text/csv")

        if _is_super_admin:
            st.markdown("---")
            render_fora_equipe_madrugada(
                _resumo_fora_etit,
                ganhos_label="Aderentes",
                perdas_label="Não Aderentes",
                pct_label="Aderência %",
                caption="Analistas que aparecem na planilha **ETIT POR EVENTO** mas não fazem parte da equipe monitorada.",
            )


# ---- TAB: INDICADORES RESIDENCIAL ----
if res_ind_loaded and _tab_res_idx is not None:
    with tabs[_tab_res_idx]:
        st.markdown("#### 🏠 Indicadores Residencial — ETIT Fibra HFC · ETIT GPON · Assert. Acion. GPON")
        if df_res_filtrado.empty:
            st.warning("Nenhum dado encontrado com os filtros atuais.")
        else:
            kpis_df = res_kpis_por_indicador(df_res_filtrado)
            st.markdown("##### 📊 Resumo por Indicador")
            n_cols = len(kpis_df)
            ind_cols = st.columns(n_cols) if n_cols > 0 else []
            for i, row in kpis_df.iterrows():
                ind_name = row["Indicador"]
                label = RES_IND_LABELS.get(ind_name, ind_name)
                color = RES_IND_COLORS.get(ind_name, "#5DADE2")
                vol = int(row["Volume"]); ader = int(row["Aderentes"]); pct = row["Aderencia_Pct"]
                tma_str = f"TMA: {_fmt_hms(row['TMA_Medio'])}" if "TMA_Medio" in row and pd.notna(row.get("TMA_Medio")) else ""
                tmr_str = f"TMR: {_fmt_hms(row['TMR_Medio'])}" if "TMR_Medio" in row and pd.notna(row.get("TMR_Medio")) else ""
                extra = " · ".join(filter(None, [tma_str, tmr_str]))
                pct_color = COR_SUCESSO if pct >= 90 else (COR_ALERTA if pct >= 70 else COR_PERIGO)
                with ind_cols[i]:
                    st.markdown(
                        f'<div class="res-ind-card" style="border-top-color:{color};">'
                        f'<div class="ri-title">{label}</div>'
                        f'<div class="ri-vol" style="color:{color};">{vol:,}</div>'
                        f'<div class="ri-pct" style="color:{pct_color};">✅ {ader:,} aderentes &nbsp;·&nbsp; {pct:.1f}%</div>'
                        f'<div class="ri-detail">{extra}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # Breakdown por Turno
            if RES_COL_TURNO in df_res_filtrado.columns:
                st.markdown("")
                st.markdown("##### 🕐 Aderência por Turno")
                _turno_order = ["Manhã", "Tarde", "Madrugada"]
                _tg = df_res_filtrado.groupby(RES_COL_TURNO).agg(
                    Volume=(RES_COL_VOLUME, "sum"),
                    Aderentes=("ADERENTE", "sum"),
                ).reset_index()
                _tg["Aderência %"] = (_tg["Aderentes"] / _tg["Volume"] * 100).round(1)
                _tg["_ord"] = _tg[RES_COL_TURNO].map({t: i for i, t in enumerate(_turno_order)}).fillna(99)
                _tg = _tg.sort_values("_ord").drop(columns="_ord").rename(columns={RES_COL_TURNO: "Turno"})
                st.dataframe(
                    _tg[["Turno", "Volume", "Aderentes", "Aderência %"]].style
                    .format({"Aderência %": "{:.1f}"})
                    .background_gradient(cmap="RdYlGn", subset=["Aderência %"], vmin=50, vmax=100),
                    use_container_width=True, hide_index=True,
                )

            st.markdown("")
            st.markdown("##### 📈 Comparativo de Aderência por Indicador")
            if not kpis_df.empty:
                chart_ader = kpis_df[["Indicador", "Aderencia_Pct"]].copy()
                chart_ader["Indicador"] = chart_ader["Indicador"].map(RES_IND_LABELS)
                chart_ader = chart_ader.set_index("Indicador")
                chart_ader.columns = ["Aderência %"]
                st.bar_chart(chart_ader, color=COR_SUCESSO, height=300)

            st.markdown("---")
            ind_to_show = (
                [res_ind_selecionado] if res_ind_selecionado != "Todos" else RES_INDICADORES_FILTRO
            )
            ind_to_show = [i for i in ind_to_show if i in df_res_filtrado[RES_COL_INDICADOR_NOME].unique()]

            for ind in ind_to_show:
                label = RES_IND_LABELS.get(ind, ind)
                color = RES_IND_COLORS.get(ind, "#5DADE2")
                sub = df_res_filtrado[df_res_filtrado[RES_COL_INDICADOR_NOME] == ind]
                if sub.empty:
                    continue
                vol_total = int(sub[RES_COL_VOLUME].sum())
                ader_total = int(sub["ADERENTE"].sum())
                pct_total = (ader_total / vol_total * 100) if vol_total > 0 else 0

                with st.expander(f"🔍 {label} — {vol_total:,} registros · {pct_total:.1f}% aderência",
                                 expanded=(len(ind_to_show) == 1)):
                    # Filtro Brownfield / Greenfield — ETIT GPON e Assertividade Acionamento GPON
                    # Mantém o escopo da equipe do usuário (não vaza Luiz/Vinícius para Nelson).
                    # Pré-inicializa a chave em session_state para reduzir a chance da primeira
                    # interação do radio resetar o estado das abas.
                    if ind in {RES_IND_ETIT_GPON, RES_IND_ASSERT_GPON} and RES_COL_SERVICO in sub.columns:
                        _radio_key = f"res_nat_{ind}"
                        if _radio_key not in st.session_state:
                            st.session_state[_radio_key] = "Todos"
                        _serv_sel = st.radio(
                            "🌿 Serviço",
                            options=["Todos", "Brownfield", "Greenfield"],
                            horizontal=True,
                            key=_radio_key,
                        )
                        if _serv_sel != "Todos":
                            sub = sub[
                                sub[RES_COL_SERVICO].astype(str).str.strip().str.upper()
                                == _serv_sel.upper()
                            ].copy()
                            vol_total  = int(sub[RES_COL_VOLUME].sum())  if not sub.empty else 0
                            ader_total = int(sub["ADERENTE"].sum())      if not sub.empty else 0
                            pct_total  = (ader_total / vol_total * 100) if vol_total > 0 else 0
                            if sub.empty:
                                st.caption(
                                    f"⚠️ Nenhum caso **{_serv_sel}** registrado pela sua equipe "
                                    "neste período/turno."
                                )

                    sk1, sk2, sk3, sk4, sk5 = st.columns(5)
                    with sk1:
                        st.markdown(kpi_card("Volume", f"{vol_total:,}", color), unsafe_allow_html=True)
                    with sk2:
                        st.markdown(kpi_card("Aderentes", f"{ader_total:,}", COR_SUCESSO), unsafe_allow_html=True)
                    with sk3:
                        pct_c = COR_SUCESSO if pct_total >= 90 else (COR_ALERTA if pct_total >= 70 else COR_PERIGO)
                        st.markdown(kpi_card("Aderência", f"{pct_total:.1f}", pct_c, suffix="%"), unsafe_allow_html=True)
                    with sk4:
                        if RES_TMA in sub.columns:
                            st.markdown(kpi_card("TMA Médio", _fmt_hms(sub[RES_TMA].mean()), COR_INFO), unsafe_allow_html=True)
                    with sk5:
                        if RES_TMR in sub.columns:
                            st.markdown(kpi_card("TMR Médio", _fmt_hms(sub[RES_TMR].mean()), COR_ALERTA), unsafe_allow_html=True)

                    # ── Ranking por Analista ──────────────────────────────
                    if _is_admin:
                        _anl_res = res_por_analista(sub, indicador=ind)
                        if not _anl_res.empty:
                            st.markdown("**👤 Por Analista**")
                            _anl_tbl = _anl_res[["Nome", "Setor", "Volume", "Aderentes", "Aderencia_Pct"]].copy()
                            _anl_tbl.columns = ["Analista", "Setor", "Volume", "Aderentes", "Aderência %"]
                            _anl_tbl.index = range(1, len(_anl_tbl) + 1)
                            _anl_tbl.index.name = "#"
                            _col_anl, _col_chart = st.columns([1, 1])
                            with _col_anl:
                                st.dataframe(
                                    _anl_tbl.style
                                        .format({"Aderência %": "{:.1f}"}, na_rep="—")
                                        .background_gradient(cmap="RdYlGn", subset=["Aderência %"], vmin=50, vmax=100)
                                        .background_gradient(cmap="Blues", subset=["Volume"]),
                                    use_container_width=True,
                                )
                            with _col_chart:
                                _chart_anl = _anl_res[["Nome", "Aderencia_Pct"]].copy()
                                _chart_anl["Nome"] = _chart_anl["Nome"].apply(primeiro_nome)
                                _chart_anl = _chart_anl.set_index("Nome").sort_values("Aderencia_Pct")
                                st.bar_chart(_chart_anl, height=max(250, len(_chart_anl) * 25), color=color)

                    cr, cn = st.columns(2)
                    with cr:
                        if RES_COL_GRUPO in sub.columns:
                            st.markdown(f"**Por Grupo (IN_GRUPO) — Regional {REGIONAL_FILTRO}**")
                            _rg_sub2 = sub.groupby(RES_COL_GRUPO).agg(
                                Volume=(RES_COL_VOLUME, "sum"),
                                Aderentes=("ADERENTE", "sum"),
                            ).reset_index()
                            _rg_sub2["Aderência %"] = (_rg_sub2["Aderentes"] / _rg_sub2["Volume"] * 100).round(1)
                            _rg_sub2 = _rg_sub2.sort_values("Volume", ascending=False).reset_index(drop=True)
                            if not _rg_sub2.empty:
                                if _is_admin:
                                    _rg_best2 = _rg_sub2.loc[_rg_sub2["Aderência %"].idxmax()]
                                    _rg_worst2 = _rg_sub2.loc[_rg_sub2["Aderência %"].idxmin()]
                                    st.caption(
                                        f"🟢 Melhor: **{_rg_best2[RES_COL_GRUPO]}** ({_rg_best2['Aderência %']:.1f}%) · "
                                        f"🔴 Pior: **{_rg_worst2[RES_COL_GRUPO]}** ({_rg_worst2['Aderência %']:.1f}%)"
                                    )
                                st.dataframe(
                                    _rg_sub2.style
                                        .format({"Aderência %": "{:.1f}"}, na_rep="—")
                                        .background_gradient(cmap="Blues", subset=["Volume"])
                                        .background_gradient(cmap="RdYlGn", subset=["Aderência %"], vmin=50, vmax=100),
                                    use_container_width=True, hide_index=True,
                                )
                    with cn:
                        st.markdown("**Por Natureza**")
                        nat_df = res_por_natureza(sub)
                        if not nat_df.empty:
                            st.dataframe(
                                nat_df.style.format({"Aderencia_Pct": "{:.1f}"}, na_rep="—"),
                                use_container_width=True, hide_index=True,
                            )
                        st.markdown("**Por Impacto**")
                        imp_df = res_por_impacto(sub)
                        if not imp_df.empty:
                            st.dataframe(imp_df.style.format({"Aderencia_Pct": "{:.1f}"}, na_rep="—"),
                                         use_container_width=True, hide_index=True)

                    st.markdown("**Top 15 Soluções**")
                    sol_df = res_por_solucao(sub, top_n=15)
                    if not sol_df.empty:
                        st.dataframe(
                            sol_df.style.format({"Aderencia_Pct": "{:.1f}"}, na_rep="—")
                                .background_gradient(cmap="YlOrRd", subset=["Volume"]),
                            use_container_width=True, hide_index=True, height=350,
                        )

            st.markdown("---")
            st.markdown(f"##### 📋 Tabela Consolidada por Grupo (IN_GRUPO) e Indicador — Regional {REGIONAL_FILTRO}")
            if not kpis_df.empty and RES_COL_GRUPO in df_res_filtrado.columns:
                pivot_list = []
                for ind in RES_INDICADORES_FILTRO:
                    sub = df_res_filtrado[df_res_filtrado[RES_COL_INDICADOR_NOME] == ind]
                    if sub.empty:
                        continue
                    _gdf = sub.groupby(RES_COL_GRUPO).agg(
                        Volume=(RES_COL_VOLUME, "sum"),
                        Aderentes=("ADERENTE", "sum"),
                    ).reset_index()
                    _gdf["Aderencia_Pct"] = (_gdf["Aderentes"] / _gdf["Volume"] * 100).round(1)
                    _gdf["Indicador"] = RES_IND_LABELS.get(ind, ind)
                    pivot_list.append(_gdf)
                if pivot_list:
                    all_grp_res = pd.concat(pivot_list, ignore_index=True)
                    try:
                        pivot_tbl = all_grp_res.pivot_table(
                            index=RES_COL_GRUPO, columns="Indicador",
                            values="Aderencia_Pct", aggfunc="first",
                        ).reset_index()
                        pivot_tbl = pivot_tbl.rename(columns={RES_COL_GRUPO: "Grupo"})
                        st.dataframe(
                            pivot_tbl.style.format(
                                {c: "{:.1f}" for c in pivot_tbl.columns if c != "Grupo"}, na_rep="—"
                            ).background_gradient(cmap="RdYlGn", vmin=50, vmax=100,
                                subset=[c for c in pivot_tbl.columns if c != "Grupo"]),
                            use_container_width=True, hide_index=True,
                        )
                    except Exception:
                        st.dataframe(all_grp_res, use_container_width=True, hide_index=True)

            if _is_admin:
                st.markdown("---")
                st.markdown("#### 💡 Insights — Indicadores Residencial")
                _res_insights = []
                _res_vol_total = int(kpis_df["Volume"].sum()) if not kpis_df.empty else 0
                _res_ader_total = int(kpis_df["Aderentes"].sum()) if not kpis_df.empty else 0
                _res_pct_global = (_res_ader_total / _res_vol_total * 100) if _res_vol_total > 0 else 0
                _cor_res = "🟢" if _res_pct_global >= 90 else ("🟡" if _res_pct_global >= 70 else "🔴")
                _res_insights.append(
                    f"- {_cor_res} **Volume total:** {_res_vol_total:,} eventos · "
                    f"**Aderência global:** {_res_pct_global:.1f}%."
                )
                if not kpis_df.empty:
                    for _, _krow in kpis_df.iterrows():
                        _lbl = RES_IND_LABELS.get(_krow["Indicador"], _krow["Indicador"])
                        _res_insights.append(
                            f"- 📊 **{_lbl}:** {int(_krow['Volume']):,} eventos · "
                            f"{_krow['Aderencia_Pct']:.1f}% aderência."
                        )
                    _kord = kpis_df.sort_values("Aderencia_Pct", ascending=False)
                    _best_ind = RES_IND_LABELS.get(_kord.iloc[0]["Indicador"], _kord.iloc[0]["Indicador"])
                    _worst_ind = RES_IND_LABELS.get(_kord.iloc[-1]["Indicador"], _kord.iloc[-1]["Indicador"])
                    _res_insights.append(
                        f"- 🏅 **Melhor indicador:** {_best_ind} ({_kord.iloc[0]['Aderencia_Pct']:.1f}%) · "
                        f"⚠️ **Pior:** {_worst_ind} ({_kord.iloc[-1]['Aderencia_Pct']:.1f}%)."
                    )
                try:
                    if RES_COL_TURNO in df_res_filtrado.columns and not _tg.empty:
                        _tg_ord = _tg.sort_values("Aderência %", ascending=False)
                        _res_insights.append(
                            f"- 🕐 **Melhor turno:** {_tg_ord.iloc[0]['Turno']} "
                            f"({_tg_ord.iloc[0]['Aderência %']:.1f}%) · "
                            f"**Pior:** {_tg_ord.iloc[-1]['Turno']} "
                            f"({_tg_ord.iloc[-1]['Aderência %']:.1f}%)."
                        )
                except NameError:
                    pass
                if RES_COL_GRUPO in df_res_filtrado.columns:
                    _grp_vol = df_res_filtrado.groupby(RES_COL_GRUPO)[RES_COL_VOLUME].sum().sort_values(ascending=False)
                    if not _grp_vol.empty:
                        _res_insights.append(
                            f"- 📍 **Top grupo por volume:** {_grp_vol.index[0]} "
                            f"({int(_grp_vol.iloc[0]):,} eventos)."
                        )
                for _ins in _res_insights:
                    st.markdown(_ins)

            st.markdown("---")
            res_show_cols = [
                RES_COL_INDICADOR_NOME, RES_COL_ID_MOSTRA, RES_COL_VOLUME,
                "ADERENTE", RES_COL_STATUS, RES_REGIONAL, RES_COL_NATUREZA,
                RES_COL_IMPACTO, RES_COL_SOLUCAO, RES_TMA, RES_TMR,
                RES_COL_DT_INICIO, RES_ANOMES,
            ]
            res_show_cols = [c for c in res_show_cols if c in df_res_filtrado.columns]
            st.dataframe(
                df_res_filtrado[res_show_cols].sort_values(
                    [RES_COL_DT_INICIO] if RES_COL_DT_INICIO in df_res_filtrado.columns else [RES_COL_INDICADOR_NOME],
                    ascending=False,
                ),
                use_container_width=True, height=400,
            )
            csv_res = df_res_filtrado[res_show_cols].to_csv(index=False).encode("utf-8")
            st.download_button("📥 Baixar Indicadores Residencial (CSV)", csv_res, "indicadores_residencial.csv", "text/csv")

        _res_ganhos = {
            RES_IND_ETIT_FIBRA_HFC:  "Aderentes",
            RES_IND_ETIT_GPON:       "Aderentes",
            RES_IND_ASSERT_GPON:     "Aderentes",
        }
        _res_perdas = {
            RES_IND_ETIT_FIBRA_HFC:  "Não Aderentes",
            RES_IND_ETIT_GPON:       "Não Aderentes",
            RES_IND_ASSERT_GPON:     "Não Aderentes",
        }

        if _is_super_admin and _resumo_fora_res:
            st.markdown("---")
            for _rind_key, _rind_df in _resumo_fora_res.items():
                _rind_label = RES_IND_LABELS.get(_rind_key, _rind_key)
                render_fora_equipe_madrugada(
                    _rind_df,
                    ganhos_label=_res_ganhos.get(_rind_key, "Aderentes"),
                    perdas_label=_res_perdas.get(_rind_key, "Não Aderentes"),
                    pct_label="Aderência %",
                    caption=f"Analistas externos — **{_rind_label}** — Madrugada (22:00–05:59).",
                )

        if _is_coord and _resumo_fora_res_coord:
            st.markdown("---")
            for _rind_key, _rind_df in _resumo_fora_res_coord.items():
                _rind_label = RES_IND_LABELS.get(_rind_key, _rind_key)
                render_fora_equipe_madrugada(
                    _rind_df,
                    ganhos_label=_res_ganhos.get(_rind_key, "Aderentes"),
                    perdas_label=_res_perdas.get(_rind_key, "Não Aderentes"),
                    pct_label="Aderência %",
                    caption=f"Analistas externos da **Madrugada** — atividade **diurna (06:00–21:59)** em **{_rind_label}**.",
                )


# ---- TAB: INDICADORES TOA ----
if toa_loaded and _tab_toa_idx is not None:
    with tabs[_tab_toa_idx]:
        if "Setor" in df_toa.columns and setor_selecionado != "Todos":
            df_toa = df_toa[df_toa["Setor"] == setor_selecionado].copy()

        anomes_str = str(toa_anomes) if toa_anomes else "?"
        st.markdown(
            f"#### 📋 Indicadores TOA — Tarefas Canceladas · Tempo de Validação do Formulário · "
            f"Período: **{anomes_str}** (mês mais recente)"
        )
        st.caption(
            "ℹ️ Dados filtrados automaticamente para o mês mais recente disponível na planilha. "
            "Tarefas Canceladas: menor = melhor. Tempo de Validação: maior aderência% = melhor."
        )

        # ---- KPIs gerais ----
        resumo_toa = toa_resumo_por_indicador(df_toa)
        if not resumo_toa.empty:
            tk_cols = st.columns(len(resumo_toa) * 2)
            ci = 0
            for _, trow in resumo_toa.iterrows():
                ind_nome = trow["Indicador"]
                cor = TOA_IND_COLORS.get(ind_nome, COR_INFO)
                label = TOA_IND_LABELS.get(ind_nome, ind_nome)
                with tk_cols[ci]:
                    st.markdown(kpi_card(f"Total — {label[:20]}", f"{trow['Total']:,}", cor), unsafe_allow_html=True)
                ci += 1
                with tk_cols[ci]:
                    if ind_nome == TOA_IND_CANCELADAS:
                        # Para canceladas: mostrar total (menor = melhor)
                        st.markdown(kpi_card("Canceladas (⚠️ menor melhor)", f"{trow['Total']:,}", COR_PERIGO), unsafe_allow_html=True)
                    else:
                        pct = trow["Aderencia_Pct"]
                        pct_c = COR_SUCESSO if pct >= 90 else (COR_ALERTA if pct >= 70 else COR_PERIGO)
                        st.markdown(kpi_card(f"Aderência — {label[:15]}", f"{pct:.1f}", pct_c, suffix="%"), unsafe_allow_html=True)
                ci += 1

        st.markdown("---")

        # Comparação com a equipe (apenas não-admin)
        if not _is_admin:
            st.markdown("##### 📊 Você vs Equipe — TOA")
            _toa_cmp_items = []
            _df_canc_u = toa_canceladas_por_analista(df_toa)
            _u_canc = int(_df_canc_u["Canceladas"].sum()) if not _df_canc_u.empty else 0
            _toa_cmp_items.append(("Suas Canceladas", str(_u_canc), COR_PERIGO if _u_canc > 0 else COR_SUCESSO))
            if _tm_toa_canc_avg is not None:
                _toa_cmp_items.append(("Média Canceladas Equipe", f"{_tm_toa_canc_avg:.1f}", COR_INFO))
            _df_val_u = toa_validacao_por_analista(df_toa)
            if not _df_val_u.empty and "Aderencia_Pct" in _df_val_u.columns:
                _u_val_pct = _df_val_u["Aderencia_Pct"].mean()
                _vc = COR_SUCESSO if _u_val_pct >= 90 else (COR_ALERTA if _u_val_pct >= 70 else COR_PERIGO)
                _toa_cmp_items.append(("Sua Ader. Validação", f"{_u_val_pct:.1f}", _vc, "%"))
            if _tm_toa_val_pct_avg is not None:
                _toa_cmp_items.append(("Média Ader. Validação Equipe", f"{_tm_toa_val_pct_avg:.1f}", COR_INFO, "%"))
            if _tm_toa_val_tmr_avg is not None:
                _toa_cmp_items.append(("TMR Médio Equipe (min)", f"{_tm_toa_val_tmr_avg:.1f}", COR_INFO))
            if _toa_cmp_items:
                _tcmp_cols = st.columns(min(len(_toa_cmp_items), 3))
                for _i, _item in enumerate(_toa_cmp_items):
                    with _tcmp_cols[_i % 3]:
                        _suffix = _item[3] if len(_item) > 3 else ""
                        st.markdown(kpi_card(_item[0], _item[1], _item[2], suffix=_suffix), unsafe_allow_html=True)
            st.markdown("---")

        # =============================================
        # SEÇÃO 1: TAREFAS CANCELADAS
        # =============================================
        st.markdown("### ❌ Tarefas Canceladas")
        st.caption("Cada linha representa uma tarefa cancelada por um analista da equipe no período.")

        st.markdown("##### 🏆 Ranking por Analista")
        df_canc_anal = toa_canceladas_por_analista(df_toa)
        if not df_canc_anal.empty:
            df_canc_anal["Analista"] = df_canc_anal["Nome"].apply(primeiro_nome)
            df_canc_anal["TMR Médio (h)"] = df_canc_anal["TMR_Medio_h"]
            tbl_canc = df_canc_anal[["Analista", "Setor", "Canceladas", "TMR Médio (h)"]].copy()
            tbl_canc = tbl_canc.reset_index(drop=True)
            tbl_canc.index += 1; tbl_canc.index.name = "#"
            st.dataframe(
                tbl_canc.style
                    .format({"TMR Médio (h)": "{:.2f}"}, na_rep="—")
                    .background_gradient(cmap="Reds", subset=["Canceladas"]),
                use_container_width=True,
            )
            # Mini bar chart
            chart_canc = df_canc_anal[["Analista", "Canceladas"]].set_index("Analista").sort_values("Canceladas")
            st.bar_chart(chart_canc, color="#E74C3C", height=300)

        # Breakdown por Rede e Grupo (linha abaixo)
        col_cr, col_creg = st.columns(2)
        with col_cr:
            st.markdown("##### 📡 Por Rede")
            df_canc_rede = toa_canceladas_por_rede(df_toa)
            if not df_canc_rede.empty:
                st.dataframe(
                    df_canc_rede.style.background_gradient(cmap="Reds", subset=["Canceladas"]),
                    use_container_width=True, hide_index=True,
                )
        with col_creg:
            st.markdown(f"##### 🗺️ Por Grupo (IN_GRUPO) — Regional {REGIONAL_FILTRO}")
            _canc_grp_col = "IN_GRUPO"
            if _canc_grp_col in df_toa.columns:
                _df_canc_grp = df_toa[df_toa["INDICADOR_NOME"] == "TAREFAS CANCELADAS"]
                if not _df_canc_grp.empty:
                    _cg = _df_canc_grp.groupby(_canc_grp_col).size().reset_index(name="Canceladas")
                    _cg.columns = ["Grupo", "Canceladas"]
                    _cg = _cg.sort_values("Canceladas", ascending=False).reset_index(drop=True)
                    st.dataframe(
                        _cg.style.background_gradient(cmap="Reds", subset=["Canceladas"]),
                        use_container_width=True, hide_index=True,
                    )

        # Evolução diária canceladas
        st.markdown("##### 📅 Evolução Diária")
        df_canc_evo = toa_canceladas_evolucao(df_toa)
        if not df_canc_evo.empty:
            st.area_chart(df_canc_evo[["Data", "Canceladas"]].set_index("Data"), color="#E74C3C", height=220)

        # Detalhe de canceladas por setor (apenas admin)
        if _is_admin and "Analista" in df_canc_anal.columns:
            st.markdown("##### 🏢🏠 Canceladas por Setor")
            c_emp_c, c_res_c = st.columns(2)
            for col_s, setor_s in [(c_emp_c, "EMPRESARIAL"), (c_res_c, "RESIDENCIAL")]:
                icon_s = "🏢" if setor_s == "EMPRESARIAL" else "🏠"
                with col_s:
                    st.markdown(f"**{icon_s} {setor_s}**")
                    sub_s = df_canc_anal[df_canc_anal["Setor"] == setor_s][["Analista", "Canceladas", "TMR Médio (h)"]].copy()
                    if sub_s.empty:
                        st.caption("Nenhum registro.")
                    else:
                        sub_s = sub_s.reset_index(drop=True); sub_s.index += 1; sub_s.index.name = "#"
                        st.dataframe(
                            sub_s.style.format({"TMR Médio (h)": "{:.2f}"}).background_gradient(cmap="Reds", subset=["Canceladas"]),
                            use_container_width=True,
                        )

        st.markdown("---")

        # =============================================
        # SEÇÃO 2: TEMPO DE VALIDAÇÃO DO FORMULÁRIO
        # =============================================
        st.markdown("### ✅ Tempo de Validação do Formulário")
        st.caption("Aderência ao tempo máximo permitido para validar o formulário TOA. Maior aderência% = melhor.")

        _df_val_geral = df_toa[df_toa["INDICADOR_NOME"] == TOA_IND_VALIDACAO] if "INDICADOR_NOME" in df_toa.columns else pd.DataFrame()
        if not _df_val_geral.empty:
            _val_total  = int(_df_val_geral["ADERENTE"].count()) if "ADERENTE" in _df_val_geral.columns else 0
            _val_ader   = int(_df_val_geral["ADERENTE"].sum())   if "ADERENTE" in _df_val_geral.columns else 0
            _val_n_ader = _val_total - _val_ader
            _val_pct    = (_val_ader / _val_total * 100) if _val_total > 0 else 0
            _val_tmr    = _df_val_geral["TMR_min"].mean() if "TMR_min" in _df_val_geral.columns else None
            _vk1, _vk2, _vk3, _vk4, _vk5 = st.columns(5)
            with _vk1:
                st.markdown(kpi_card("Total", f"{_val_total:,}", COR_INFO), unsafe_allow_html=True)
            with _vk2:
                st.markdown(kpi_card("Aderentes", f"{_val_ader:,}", COR_SUCESSO), unsafe_allow_html=True)
            with _vk3:
                st.markdown(kpi_card("Não Aderentes", f"{_val_n_ader:,}", COR_PERIGO), unsafe_allow_html=True)
            with _vk4:
                _pct_c = COR_SUCESSO if _val_pct >= 90 else (COR_ALERTA if _val_pct >= 70 else COR_PERIGO)
                st.markdown(kpi_card("Aderência", f"{_val_pct:.1f}", _pct_c, suffix="%"), unsafe_allow_html=True)
            with _vk5:
                if _val_tmr is not None and pd.notna(_val_tmr):
                    st.markdown(kpi_card("TMR Médio (min)", f"{_val_tmr:.1f}", COR_ALERTA), unsafe_allow_html=True)

        col_val1, col_val2 = st.columns([1, 1])

        with col_val1:
            st.markdown("##### 🏆 Ranking por Analista")
            df_val_anal = toa_validacao_por_analista(df_toa)
            if not df_val_anal.empty:
                df_val_anal["Analista"] = df_val_anal["Nome"].apply(primeiro_nome)
                tbl_val = df_val_anal[["Analista", "Setor", "Total", "Aderentes", "Aderencia_Pct", "TMR_Medio_min"]].copy()
                tbl_val.columns = ["Analista", "Setor", "Total", "Aderentes", "Aderência %", "TMR Médio (min)"]
                tbl_val = tbl_val.reset_index(drop=True)
                tbl_val.index += 1; tbl_val.index.name = "#"
                styled_val = tbl_val.style.format(
                    {"Aderência %": "{:.1f}", "TMR Médio (min)": "{:.1f}"}, na_rep="—"
                )
                styled_val = styled_val.background_gradient(cmap="RdYlGn", subset=["Aderência %"], vmin=40, vmax=100)
                styled_val = styled_val.background_gradient(cmap="RdYlGn_r", subset=["TMR Médio (min)"], vmin=5, vmax=60)
                st.dataframe(styled_val, use_container_width=True)

                # Destaques (apenas admin — non-admin só tem 1 analista)
                if _is_admin and len(tbl_val) >= 2:
                    best_v = tbl_val.iloc[0]
                    worst_v = tbl_val.iloc[-1]
                    cv1, cv2 = st.columns(2)
                    with cv1:
                        st.markdown(f"""<div class="perf-card perf-best">
                            <div class="p-title">🏆 Melhor Aderência</div>
                            <div class="p-name" style="color:#2ECC71;">{best_v['Analista']}</div>
                            <div class="p-detail">{best_v['Aderência %']:.1f}% · TMR: {best_v['TMR Médio (min)']:.1f} min</div>
                        </div>""", unsafe_allow_html=True)
                    with cv2:
                        st.markdown(f"""<div class="perf-card perf-worst">
                            <div class="p-title">⚠️ Menor Aderência</div>
                            <div class="p-name" style="color:#E74C3C;">{worst_v['Analista']}</div>
                            <div class="p-detail">{worst_v['Aderência %']:.1f}% · TMR: {worst_v['TMR Médio (min)']:.1f} min</div>
                        </div>""", unsafe_allow_html=True)

        with col_val2:
            st.markdown("##### 📊 Aderência por Analista")
            if not df_val_anal.empty and "Analista" in df_val_anal.columns:
                chart_val = df_val_anal[["Analista", "Aderencia_Pct"]].set_index("Analista").sort_values("Aderencia_Pct")
                chart_val.columns = ["Aderência %"]
                st.bar_chart(chart_val, horizontal=True, color="#16A085", height=400)
            else:
                st.info("Nenhum dado de validação disponível.")

        # Breakdowns por tipo, rede e grupo
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown("##### 🔧 Por Tipo de Atividade")
            df_val_tipo = toa_validacao_por_tipo(df_toa)
            if not df_val_tipo.empty:
                df_val_tipo_show = df_val_tipo[["Tipo Atividade", "Total", "Aderentes", "Aderencia_Pct", "TMR_Medio_min"]].copy()
                df_val_tipo_show.columns = ["Tipo Atividade", "Total", "Aderentes", "Aderência %", "TMR (min)"]
                st.dataframe(
                    df_val_tipo_show.style
                        .format({"Aderência %": "{:.1f}", "TMR (min)": "{:.1f}"}, na_rep="—")
                        .background_gradient(cmap="RdYlGn", subset=["Aderência %"], vmin=40, vmax=100),
                    use_container_width=True, hide_index=True,
                )
        with col_v2:
            st.markdown("##### 📡 Por Rede")
            df_val_rede = toa_validacao_por_rede(df_toa)
            if not df_val_rede.empty:
                df_val_rede_show = df_val_rede[["Rede", "Total", "Aderentes", "Aderencia_Pct", "TMR_Medio_min"]].copy()
                df_val_rede_show.columns = ["Rede", "Total", "Aderentes", "Aderência %", "TMR (min)"]
                st.dataframe(
                    df_val_rede_show.style
                        .format({"Aderência %": "{:.1f}", "TMR (min)": "{:.1f}"}, na_rep="—")
                        .background_gradient(cmap="RdYlGn", subset=["Aderência %"], vmin=40, vmax=100),
                    use_container_width=True, hide_index=True,
                )

        # Breakdown por IN_GRUPO (dentro da Regional Leste)
        st.markdown(f"##### 🗺️ Por Grupo (IN_GRUPO) — Regional {REGIONAL_FILTRO}")
        _val_grp_col = "IN_GRUPO"
        if _val_grp_col in df_toa.columns:
            _df_val_grp = df_toa[df_toa["INDICADOR_NOME"] == "TEMPO DE VALIDAÇÃO DO FORMULÁRIO"]
            if not _df_val_grp.empty:
                _vg = _df_val_grp.groupby(_val_grp_col).agg(
                    Total=("INDICADOR", "count"),
                    Aderentes=("ADERENTE", "sum"),
                    TMR_Medio_min=("TMR_min", "mean"),
                ).reset_index().rename(columns={_val_grp_col: "Grupo"})
                _vg["Aderência %"] = (_vg["Aderentes"] / _vg["Total"] * 100).round(1)
                _vg["TMR (min)"] = _vg["TMR_Medio_min"].round(1)
                _vg = _vg.sort_values("Total", ascending=False).reset_index(drop=True)
                if not _vg.empty:
                    if _is_admin:
                        _vg_best = _vg.loc[_vg["Aderência %"].idxmax()]
                        _vg_worst = _vg.loc[_vg["Aderência %"].idxmin()]
                        st.caption(
                            f"🟢 Melhor: **{_vg_best['Grupo']}** ({_vg_best['Aderência %']:.1f}%) · "
                            f"🔴 Pior: **{_vg_worst['Grupo']}** ({_vg_worst['Aderência %']:.1f}%)"
                        )
                    st.dataframe(
                        _vg[["Grupo", "Total", "Aderentes", "Aderência %", "TMR (min)"]].style
                            .format({"Aderência %": "{:.1f}", "TMR (min)": "{:.1f}"}, na_rep="—")
                            .background_gradient(cmap="RdYlGn", subset=["Aderência %"], vmin=40, vmax=100)
                            .background_gradient(cmap="Blues", subset=["Total"]),
                        use_container_width=True, hide_index=True,
                    )

        # Validação por setor (apenas admin)
        if _is_admin:
            st.markdown("##### 🏢🏠 Aderência por Setor")
            c_emp_v, c_res_v = st.columns(2)
            for col_sv, setor_sv in [(c_emp_v, "EMPRESARIAL"), (c_res_v, "RESIDENCIAL")]:
                icon_sv = "🏢" if setor_sv == "EMPRESARIAL" else "🏠"
                with col_sv:
                    st.markdown(f"**{icon_sv} {setor_sv}**")
                    if df_val_anal.empty or "Setor" not in df_val_anal.columns:
                        st.caption("Nenhum registro.")
                        continue
                    sub_sv = df_val_anal[df_val_anal["Setor"] == setor_sv].copy()
                    if sub_sv.empty:
                        st.caption("Nenhum registro.")
                        continue
                    media_ader_sv = sub_sv["Aderencia_Pct"].mean()
                    media_tmr_sv  = sub_sv["TMR_Medio_min"].mean()
                    sv1, sv2 = st.columns(2)
                    with sv1:
                        pct_c_sv = COR_SUCESSO if media_ader_sv >= 90 else (COR_ALERTA if media_ader_sv >= 70 else COR_PERIGO)
                        st.markdown(kpi_card("Aderência Média", f"{media_ader_sv:.1f}", pct_c_sv, suffix="%"), unsafe_allow_html=True)
                    with sv2:
                        st.markdown(kpi_card("TMR Médio (min)", f"{media_tmr_sv:.1f}", COR_INFO), unsafe_allow_html=True)
                    _sv_cols = [c for c in ["Analista", "Total", "Aderencia_Pct", "TMR_Medio_min"] if c in sub_sv.columns]
                    sub_sv_show = sub_sv[_sv_cols].copy().reset_index(drop=True)
                    sub_sv_show.columns = [{"Aderencia_Pct": "Aderência %", "TMR_Medio_min": "TMR Médio (min)"}.get(c, c) for c in _sv_cols]
                    sub_sv_show.index += 1; sub_sv_show.index.name = "#"
                    _sv_fmt = {c: "{:.1f}" for c in ["Aderência %", "TMR Médio (min)"] if c in sub_sv_show.columns}
                    _sv_styled = sub_sv_show.style.format(_sv_fmt)
                    if "Aderência %" in sub_sv_show.columns:
                        _sv_styled = _sv_styled.background_gradient(cmap="RdYlGn", subset=["Aderência %"], vmin=40, vmax=100)
                    st.dataframe(_sv_styled, use_container_width=True)

        st.markdown("---")

        # ---- Export combinado ----
        st.markdown("##### 📥 Exportar dados TOA")
        toa_export_cols = [
            "INDICADOR_NOME", "ID_ATIVIDADE", "LOGIN", "Nome", "Setor",
            "IN_REGIONAL", "TIPO_ATIVIDADE", "REDE", "MERCADO", "NATUREZA",
            "INDICADOR", "INDICADOR_STATUS", "ADERENTE",
            "TMR_min", "AGING", "DATA", "DT_CANCELAMENTO",
            "DT_INICIO_FORM", "DT_FIM_FORM", "ANOMES",
        ]
        toa_export_cols = [c for c in toa_export_cols if c in df_toa.columns]
        csv_toa = df_toa[toa_export_cols].to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Baixar Indicadores TOA (CSV)",
            csv_toa,
            f"indicadores_toa_{anomes_str}.csv",
            "text/csv",
        )

        if _is_admin:
            st.markdown("---")
            st.markdown("#### 💡 Insights — Indicadores TOA")
            _toa_insights = []
            try:
                if not df_canc_anal.empty and "Canceladas" in df_canc_anal.columns:
                    _canc_total = int(df_canc_anal["Canceladas"].sum())
                    _n_canc = int((df_canc_anal["Canceladas"] > 0).sum())
                    _toa_insights.append(
                        f"- 🚫 **Total de canceladas:** {_canc_total:,} "
                        f"· **{_n_canc} analistas** com cancelamentos."
                    )
                    _canc_ord = df_canc_anal.sort_values("Canceladas", ascending=False)
                    if not _canc_ord.empty and _canc_ord.iloc[0]["Canceladas"] > 0:
                        _top_canc = _canc_ord.iloc[0]
                        _nome_top = _top_canc.get("Analista") or primeiro_nome(_top_canc.get("Nome", ""))
                        _toa_insights.append(
                            f"- ⚠️ **Mais cancelamentos:** {_nome_top} "
                            f"({int(_top_canc['Canceladas'])})."
                        )
            except NameError:
                pass
            try:
                if not df_canc_tipo.empty and "Canceladas" in df_canc_tipo.columns:
                    _tipo_ord = df_canc_tipo.sort_values("Canceladas", ascending=False)
                    if not _tipo_ord.empty:
                        _top_tipo = _tipo_ord.iloc[0]
                        _col_tipo = next((c for c in ["TIPO_ATIVIDADE", "Tipo", "Tipo de Atividade"]
                                          if c in _tipo_ord.columns), _tipo_ord.columns[0])
                        _toa_insights.append(
                            f"- 📌 **Tipo com mais cancelamentos:** {_top_tipo[_col_tipo]} "
                            f"({int(_top_tipo['Canceladas'])})."
                        )
            except NameError:
                pass
            try:
                _cor_val = "🟢" if _val_pct >= 90 else ("🟡" if _val_pct >= 70 else "🔴")
                _toa_insights.append(
                    f"- {_cor_val} **Aderência média validação formulário:** {_val_pct:.1f}%."
                )
            except NameError:
                pass
            try:
                if not df_val_anal.empty and "Aderencia_Pct" in df_val_anal.columns:
                    _val_ord = df_val_anal.sort_values("Aderencia_Pct", ascending=False)
                    _best_v = _val_ord.iloc[0]
                    _worst_v = _val_ord.iloc[-1]
                    _nome_best_v = _best_v.get("Analista") or primeiro_nome(_best_v.get("Nome", ""))
                    _nome_worst_v = _worst_v.get("Analista") or primeiro_nome(_worst_v.get("Nome", ""))
                    _toa_insights.append(
                        f"- 🏅 **Melhor validação:** {_nome_best_v} "
                        f"({_best_v['Aderencia_Pct']:.1f}%) · "
                        f"⚠️ **Pior:** {_nome_worst_v} "
                        f"({_worst_v['Aderencia_Pct']:.1f}%)."
                    )
            except NameError:
                pass
            for _ins in _toa_insights:
                st.markdown(_ins)

        if _is_admin and _resumo_fora_toa:
            st.markdown("---")
            _toa_ext_cfg = {
                TOA_IND_CANCELADAS: {
                    "ganhos_label": "Não Canceladas",
                    "perdas_label": "Canceladas",
                    "caption":      f"Analistas externos — **Tarefas Canceladas** — Madrugada (22:00–05:59).",
                },
                TOA_IND_VALIDACAO: {
                    "ganhos_label": "Aderentes",
                    "perdas_label": "Não Aderentes",
                    "caption":      f"Analistas externos — **Tempo de Validação do Formulário** — Madrugada (22:00–05:59).",
                },
            }
            for _tind_key, _tind_df in _resumo_fora_toa.items():
                _tcfg = _toa_ext_cfg.get(_tind_key, {})
                render_fora_equipe_madrugada(
                    _tind_df,
                    ganhos_label=_tcfg.get("ganhos_label", "Aderentes"),
                    perdas_label=_tcfg.get("perdas_label", "Não Aderentes"),
                    pct_label="Aderência %",
                    caption=_tcfg.get("caption", f"Analistas externos — **{TOA_IND_LABELS.get(_tind_key, _tind_key)}** — Madrugada."),
                )


# ---- TAB: OCUPAÇÃO DPA ----
if dpa_loaded and _tab_dpa_idx is not None:
    with tabs[_tab_dpa_idx]:
        mes_nome_dpa  = dpa_mes_info.get("mes_nome", "—")
        mes_num_dpa   = dpa_mes_info.get("mes_num")
        # DPA Equipe — média das médias setoriais (Empresarial e Residencial
        # com peso igual). Mesma fórmula usada nos KPIs do header.
        dpa_geral_pct = _dpa_equipe_pct(df_dpa_filtrado)

        st.markdown(
            f"#### 📊 Ocupação DPA — Dados Oficiais · "
            f"Mês mais recente: **{mes_nome_dpa} 2026**"
        )

        if mes_num_dpa:
            st.caption(
                f"ℹ️ O mês mais recente com dados disponíveis na planilha é **{mes_nome_dpa}**. "
                f"Os percentuais refletem a ocupação acumulada de Janeiro a {mes_nome_dpa} de 2026."
            )

        # KPIs gerais
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            dpa_g_str = f"{dpa_geral_pct:.1f}" if dpa_geral_pct else "—"
            st.markdown(kpi_card(f"DPA Equipe ({mes_nome_dpa[:3]})", dpa_g_str, _dpa_color(dpa_geral_pct), suffix="%"),
                        unsafe_allow_html=True)
        with k2:
            st.markdown(kpi_card("Analistas Monitorados", str(len(df_dpa_filtrado)), COR_INFO), unsafe_allow_html=True)
        with k3:
            above = (df_dpa_filtrado["DPA_Pct_Oficial"] >= DPA_THRESHOLD_OK).sum()
            st.markdown(kpi_card(f"Acima de {DPA_THRESHOLD_OK:.0f}% 🟢", str(above), COR_SUCESSO), unsafe_allow_html=True)
        with k4:
            below = (df_dpa_filtrado["DPA_Pct_Oficial"] < DPA_THRESHOLD_ALERTA).sum()
            st.markdown(kpi_card(f"Abaixo de {DPA_THRESHOLD_ALERTA:.0f}% 🔴", str(below), COR_PERIGO), unsafe_allow_html=True)

        st.markdown("")
        st.markdown("---")

        # Comparação com a equipe (apenas não-admin)
        if not _is_admin and not df_dpa_filtrado.empty:
            _u_dpa_pct = df_dpa_filtrado["DPA_Pct_Oficial"].iloc[0] if not df_dpa_filtrado.empty else None
            # Comparação restrita ao setor do analista
            _df_dpa_for_user = _df_dpa_team_full
            if _user_setor and _df_dpa_team_full is not None and "Setor" in _df_dpa_team_full.columns:
                _df_dpa_for_user = _df_dpa_team_full[_df_dpa_team_full["Setor"] == _user_setor]
            _dpa_tm_all = _dpa_equipe_pct(_df_dpa_for_user)
            st.markdown("##### 📊 Seu DPA vs Equipe")
            _dpa_cmp_cols = st.columns(3)
            with _dpa_cmp_cols[0]:
                if _u_dpa_pct is not None:
                    _dc = _dpa_color(_u_dpa_pct)
                    st.markdown(kpi_card("Seu DPA Oficial", f"{_u_dpa_pct:.1f}", _dc, suffix="%"), unsafe_allow_html=True)
            with _dpa_cmp_cols[1]:
                # Comparar contra a média da equipe rastreada (_dpa_tm_all),
                # não contra o agregado da planilha inteira.
                if _dpa_tm_all is not None and pd.notna(_dpa_tm_all):
                    st.markdown(kpi_card(f"DPA Médio Equipe ({mes_nome_dpa[:3]})", f"{_dpa_tm_all:.1f}", _dpa_color(_dpa_tm_all), suffix="%"), unsafe_allow_html=True)
            with _dpa_cmp_cols[2]:
                if _u_dpa_pct is not None:
                    st.markdown(kpi_card("Status", _dpa_semaforo(_u_dpa_pct), _dpa_color(_u_dpa_pct)), unsafe_allow_html=True)
            st.markdown("---")

        # ---- Ranking principal (apenas admin) ----
        if _is_admin:
            st.markdown("##### 🏆 Ranking de Ocupação DPA por Analista")
            rank_of = dpa_ranking(df_dpa_filtrado)
            if not rank_of.empty:
                rank_of = rank_of[~rank_of["Login"].isin(LIDERES_IDS)].reset_index(drop=True)
                rank_of.index += 1; rank_of.index.name = "#"
                rank_of["Status"] = rank_of["DPA %"].apply(_dpa_semaforo)
                rank_of_display = rank_of[["Status", "Analista", "Setor", "DPA %"]]

                col_tbl, col_chart = st.columns([1, 1])
                with col_tbl:
                    st.dataframe(
                        rank_of_display.style
                            .format({"DPA %": "{:.1f}"})
                            .background_gradient(cmap="RdYlGn", subset=["DPA %"], vmin=50, vmax=100),
                        use_container_width=True, height=560,
                    )
                with col_chart:
                    chart_dpa = rank_of[["Analista", "DPA %"]].set_index("Analista").sort_values("DPA %")
                    st.bar_chart(chart_dpa, color="#16A085", height=560)

            st.markdown("---")

            # ---- Breakdown por Setor ----
            st.markdown("##### 🏢🏠 Ocupação DPA por Setor")
            c_emp, c_res = st.columns(2)
            for col_s, setor_s, cmap_s in [
                (c_emp, "EMPRESARIAL", "Oranges"),
                (c_res, "RESIDENCIAL", "Blues"),
            ]:
                with col_s:
                    icon_s = "🏢" if setor_s == "EMPRESARIAL" else "🏠"
                    st.markdown(f"**{icon_s} {setor_s}**")
                    df_sec_s = df_dpa_filtrado[df_dpa_filtrado["Setor"] == setor_s].copy()
                    if df_sec_s.empty:
                        st.caption("Sem dados.")
                        continue
                    media_s = df_sec_s["DPA_Pct_Oficial"].mean()
                    df_sec_s["Nome_Curto"] = df_sec_s["Nome"].apply(primeiro_nome)
                    df_sec_s["Status"] = df_sec_s["DPA_Pct_Oficial"].apply(_dpa_semaforo)
                    df_sec_s_show = df_sec_s[["Status", "Nome_Curto", "DPA_Pct_Oficial"]].copy()
                    df_sec_s_show.columns = ["Status", "Analista", "DPA %"]
                    df_sec_s_show = df_sec_s_show.sort_values("DPA %", ascending=False).reset_index(drop=True)
                    df_sec_s_show.index += 1; df_sec_s_show.index.name = "#"
                    st.caption(f"Média do setor: **{media_s:.1f}%** {_dpa_semaforo(media_s)}")
                    st.dataframe(
                        df_sec_s_show.style
                            .format({"DPA %": "{:.1f}"})
                            .background_gradient(cmap="RdYlGn", subset=["DPA %"], vmin=50, vmax=100),
                        use_container_width=True, height=400,
                    )

            st.markdown("---")

        # ---- Semáforos visuais e comparativo (apenas admin) ----
        if _is_admin:
            st.markdown("##### 🚦 Painel de Semáforo — Todos os Analistas")
            n_cards = 4
            card_cols = st.columns(n_cards)
            sorted_dpa = df_dpa_filtrado.sort_values("DPA_Pct_Oficial", ascending=False).reset_index(drop=True)
            for ci, (_, arow) in enumerate(sorted_dpa.iterrows()):
                pct_v = arow["DPA_Pct_Oficial"]
                nome_c = primeiro_nome(arow["Nome"])
                setor_c = arow["Setor"][:3]
                sem_icon = _dpa_semaforo(pct_v)
                sem_color = (
                    "#27AE60" if pct_v >= DPA_THRESHOLD_OK
                    else "#F39C12" if pct_v >= DPA_THRESHOLD_ALERTA
                    else "#E74C3C"
                )
                with card_cols[ci % n_cards]:
                    st.markdown(f"""<div class="dpa-card" style="border-left-color:{sem_color};">
                        <div class="dpa-nome">{sem_icon} {nome_c} <span style="font-size:0.72rem;opacity:0.55;">{setor_c}</span></div>
                        <div class="dpa-val" style="color:{sem_color};">{pct_v:.1f}%</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("---")

        # ---- Export ----
        st.markdown("---")
        csv_dpa = df_dpa_filtrado[["Login", "Nome", "Setor", "DPA_Pct_Oficial"]].copy()
        csv_dpa.columns = ["Login", "Nome", "Setor", "DPA % Oficial"]
        st.download_button(
            "📥 Baixar Ocupação DPA (CSV)",
            csv_dpa.to_csv(index=False).encode("utf-8"),
            f"ocupacao_dpa_{mes_nome_dpa.lower()}_2026.csv",
            "text/csv",
        )

        if _is_admin and not df_dpa_filtrado.empty:
            st.markdown("---")
            st.markdown("#### 💡 Insights — Ocupação DPA")
            _dpa_insights = []
            _dpa_g = dpa_geral_pct if dpa_geral_pct else df_dpa_filtrado["DPA_Pct_Oficial"].mean()
            _cor_dpa = (
                "🟢" if _dpa_g >= DPA_THRESHOLD_OK
                else ("🟡" if _dpa_g >= DPA_THRESHOLD_ALERTA else "🔴")
            )
            _dpa_insights.append(
                f"- {_cor_dpa} **DPA médio da equipe:** {_dpa_g:.1f}% "
                f"· **{len(df_dpa_filtrado)} analistas** monitorados."
            )
            _dpa_sorted = df_dpa_filtrado.sort_values("DPA_Pct_Oficial", ascending=False)
            if not _dpa_sorted.empty:
                _top = _dpa_sorted.iloc[0]
                _bot = _dpa_sorted.iloc[-1]
                _dpa_insights.append(
                    f"- 🏅 **Maior ocupação:** {primeiro_nome(_top['Nome'])} "
                    f"({_top['DPA_Pct_Oficial']:.1f}%) · "
                    f"⚠️ **Menor:** {primeiro_nome(_bot['Nome'])} "
                    f"({_bot['DPA_Pct_Oficial']:.1f}%)."
                )
            _abaixo_dpa = df_dpa_filtrado[df_dpa_filtrado["DPA_Pct_Oficial"] < DPA_THRESHOLD_ALERTA]
            if not _abaixo_dpa.empty:
                _nomes_ab = ", ".join(primeiro_nome(n) for n in _abaixo_dpa["Nome"].tolist())
                _dpa_insights.append(
                    f"- 🔴 **Abaixo de {DPA_THRESHOLD_ALERTA:.0f}%:** "
                    f"{len(_abaixo_dpa)} analistas — {_nomes_ab}."
                )
            else:
                _dpa_insights.append(
                    f"- ✅ **Nenhum analista abaixo de {DPA_THRESHOLD_ALERTA:.0f}%**."
                )
            _acima_dpa = df_dpa_filtrado[df_dpa_filtrado["DPA_Pct_Oficial"] >= DPA_THRESHOLD_OK]
            _dpa_insights.append(
                f"- 🟢 **Acima de {DPA_THRESHOLD_OK:.0f}%:** {len(_acima_dpa)} analistas."
            )
            for _set in ("EMPRESARIAL", "RESIDENCIAL"):
                _df_set = df_dpa_filtrado[df_dpa_filtrado["Setor"] == _set]
                if not _df_set.empty:
                    _dpa_insights.append(
                        f"- 📊 **Média {_set}:** {_df_set['DPA_Pct_Oficial'].mean():.1f}% "
                        f"({len(_df_set)} analistas)."
                    )
            for _ins in _dpa_insights:
                st.markdown(_ins)

        pass  # DPA não exibe analistas externos


# ---- TAB: FECHAMENTO TOA x SIR (Madrugada) ----
if fech_sir_loaded and _tab_fech_sir_idx is not None:
    with tabs[_tab_fech_sir_idx]:
        anomes_str_fech = str(fech_sir_anomes) if fech_sir_anomes else "?"
        if _is_evandro:
            st.markdown(
                f"#### 🔗 Fechamento TOA x SIR — Todos os Turnos · "
                f"Período: **{anomes_str_fech}** (mês mais recente)"
            )
            st.caption(
                "Dados consolidados das equipes Alexandre, Patrick, Thiago Paroli e "
                "Nelson (Empresarial). Inclui registros dos turnos Manhã, Tarde e Madrugada. "
                "Líderes aparecem em destaque separado abaixo."
            )
        elif _is_pralon:
            st.markdown(
                f"#### 🔗 Fechamento TOA x SIR — Todos os Turnos · "
                f"Período: **{anomes_str_fech}** (mês mais recente)"
            )
            st.caption(
                "Dados consolidados das equipes Luiz, Vinícius e Nelson (Residencial). "
                "Inclui registros dos turnos Manhã, Tarde e Madrugada. "
                "Líderes aparecem em destaque separado abaixo."
            )
        else:
            st.markdown(
                f"#### 🌙 Fechamento TOA x SIR — **Madrugada** · "
                f"Período: **{anomes_str_fech}** (mês mais recente)"
            )
            st.caption(
                "📌 Dados extraídos automaticamente do turno **Madrugada**. "
                "Assertividade = fechamento TOA com causa compatível com o fechamento SIR. "
                "Líderes (Marley, Kelly, Bruno, Leandro) aparecem em destaque separado abaixo."
            )

        # Separar líderes e analistas
        _fech_eq   = df_fech_sir[~df_fech_sir[FECH_SIR_COL_LOGIN].str.upper().isin({l.upper() for l in LIDERES_IDS})].copy()
        _fech_lids = df_fech_sir[df_fech_sir[FECH_SIR_COL_LOGIN].str.upper().isin({l.upper() for l in LIDERES_IDS})].copy()

        # KPIs gerais (equipe toda)
        _n_total_all  = int(df_fech_sir[FECH_SIR_COL_VOLUME].sum())
        _n_asser_all  = int(df_fech_sir['ASSERTIVO'].sum())
        _n_nao_all    = int(df_fech_sir['NAO_ASSERTIVO'].sum()) if 'NAO_ASSERTIVO' in df_fech_sir.columns else _n_total_all - _n_asser_all
        _pct_all      = (_n_asser_all / _n_total_all * 100) if _n_total_all > 0 else 0
        _n_analistas_fech = df_fech_sir['Nome'].nunique()

        kf1, kf2, kf3, kf4, kf5 = st.columns(5)
        with kf1:
            st.markdown(kpi_card("Total Tarefas", f"{_n_total_all:,}", FECH_SIR_COR), unsafe_allow_html=True)
        with kf2:
            st.markdown(kpi_card("Assertivos ✅", f"{_n_asser_all:,}", COR_SUCESSO), unsafe_allow_html=True)
        with kf3:
            st.markdown(kpi_card("Não Assertivos ❌", f"{_n_nao_all:,}", COR_PERIGO), unsafe_allow_html=True)
        with kf4:
            _pct_c = COR_SUCESSO if _pct_all >= 90 else (COR_ALERTA if _pct_all >= 70 else COR_PERIGO)
            st.markdown(kpi_card("Assertividade", f"{_pct_all:.1f}", _pct_c, suffix="%"), unsafe_allow_html=True)
        with kf5:
            st.markdown(kpi_card("Analistas", f"{_n_analistas_fech}", COR_INFO), unsafe_allow_html=True)

        st.markdown("---")

        # Comparação com equipe (apenas não-admin)
        if not _is_admin and _tm_fech_sir_asser_avg is not None:
            st.markdown("##### 📊 Você vs Equipe — Assertividade Madrugada")
            _fech_cmp = st.columns(2)
            with _fech_cmp[0]:
                _pct_c_u = COR_SUCESSO if _pct_all >= 90 else (COR_ALERTA if _pct_all >= 70 else COR_PERIGO)
                st.markdown(kpi_card("Sua Assertividade", f"{_pct_all:.1f}", _pct_c_u, suffix="%"), unsafe_allow_html=True)
            with _fech_cmp[1]:
                _tm_asser_c = _dpa_color(_tm_fech_sir_asser_avg) if _tm_fech_sir_asser_avg else COR_INFO
                st.markdown(kpi_card("Média Assertividade Equipe", f"{_tm_fech_sir_asser_avg:.1f}", COR_INFO, suffix="%"), unsafe_allow_html=True)
            st.markdown("---")

        # ==================================
        # SEÇÃO: ANALISTAS (sem líderes)
        # ==================================
        st.markdown("### 👥 Analistas — Assertividade Madrugada")

        # Sempre calcular _resumo_eq para uso nos insights e na seção não-admin
        _resumo_eq = fech_sir_resumo_analista(_fech_eq if not _fech_eq.empty else df_fech_sir)
        if not _resumo_eq.empty:
            _resumo_eq["Analista"] = _resumo_eq["Nome"].apply(primeiro_nome)

        if _is_admin:
            col_ra, col_ca = st.columns([1, 1])

            with col_ra:
                st.markdown("##### 🏆 Ranking por Analista")
                if not _resumo_eq.empty:
                    _tbl_eq = _resumo_eq[["Analista", "Setor", "Volume", "Assertivos", "Assertividade_Pct"]].copy()
                    _tbl_eq.columns = ["Analista", "Setor", "Tarefas", "Assertivos", "Assertividade %"]
                    _tbl_eq = _tbl_eq.reset_index(drop=True)
                    _tbl_eq.index += 1; _tbl_eq.index.name = "#"
                    st.dataframe(
                        _tbl_eq.style
                            .format({"Assertividade %": "{:.1f}", "Tarefas": "{:.0f}", "Assertivos": "{:.0f}"}, na_rep="—")
                            .background_gradient(cmap="RdYlGn", subset=["Assertividade %"], vmin=50, vmax=100)
                            .background_gradient(cmap="Purples", subset=["Tarefas"]),
                        use_container_width=True,
                    )
                    if len(_tbl_eq) >= 2:
                        _best_a = _tbl_eq.iloc[0]; _worst_a = _tbl_eq.iloc[-1]
                        ca1, ca2 = st.columns(2)
                        with ca1:
                            st.markdown(f"""<div class="perf-card perf-best">
                                <div class="p-title">🏆 Melhor Assertividade</div>
                                <div class="p-name" style="color:#2ECC71;">{_best_a['Analista']}</div>
                                <div class="p-detail">{_best_a['Assertividade %']:.1f}% · {int(_best_a['Tarefas'])} tarefas</div>
                            </div>""", unsafe_allow_html=True)
                        with ca2:
                            st.markdown(f"""<div class="perf-card perf-worst">
                                <div class="p-title">⚠️ Menor Assertividade</div>
                                <div class="p-name" style="color:#E74C3C;">{_worst_a['Analista']}</div>
                                <div class="p-detail">{_worst_a['Assertividade %']:.1f}% · {int(_worst_a['Tarefas'])} tarefas</div>
                            </div>""", unsafe_allow_html=True)
        else:
            # Non-admin: show their own data in a compact table
            if not _resumo_eq.empty:
                _tbl_eq = _resumo_eq[["Analista", "Setor", "Volume", "Assertivos", "Assertividade_Pct"]].copy()
                _tbl_eq.columns = ["Analista", "Setor", "Tarefas", "Assertivos", "Assertividade %"]
                _tbl_eq = _tbl_eq.reset_index(drop=True)
                _tbl_eq.index += 1; _tbl_eq.index.name = "#"
                st.dataframe(
                    _tbl_eq.style
                        .format({"Assertividade %": "{:.1f}", "Tarefas": "{:.0f}", "Assertivos": "{:.0f}"}, na_rep="—")
                        .background_gradient(cmap="RdYlGn", subset=["Assertividade %"], vmin=50, vmax=100),
                    use_container_width=True, hide_index=True,
                )
        # col_ca (gráfico) — apenas admin
        if _is_admin and not _resumo_eq.empty:
            with col_ca:
                st.markdown("##### 📊 Assertividade por Analista")
                _chart_eq = _resumo_eq[["Analista", "Assertividade_Pct"]].set_index("Analista").sort_values("Assertividade_Pct")
                _chart_eq.columns = ["Assertividade %"]
                st.bar_chart(_chart_eq, horizontal=True, color=FECH_SIR_COR, height=400)

        st.markdown("---")

        # ==================================
        # LÍDERES
        # ==================================
        if not _fech_lids.empty:
            st.markdown("### 👑 Líderes — Assertividade Madrugada")
            _resumo_lid_fech = fech_sir_resumo_analista(_fech_lids)
            if not _resumo_lid_fech.empty:
                _resumo_lid_fech["Analista"] = _resumo_lid_fech["Nome"].apply(primeiro_nome)
                _tbl_lid = _resumo_lid_fech[["Analista", "Setor", "Volume", "Assertivos", "Assertividade_Pct"]].copy()
                _tbl_lid.columns = ["Analista", "Setor", "Tarefas", "Assertivos", "Assertividade %"]
                _tbl_lid = _tbl_lid.reset_index(drop=True)
                _tbl_lid.index += 1; _tbl_lid.index.name = "#"
                _cl1, _cl2 = st.columns([1, 1])
                with _cl1:
                    st.dataframe(
                        _tbl_lid.style
                            .format({"Assertividade %": "{:.1f}", "Tarefas": "{:.0f}", "Assertivos": "{:.0f}"}, na_rep="—")
                            .background_gradient(cmap="RdYlGn", subset=["Assertividade %"], vmin=50, vmax=100),
                        use_container_width=True,
                    )
                with _cl2:
                    _chart_lid = _tbl_lid[["Analista", "Assertividade %"]].set_index("Analista").sort_values("Assertividade %")
                    st.bar_chart(_chart_lid, horizontal=True, color="#F39C12", height=250)
            st.markdown("---")

        # ==================================
        # BREAKDOWNS
        # ==================================
        bc1, bc2 = st.columns(2)
        with bc1:
            st.markdown("##### ❌ Top Causas Não Assertivas — TOA")
            _causa_toa = fech_sir_por_causa_toa(df_fech_sir)
            if not _causa_toa.empty:
                st.dataframe(
                    _causa_toa.style.background_gradient(cmap="Reds", subset=["Não Assertivo"]),
                    use_container_width=True, hide_index=True,
                )

        with bc2:
            st.markdown("##### ❌ Top Causas Não Assertivas — SIR")
            _causa_sir = fech_sir_por_causa_sir(df_fech_sir)
            if not _causa_sir.empty:
                st.dataframe(
                    _causa_sir.style.background_gradient(cmap="Reds", subset=["Não Assertivo"]),
                    use_container_width=True, hide_index=True,
                )

        bc3, bc4 = st.columns(2)
        with bc3:
            st.markdown("##### 🗺️ Por Grupo (IN_GRUPO) — Regional Leste")
            _grp_fech = fech_sir_por_grupo(df_fech_sir)
            if not _grp_fech.empty:
                if _is_admin:
                    _bg_f = _grp_fech.loc[_grp_fech["Assertividade_Pct"].idxmax()]
                    _bw_f = _grp_fech.loc[_grp_fech["Assertividade_Pct"].idxmin()]
                    st.caption(
                        f"🟢 Melhor: **{_bg_f['Grupo']}** ({_bg_f['Assertividade_Pct']:.1f}%) · "
                        f"🔴 Pior: **{_bw_f['Grupo']}** ({_bw_f['Assertividade_Pct']:.1f}%)"
                    )
                st.dataframe(
                    _grp_fech.style
                        .format({"Assertividade_Pct": "{:.1f}"}, na_rep="—")
                        .background_gradient(cmap="RdYlGn", subset=["Assertividade_Pct"], vmin=50, vmax=100)
                        .background_gradient(cmap="Purples", subset=["Volume"]),
                    use_container_width=True, hide_index=True,
                )
        with bc4:
            st.markdown("##### 📋 Por Tipo de Demanda")
            _dem_fech = fech_sir_por_demanda(df_fech_sir)
            if not _dem_fech.empty:
                st.dataframe(
                    _dem_fech.style
                        .format({"Assertividade_Pct": "{:.1f}"}, na_rep="—")
                        .background_gradient(cmap="RdYlGn", subset=["Assertividade_Pct"], vmin=50, vmax=100),
                    use_container_width=True, hide_index=True,
                )


        # Insights (apenas admin — para não-admin os insights da equipe expõem dados de colegas)
        if _is_admin:
            st.markdown("---")
            st.markdown("### 💡 Insights — Fechamento TOA x SIR Madrugada")
            _fech_insights = []
            if not _resumo_eq.empty:
                _avg_asser  = _resumo_eq["Assertividade_Pct"].mean()
                _best_fech  = _resumo_eq.iloc[0]
                _worst_fech = _resumo_eq.iloc[-1]
                _fech_insights.append(f"📊 Assertividade média da equipe na madrugada: **{_avg_asser:.1f}%**.")
                _fech_insights.append(f"🏆 Melhor: **{_best_fech['Analista']}** com **{_best_fech['Assertividade_Pct']:.1f}%** ({int(_best_fech['Volume'])} tarefas).")
                _fech_insights.append(f"⚠️ Atenção: **{_worst_fech['Analista']}** com **{_worst_fech['Assertividade_Pct']:.1f}%** ({int(_worst_fech['Volume'])} tarefas).")
                _low_asser = _resumo_eq[_resumo_eq["Assertividade_Pct"] < 80]
                if len(_low_asser) > 0:
                    _fech_insights.append(f"🔴 {len(_low_asser)} analista(s) com assertividade abaixo de 80%: {', '.join(_low_asser['Analista'].tolist())}.")
            _causa_toa_i = fech_sir_por_causa_toa(df_fech_sir)
            if not _causa_toa_i.empty:
                _top_c = _causa_toa_i.iloc[0]
                _fech_insights.append(f"🔧 Causa TOA mais frequente nos não assertivos: **{_top_c['Causa TOA']}** ({int(_top_c['Não Assertivo'])} ocorrências).")
            if _fech_insights:
                for ins in _fech_insights:
                    st.markdown(ins)

        # Export
        st.markdown("---")
        _fech_export_cols = [c for c in [
            FECH_SIR_COL_LOGIN, 'Nome', 'Setor', FECH_SIR_COL_ANOMES,
            FECH_SIR_COL_VOLUME, 'ASSERTIVO', FECH_SIR_COL_CAUSA_TOA,
            FECH_SIR_COL_CAUSA_SIR, FECH_SIR_COL_REGIONAL, FECH_SIR_COL_DEMANDA,
            FECH_SIR_COL_DIA,
        ] if c in df_fech_sir.columns]
        csv_fech = df_fech_sir[_fech_export_cols].to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Baixar Fechamento TOA x SIR Madrugada (CSV)",
            csv_fech,
            f"fech_toa_sir_madrugada_{anomes_str_fech}.csv",
            "text/csv",
        )

        if _is_admin and not _is_evandro:
            st.markdown("---")
            st.markdown("### 👥 Analistas Externos — Madrugada (Fora da Equipe)")
            render_fora_equipe_madrugada(
                _resumo_fora_equipe,
                expanded=True,
                ganhos_label="Assertivos",
                perdas_label="Não Assertivos",
                pct_label="Assertividade %",
                caption="Analistas que aparecem no turno **Madrugada (22:00–05:59)** no arquivo Fechamento TOA x SIR mas **não fazem parte da equipe monitorada**.",
            )

        if _is_coord and not _resumo_fora_equipe_coord.empty:
            st.markdown("---")
            st.markdown("### 👥 Analistas Externos — Horário Diurno (06:00–21:59)")
            render_fora_equipe_madrugada(
                _resumo_fora_equipe_coord,
                expanded=True,
                ganhos_label="Assertivos",
                perdas_label="Não Assertivos",
                pct_label="Assertividade %",
                caption="Analistas externos que também atuam na **Madrugada (22:00–05:59)**, exibindo aqui seus casos no horário **diurno (06:00–21:59)**.",
            )


# ---- TAB: CHAT TOA ----
def _fmt_mmss(sec) -> str:
    """Converte segundos para string 'MM:SS'."""
    if sec is None or (isinstance(sec, float) and pd.isna(sec)):
        return "—"
    sec = int(sec)
    return f"{sec // 60:02d}:{sec % 60:02d}"

if chat_toa_loaded and _tab_chat_toa_idx is not None:
    with tabs[_tab_chat_toa_idx]:
        _ct_anomes_str = str(chat_toa_anomes) if chat_toa_anomes else "?"
        st.markdown(
            f"#### 💬 Chat TOA — TMA (≤10 min) · Período: **{_ct_anomes_str}**"
        )
        st.caption(
            "**TMA** (Tempo Médio de Atendimento): duração total do atendimento. Meta: ≤ 10 min."
        )

        # Filtro de setor do sidebar
        _df_ct = df_chat_toa.copy()
        if setor_selecionado != "Todos" and "Setor" in _df_ct.columns:
            _df_ct = _df_ct[_df_ct["Setor"].str.upper() == setor_selecionado].copy()

        _ct_kpis = chat_toa_kpis_gerais(_df_ct)

        # ━━━ KPIs GERAIS ━━━
        _kct1, _kct2, _kct3, _kct4 = st.columns(4)
        with _kct1:
            st.markdown(kpi_card("Vol. Chat TMA", f"{_ct_kpis.get('vol_tma', 0):,}", CHAT_TOA_COR), unsafe_allow_html=True)
        with _kct2:
            st.markdown(kpi_card("TMA Aderentes", f"{_ct_kpis.get('tma_aderentes', 0):,}", COR_SUCESSO), unsafe_allow_html=True)
        with _kct3:
            _tma_pct = _ct_kpis.get("tma_pct", 0)
            _c_tma = COR_SUCESSO if _tma_pct >= 90 else (COR_ALERTA if _tma_pct >= 70 else COR_PERIGO)
            st.markdown(kpi_card("TMA %", f"{_tma_pct:.1f}", _c_tma, suffix="%"), unsafe_allow_html=True)
        with _kct4:
            _tma_med = _ct_kpis.get("tma_medio_min")
            _tma_med_str = f"{_tma_med:.1f}" if _tma_med is not None else "—"
            st.markdown(kpi_card("TMA Médio (min)", _tma_med_str, COR_INFO), unsafe_allow_html=True)

        st.markdown("---")

        # ━━━ SEÇÃO 1: TMA ━━━
        st.markdown("### ⏱️ TMA — Tempo Médio de Atendimento")
        st.caption("Meta: ≤ 10 minutos. Volume: chats com vida ≤ 1h, sem Sistema, sem MENSAGEM PRIVADA.")

        _ct_anl = chat_toa_por_analista(_df_ct)
        if not _ct_anl.empty:
            _col_tma_l, _col_tma_r = st.columns([1, 1])
            with _col_tma_l:
                st.markdown("##### 🏆 Ranking por Analista — TMA")
                _tbl_tma = _ct_anl[["Nome", "Setor", "Vol_TMA", "TMA_Aderentes", "TMA_Pct", "TMA_Medio_Min"]].copy()
                _tbl_tma.columns = ["Analista", "Setor", "Vol. TMA", "Aderentes", "TMA %", "TMA Médio (min)"]
                _tbl_tma.index = range(1, len(_tbl_tma) + 1); _tbl_tma.index.name = "#"
                st.dataframe(
                    _tbl_tma.style
                        .format({"TMA %": "{:.1f}", "TMA Médio (min)": "{:.2f}"}, na_rep="—")
                        .background_gradient(cmap="RdYlGn", subset=["TMA %"], vmin=50, vmax=100)
                        .background_gradient(cmap="Blues", subset=["Vol. TMA"]),
                    use_container_width=True,
                )
                # Destaques
                if _is_admin:
                    _tma_best = _ct_anl[_ct_anl["Vol_TMA"] > 0].sort_values("TMA_Pct", ascending=False)
                    _tma_worst = _ct_anl[_ct_anl["Vol_TMA"] > 0].sort_values("TMA_Pct")
                    if not _tma_best.empty:
                        _b = _tma_best.iloc[0]
                        st.markdown(
                            f'<div class="perf-best">🏅 Melhor TMA: <b>{primeiro_nome(_b["Nome"])}</b> — {_b["TMA_Pct"]:.1f}%</div>',
                            unsafe_allow_html=True,
                        )
                    if not _tma_worst.empty:
                        _w = _tma_worst.iloc[0]
                        st.markdown(
                            f'<div class="perf-worst">⚠️ Pior TMA: <b>{primeiro_nome(_w["Nome"])}</b> — {_w["TMA_Pct"]:.1f}%</div>',
                            unsafe_allow_html=True,
                        )
            with _col_tma_r:
                st.markdown("##### 📊 TMA % por Analista")
                _chart_tma = _ct_anl[_ct_anl["Vol_TMA"] > 0][["Nome", "TMA_Pct"]].copy()
                _chart_tma["Nome"] = _chart_tma["Nome"].apply(primeiro_nome)
                _chart_tma = _chart_tma.set_index("Nome").sort_values("TMA_Pct")
                st.bar_chart(_chart_tma, height=350, color=CHAT_TOA_COR)

        # Por Tipo de Fila
        _ct_tipo = chat_toa_por_tipo_fila(_df_ct)
        if not _ct_tipo.empty:
            st.markdown("##### 📂 Por Tipo de Fila")
            st.dataframe(
                _ct_tipo.style
                    .format({"TMA_Pct": "{:.1f}"}, na_rep="—")
                    .background_gradient(cmap="RdYlGn", subset=["TMA_Pct"], vmin=50, vmax=100),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("---")

        # ━━━ EXPORT ━━━
        _csv_ct = _df_ct.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CSV — Chat TOA",
            data=_csv_ct,
            file_name=f"chat_toa_{_ct_anomes_str}.csv",
            mime="text/csv",
        )

        if _is_admin:
            st.markdown("---")
            st.markdown("#### 💡 Insights — Chat TOA")
            _chat_insights = []
            _tma_pct_g = _ct_kpis.get("tma_pct", 0)
            _tma_med_g = _ct_kpis.get("tma_medio_min")
            _cor_tma = "🟢" if _tma_pct_g >= 90 else ("🟡" if _tma_pct_g >= 70 else "🔴")
            _tma_med_str = f"{_tma_med_g:.1f} min" if _tma_med_g is not None else "—"
            _chat_insights.append(
                f"- {_cor_tma} **TMA médio da equipe:** {_tma_pct_g:.1f}% aderência · "
                f"tempo médio **{_tma_med_str}** (meta ≤ 10 min)."
            )
            if not _ct_anl.empty and "Vol_TMA" in _ct_anl.columns:
                _ct_valid = _ct_anl[_ct_anl["Vol_TMA"] > 0].copy()
                if not _ct_valid.empty:
                    _ct_ord = _ct_valid.sort_values("TMA_Pct", ascending=False)
                    _best_ct = _ct_ord.iloc[0]
                    _worst_ct = _ct_ord.iloc[-1]
                    _chat_insights.append(
                        f"- 🏅 **Melhor TMA:** {primeiro_nome(_best_ct['Nome'])} "
                        f"({_best_ct['TMA_Pct']:.1f}%) · "
                        f"⚠️ **Pior:** {primeiro_nome(_worst_ct['Nome'])} "
                        f"({_worst_ct['TMA_Pct']:.1f}%)."
                    )
                    _abaixo_ct = _ct_valid[_ct_valid["TMA_Pct"] < 70]
                    if not _abaixo_ct.empty:
                        _nomes_ab_ct = ", ".join(primeiro_nome(n) for n in _abaixo_ct["Nome"].tolist())
                        _chat_insights.append(
                            f"- 🔴 **Abaixo de 70% TMA:** {len(_abaixo_ct)} analistas — {_nomes_ab_ct}."
                        )
                    if "TMA_Medio_Min" in _ct_valid.columns:
                        _acima_meta = _ct_valid[_ct_valid["TMA_Medio_Min"] > 10]
                        _chat_insights.append(
                            f"- ⏱️ **Acima da meta (>10 min):** {len(_acima_meta)} analistas."
                        )
            if not _ct_tipo.empty and "TMA_Pct" in _ct_tipo.columns:
                _tipo_ord = _ct_tipo.sort_values("TMA_Pct")
                if not _tipo_ord.empty:
                    _col_fila = next((c for c in ["Tipo_Fila", "Tipo", "Fila", "TIPO_FILA"]
                                      if c in _tipo_ord.columns), _tipo_ord.columns[0])
                    _pior_tipo = _tipo_ord.iloc[0]
                    _chat_insights.append(
                        f"- 📂 **Pior tipo de fila:** {_pior_tipo[_col_fila]} "
                        f"({_pior_tipo['TMA_Pct']:.1f}%)."
                    )
            for _ins in _chat_insights:
                st.markdown(_ins)


# ---- TAB: ANALISTA CERTIFICADO (apenas admins) ----
if _is_admin and _tab_cert_idx is not None:
    with tabs[_tab_cert_idx]:
        st.markdown("#### ✅ Analista Certificado")
        st.caption(
            "Status de certificação de cada analista da sua equipe, segundo as "
            "regras Residencial (ETIT Fibra HFC · DPA · Média Assertividade) ou "
            "Empresarial (ETIT por Evento · DPA)."
        )

        # ── Determinar escopo de analistas deste admin ───────────────────────
        _luiz_ids       = {m.upper() for m in COORD_ANALYSTS_MAP.get("LUIZ",     set())}
        _vinicius_ids   = {m.upper() for m in COORD_ANALYSTS_MAP.get("VINICIUS", set())}
        _alexandre_ids  = {m.upper() for m in COORD_ANALYSTS_MAP.get("N0150817", set())}
        _patrick_ids    = {m.upper() for m in COORD_ANALYSTS_MAP.get("N5768308", set())}
        _paroli_ids     = {m.upper() for m in COORD_ANALYSTS_MAP.get("TPAROLI",  set())}
        _res_fixed_ids  = {m.upper() for m in BASE_EQUIPE[BASE_EQUIPE["Setor"] == "RESIDENCIAL"]["Matricula"].tolist()}
        _emp_fixed_ids  = {m.upper() for m in BASE_EQUIPE[BASE_EQUIPE["Setor"] == "EMPRESARIAL"]["Matricula"].tolist()}

        _cert_scope_ids: set = set()
        if _is_pralon:
            _cert_scope_ids = {m.upper() for m in PRALON_ANALYSTS}
        elif _is_evandro:
            _cert_scope_ids = (
                _evandro_scope_ids if _evandro_scope_ids is not None
                else {m.upper() for m in EVANDRO_ANALYSTS}
            )
        elif _auth_user in COORD_ANALYSTS_MAP:
            _cert_scope_ids = {m.upper() for m in COORD_ANALYSTS_MAP[_auth_user]}
        else:
            # Super admin Nelson — equipe fixa (Residencial + Empresarial)
            _cert_scope_ids = {m.upper() for m in EQUIPE_IDS}

        _cert_scope_ids = _cert_scope_ids - {m.upper() for m in LIDERES_IDS}

        # ── Exportar todos os indicadores da equipe (XLSX) ───────────────────
        if _cert_scope_ids:
            _scope_upper = {m.upper() for m in _cert_scope_ids}

            def _filter_by_login(_df: pd.DataFrame, _col: str) -> pd.DataFrame:
                if _df is None or _df.empty or _col not in _df.columns:
                    return _df if _df is not None else pd.DataFrame()
                return _df[_df[_col].astype(str).str.upper().isin(_scope_upper)].copy()

            _export_sheets = {
                "Produtividade":        _filter_by_login(df_filtrado,  COL_LOGIN),
                "ETIT por Evento":      _filter_by_login(df_etit,      ETIT_COL_LOGIN),
                "Residencial":          _filter_by_login(df_res_ind,   RES_LOGIN),
                "TOA":                  _filter_by_login(df_toa,       "LOGIN"),
                "DPA Ocupacao":         _filter_by_login(df_dpa,       "Login"),
                "Fechamento TOA x SIR": _filter_by_login(df_fech_sir,  FECH_SIR_COL_LOGIN),
                "Chat TOA":             _filter_by_login(df_chat_toa,  CHAT_TOA_COL_LOGIN),
            }

            _has_any = any((_df is not None and not _df.empty) for _df in _export_sheets.values())
            if _has_any:
                _xlsx_buf = io.BytesIO()
                with pd.ExcelWriter(_xlsx_buf, engine="openpyxl") as _writer:
                    for _sheet_name, _df_sheet in _export_sheets.items():
                        if _df_sheet is None or _df_sheet.empty:
                            continue
                        _df_sheet.to_excel(_writer, sheet_name=_sheet_name[:31], index=False)
                _xlsx_buf.seek(0)
                _today = datetime.date.today().strftime("%Y%m%d")
                st.download_button(
                    "📦 Exportar todos os indicadores da equipe (XLSX)",
                    _xlsx_buf.getvalue(),
                    f"indicadores_equipe_{_auth_user}_{_today}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        if not _cert_scope_ids:
            st.info("Nenhum analista no escopo desta visão.")
        else:
            # ── Pré-agregações por analista ──────────────────────────────────
            _resumo_cert_adm = resumo_geral(df_filtrado) if not df_filtrado.empty else pd.DataFrame()
            _dpa_calc_map = {}
            if not _resumo_cert_adm.empty and COL_LOGIN in _resumo_cert_adm.columns:
                for _, _rr in _resumo_cert_adm.iterrows():
                    _lg = str(_rr.get(COL_LOGIN, "")).upper()
                    _vv = _rr.get("DPA_Media", None)
                    if _lg and _vv is not None and pd.notna(_vv):
                        _dpa_calc_map[_lg] = float(_vv)

            _dpa_of_map = {}
            if dpa_loaded and not df_dpa.empty and "Login" in df_dpa.columns and "DPA_Pct_Oficial" in df_dpa.columns:
                for _, _rr in df_dpa.iterrows():
                    _lg = str(_rr.get("Login", "")).upper()
                    _vv = _rr.get("DPA_Pct_Oficial", None)
                    if _lg and _vv is not None and pd.notna(_vv):
                        _dpa_of_map[_lg] = float(_vv)

            # ETIT por Evento — agregado por login
            _etit_map: dict = {}
            if etit_loaded and not df_etit.empty and ETIT_COL_LOGIN in df_etit.columns:
                _g = df_etit.groupby(df_etit[ETIT_COL_LOGIN].astype(str).str.upper()).agg(
                    _vol=(ETIT_COL_VOLUME, "sum"),
                    _ad=(ETIT_COL_INDICADOR_VAL, "sum"),
                )
                for _lg, _rr in _g.iterrows():
                    _v = float(_rr["_vol"]) if pd.notna(_rr["_vol"]) else 0.0
                    _a = float(_rr["_ad"])  if pd.notna(_rr["_ad"])  else 0.0
                    if _v > 0:
                        _etit_map[_lg] = (_a / _v) * 100.0

            # Residencial — por (login, indicador)
            _res_map: dict = {}
            if res_ind_loaded and not df_res_ind.empty and RES_LOGIN in df_res_ind.columns:
                _ader_col = "ADERENTE" if "ADERENTE" in df_res_ind.columns else RES_COL_IND_VAL
                if _ader_col in df_res_ind.columns and RES_COL_VOLUME in df_res_ind.columns:
                    _gres = df_res_ind.groupby(
                        [df_res_ind[RES_LOGIN].astype(str).str.upper(), RES_COL_INDICADOR_NOME]
                    ).agg(_vol=(RES_COL_VOLUME, "sum"), _ad=(_ader_col, "sum"))
                    for (_lg, _ind), _rr in _gres.iterrows():
                        _v = float(_rr["_vol"]) if pd.notna(_rr["_vol"]) else 0.0
                        _a = float(_rr["_ad"])  if pd.notna(_rr["_ad"])  else 0.0
                        if _v > 0:
                            _res_map[(_lg, _ind)] = (_a / _v) * 100.0

            # ── Avaliação por analista ───────────────────────────────────────
            _rows: list = []
            for _mat in sorted(_cert_scope_ids):
                _is_res_analista = (
                    _mat in _res_fixed_ids
                    or _mat in _luiz_ids
                    or _mat in _vinicius_ids
                )
                _is_emp_analista = (
                    _mat in _emp_fixed_ids
                    or _mat in _alexandre_ids
                    or _mat in _patrick_ids
                    or _mat in _paroli_ids
                )
                if _is_res_analista:
                    _segmento = "Residencial"
                elif _is_emp_analista:
                    _segmento = "Empresarial"
                else:
                    _segmento = "—"

                _equipe = (
                    "Nelson (Res.)"   if _mat in _res_fixed_ids else
                    "Luiz"            if _mat in _luiz_ids else
                    "Vinícius"        if _mat in _vinicius_ids else
                    "Nelson (Emp.)"   if _mat in _emp_fixed_ids else
                    "Alexandre"       if _mat in _alexandre_ids else
                    "Patrick"         if _mat in _patrick_ids else
                    "Thiago Paroli"   if _mat in _paroli_ids else
                    "—"
                )

                _dpa_pct = _dpa_of_map.get(_mat, _dpa_calc_map.get(_mat))

                if _segmento == "Residencial":
                    _etit_pct = _res_map.get((_mat, RES_IND_ETIT_FIBRA_HFC))
                    _ahfc     = _res_map.get((_mat, RES_IND_ASSERT_FIBRA_HFC))
                    _agpon    = _res_map.get((_mat, RES_IND_ASSERT_GPON))
                    if _ahfc is not None and _agpon is not None:
                        _media_assert = (_ahfc + _agpon) / 2.0
                    elif _ahfc is not None:
                        _media_assert = _ahfc
                    elif _agpon is not None:
                        _media_assert = _agpon
                    else:
                        _media_assert = None

                    # Dados ausentes são tratados como dentro da meta
                    _etit_ok   = (_etit_pct     is None) or (_etit_pct     >= 90.0)
                    _dpa_ok    = (_dpa_pct      is None) or (_dpa_pct      >= 90.0)
                    _dpa_alert = (_dpa_pct is not None)  and (85.0 <= _dpa_pct < 90.0)
                    _assert_ok = (_media_assert is None) or (_media_assert >= 85.0)

                    _assumidos = []
                    if _etit_pct     is None: _assumidos.append("ETIT Fibra HFC")
                    if _dpa_pct      is None: _assumidos.append("DPA")
                    if _media_assert is None: _assumidos.append("Média Assertividade")

                    if _etit_ok and _dpa_ok and _assert_ok:
                        _status = "Certificando"; _semaforo = "🟢"; _observ = ""
                    elif _etit_ok and _dpa_alert and _assert_ok:
                        _status = "Certificando (DPA fora da meta)"; _semaforo = "🟡"
                        _observ = "DPA individual entre 85% e 90%."
                    else:
                        _status = "NÃO Certificando"; _semaforo = "🔴"
                        _mot = []
                        if (_etit_pct     is not None) and (_etit_pct     < 90.0):
                            _mot.append(f"ETIT HFC {_etit_pct:.1f}%")
                        if (_dpa_pct      is not None) and (_dpa_pct      < 85.0):
                            _mot.append(f"DPA {_dpa_pct:.1f}%")
                        if (_media_assert is not None) and (_media_assert < 85.0):
                            _mot.append(f"Média Assert. {_media_assert:.1f}%")
                        _observ = " · ".join(_mot)

                    if _assumidos:
                        _nota_assum = f"sem dados de {', '.join(_assumidos)} (considerados dentro da meta)"
                        _observ = f"{_observ} · {_nota_assum}" if _observ else _nota_assum

                    _rows.append({
                        "Status":        _semaforo,
                        "Analista":      _name_for_login(_mat),
                        "Matrícula":     _mat,
                        "Segmento":      _segmento,
                        "Equipe":        _equipe,
                        "ETIT Fibra HFC %": _etit_pct,
                        "DPA %":         _dpa_pct,
                        "Assert. Fibra HFC %": _ahfc,
                        "Assert. GPON %":      _agpon,
                        "Média Assert. %":     _media_assert,
                        "ETIT por Evento %":   None,
                        "Situação":      _status,
                        "Observação":    _observ,
                    })

                elif _segmento == "Empresarial":
                    _etit_pct = _etit_map.get(_mat)

                    # Dados ausentes são tratados como dentro da meta
                    _etit_ok   = (_etit_pct is None) or (_etit_pct >= 90.0)
                    _dpa_ok    = (_dpa_pct  is None) or (_dpa_pct  >= 90.0)
                    _dpa_alert = (_dpa_pct is not None) and (85.0 <= _dpa_pct < 90.0)

                    _assumidos = []
                    if _etit_pct is None: _assumidos.append("ETIT por Evento")
                    if _dpa_pct  is None: _assumidos.append("DPA")

                    if _etit_ok and _dpa_ok:
                        _status = "Certificando"; _semaforo = "🟢"; _observ = ""
                    elif _etit_ok and _dpa_alert:
                        _status = "Certificando (DPA fora da meta)"; _semaforo = "🟡"
                        _observ = "DPA individual entre 85% e 90%."
                    else:
                        _status = "NÃO Certificando"; _semaforo = "🔴"
                        _mot = []
                        if (_etit_pct is not None) and (_etit_pct < 90.0):
                            _mot.append(f"ETIT Evento {_etit_pct:.1f}%")
                        if (_dpa_pct  is not None) and (_dpa_pct  < 85.0):
                            _mot.append(f"DPA {_dpa_pct:.1f}%")
                        _observ = " · ".join(_mot)

                    if _assumidos:
                        _nota_assum = f"sem dados de {', '.join(_assumidos)} (considerados dentro da meta)"
                        _observ = f"{_observ} · {_nota_assum}" if _observ else _nota_assum

                    _rows.append({
                        "Status":         _semaforo,
                        "Analista":       _name_for_login(_mat),
                        "Matrícula":      _mat,
                        "Segmento":       _segmento,
                        "Equipe":         _equipe,
                        "ETIT Fibra HFC %":    None,
                        "DPA %":          _dpa_pct,
                        "Assert. Fibra HFC %": None,
                        "Assert. GPON %":      None,
                        "Média Assert. %":     None,
                        "ETIT por Evento %":   _etit_pct,
                        "Situação":       _status,
                        "Observação":     _observ,
                    })
                else:
                    _rows.append({
                        "Status":         "⚪",
                        "Analista":       _name_for_login(_mat),
                        "Matrícula":      _mat,
                        "Segmento":       _segmento,
                        "Equipe":         _equipe,
                        "ETIT Fibra HFC %":    None,
                        "DPA %":          _dpa_pct,
                        "Assert. Fibra HFC %": None,
                        "Assert. GPON %":      None,
                        "Média Assert. %":     None,
                        "ETIT por Evento %":   None,
                        "Situação":       "Segmento não identificado",
                        "Observação":     "",
                    })

            df_cert = pd.DataFrame(_rows)

            # ── KPIs de resumo ───────────────────────────────────────────────
            _total     = len(df_cert)
            _n_verde   = int((df_cert["Status"] == "🟢").sum())
            _n_amarelo = int((df_cert["Status"] == "🟡").sum())
            _n_vermelho= int((df_cert["Status"] == "🔴").sum())
            _n_branco  = int((df_cert["Status"] == "⚪").sum())
            _n_cert    = _n_verde + _n_amarelo
            _pct_cert  = (_n_cert / _total * 100.0) if _total > 0 else 0.0
            _cor_pct   = (
                COR_SUCESSO if _pct_cert >= 90.0
                else COR_ALERTA if _pct_cert >= 70.0
                else COR_PERIGO
            )

            _kc = st.columns(5)
            with _kc[0]:
                st.markdown(kpi_card("Total Analistas", f"{_total}", COR_PRIMARIA), unsafe_allow_html=True)
            with _kc[1]:
                st.markdown(kpi_card("🟢 Certificando", f"{_n_verde}", COR_SUCESSO), unsafe_allow_html=True)
            with _kc[2]:
                st.markdown(kpi_card("🟡 DPA fora da meta", f"{_n_amarelo}", COR_ALERTA), unsafe_allow_html=True)
            with _kc[3]:
                st.markdown(kpi_card("🔴 NÃO Certificando", f"{_n_vermelho}", COR_PERIGO), unsafe_allow_html=True)
            with _kc[4]:
                st.markdown(
                    kpi_card("% Certificando (Geral)", f"{_pct_cert:.1f}%", _cor_pct),
                    unsafe_allow_html=True,
                )

            st.markdown("")

            # ── Quebra por segmento (% Certificando Empresarial vs Residencial) ──
            _df_res = df_cert[df_cert["Segmento"] == "Residencial"]
            _df_emp = df_cert[df_cert["Segmento"] == "Empresarial"]
            _has_res = len(_df_res) > 0
            _has_emp = len(_df_emp) > 0
            if _has_res and _has_emp:
                _t_res = len(_df_res)
                _c_res = int(_df_res["Status"].isin(["🟢", "🟡"]).sum())
                _pct_res = (_c_res / _t_res * 100.0) if _t_res > 0 else 0.0
                _cor_res = (
                    COR_SUCESSO if _pct_res >= 90.0
                    else COR_ALERTA if _pct_res >= 70.0
                    else COR_PERIGO
                )

                _t_emp = len(_df_emp)
                _c_emp = int(_df_emp["Status"].isin(["🟢", "🟡"]).sum())
                _pct_emp = (_c_emp / _t_emp * 100.0) if _t_emp > 0 else 0.0
                _cor_emp = (
                    COR_SUCESSO if _pct_emp >= 90.0
                    else COR_ALERTA if _pct_emp >= 70.0
                    else COR_PERIGO
                )

                _kseg = st.columns(2)
                with _kseg[0]:
                    st.markdown(
                        kpi_card(
                            "% Certificando — Residencial",
                            f"{_pct_res:.1f}%  ({_c_res}/{_t_res})",
                            _cor_res,
                        ),
                        unsafe_allow_html=True,
                    )
                with _kseg[1]:
                    st.markdown(
                        kpi_card(
                            "% Certificando — Empresarial",
                            f"{_pct_emp:.1f}%  ({_c_emp}/{_t_emp})",
                            _cor_emp,
                        ),
                        unsafe_allow_html=True,
                    )

                st.markdown("")

            st.caption(
                "Indicadores sem dados são considerados dentro da meta — veja a coluna "
                "Observação para identificar analistas avaliados com base em dados parciais."
            )

            # ── Filtros ──────────────────────────────────────────────────────
            st.markdown("")
            _f1, _f2 = st.columns([1, 1])
            with _f1:
                _situacao_opts = ["Todos"] + sorted([s for s in df_cert["Situação"].dropna().unique().tolist()])
                _sit_sel = st.selectbox("Situação", options=_situacao_opts, index=0)
            with _f2:
                _seg_opts = ["Todos"] + sorted([s for s in df_cert["Segmento"].dropna().unique().tolist() if s != "—"])
                _seg_sel = st.selectbox("Segmento", options=_seg_opts, index=0)

            _df_view = df_cert.copy()
            if _sit_sel != "Todos":
                _df_view = _df_view[_df_view["Situação"] == _sit_sel]
            if _seg_sel != "Todos":
                _df_view = _df_view[_df_view["Segmento"] == _seg_sel]

            _df_view = _df_view.sort_values(
                by=["Situação", "Segmento", "Analista"],
                key=lambda col: col.map({
                    "NÃO Certificando": 0,
                    "Certificando (DPA fora da meta)": 1,
                    "Certificando": 2,
                    "Segmento não identificado": 3,
                }) if col.name == "Situação" else col,
                ascending=True,
            ).reset_index(drop=True)
            _df_view.index += 1
            _df_view.index.name = "#"

            _fmt_cert = {
                "ETIT Fibra HFC %":    "{:.1f}",
                "DPA %":               "{:.1f}",
                "Assert. Fibra HFC %": "{:.1f}",
                "Assert. GPON %":      "{:.1f}",
                "Média Assert. %":     "{:.1f}",
                "ETIT por Evento %":   "{:.1f}",
            }

            st.dataframe(
                _df_view.style.format(_fmt_cert, na_rep="—"),
                use_container_width=True,
                height=min(640, 80 + 36 * max(1, len(_df_view))),
            )

            _csv_cert = _df_view.reset_index().to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Baixar status de certificação (CSV)",
                _csv_cert,
                "analistas_certificacao.csv",
                "text/csv",
            )


# ---- TAB: HIGHLIGHTS (apenas não-admin) ----
if not _is_admin and _u_highlights_idx is not None:
    with tabs[_u_highlights_idx]:
        _u_nome_display = _user_nome or _mat_up or "Analista"
        st.markdown(f"#### ⭐ Highlights — {_u_nome_display}")
        st.caption("Resumo consolidado da sua performance em todos os indicadores carregados.")

        # ── Status de Certificação — Empresarial (Patrick / Alexandre / Thiago Paroli / Nelson) ──
        _cert_emp_alexandre = _mat_up in COORD_ANALYSTS_MAP.get("N0150817", set())
        _cert_emp_patrick   = _mat_up in COORD_ANALYSTS_MAP.get("N5768308", set())
        _cert_emp_paroli    = _mat_up in COORD_ANALYSTS_MAP.get("TPAROLI",  set())
        _cert_emp_nelson    = (_user_setor == "EMPRESARIAL")
        _is_cert_emp_elig   = (
            _cert_emp_alexandre or _cert_emp_patrick
            or _cert_emp_paroli or _cert_emp_nelson
        )

        if _is_cert_emp_elig:
            # ETIT POR EVENTO % (planilha Analítico Empresarial)
            _cert_emp_etit_pct = None
            if etit_loaded and not df_etit_filtrado.empty:
                _ev = float(df_etit_filtrado[ETIT_COL_VOLUME].sum()) if ETIT_COL_VOLUME in df_etit_filtrado.columns else 0.0
                _ad = float(df_etit_filtrado[ETIT_COL_INDICADOR_VAL].sum()) if ETIT_COL_INDICADOR_VAL in df_etit_filtrado.columns else 0.0
                if _ev > 0:
                    _cert_emp_etit_pct = (_ad / _ev) * 100.0

            # DPA % — preferir DPA Oficial; senão, DPA calculado da produtividade
            _cert_emp_dpa_pct = None
            if dpa_loaded and not df_dpa_filtrado.empty and "DPA_Pct_Oficial" in df_dpa_filtrado.columns:
                _dpa_val = df_dpa_filtrado["DPA_Pct_Oficial"].iloc[0]
                if pd.notna(_dpa_val):
                    _cert_emp_dpa_pct = float(_dpa_val)
            if _cert_emp_dpa_pct is None and not df_filtrado.empty:
                _resumo_cert_emp = resumo_geral(df_filtrado)
                if not _resumo_cert_emp.empty:
                    _dpa_calc = _resumo_cert_emp.iloc[0].get("DPA_Media", None)
                    if _dpa_calc is not None and pd.notna(_dpa_calc):
                        _cert_emp_dpa_pct = float(_dpa_calc)

            _coord_emp_nome = (
                "Alexandre" if _cert_emp_alexandre else
                "Patrick"   if _cert_emp_patrick   else
                "Thiago Paroli" if _cert_emp_paroli else
                "Nelson (Empresarial)"
            )

            st.markdown("---")
            st.markdown("##### 🎯 Status de Certificação — ETIT por Evento &amp; DPA Individual")

            # Dados ausentes são tratados como dentro da meta
            _etit_emp_ok    = (_cert_emp_etit_pct is None) or (_cert_emp_etit_pct >= 90.0)
            _dpa_emp_ok     = (_cert_emp_dpa_pct  is None) or (_cert_emp_dpa_pct  >= 90.0)
            _dpa_emp_alerta = (_cert_emp_dpa_pct is not None) and (85.0 <= _cert_emp_dpa_pct < 90.0)

            _assumidos_emp = []
            if _cert_emp_etit_pct is None: _assumidos_emp.append("ETIT por Evento")
            if _cert_emp_dpa_pct  is None: _assumidos_emp.append("DPA")

            if _etit_emp_ok and _dpa_emp_ok:
                _cert_emp_titulo = "✅ Você está Certificando"
                _cert_emp_msg    = "ETIT por Evento e DPA individual dentro da meta."
                _cert_emp_cor    = COR_SUCESSO
            elif _etit_emp_ok and _dpa_emp_alerta:
                _cert_emp_titulo = "⚠️ Você está Certificando"
                _cert_emp_msg    = "Porém o DPA individual não está dentro da meta (85% ≤ DPA &lt; 90%)."
                _cert_emp_cor    = COR_ALERTA
            else:
                _cert_emp_titulo = "❌ Você NÃO está Certificando"
                _motivos_emp = []
                if (_cert_emp_etit_pct is not None) and (_cert_emp_etit_pct < 90.0):
                    _motivos_emp.append(f"ETIT por Evento abaixo de 90% ({_cert_emp_etit_pct:.1f}%)")
                if (_cert_emp_dpa_pct  is not None) and (_cert_emp_dpa_pct  < 85.0):
                    _motivos_emp.append(f"DPA individual abaixo de 85% ({_cert_emp_dpa_pct:.1f}%)")
                _cert_emp_msg = "Porém o DPA individual não está dentro da meta — " + " · ".join(_motivos_emp) + "."
                _cert_emp_cor = COR_PERIGO

            if _assumidos_emp:
                _cert_emp_msg = (
                    f"{_cert_emp_msg} (Sem dados de {', '.join(_assumidos_emp)} — "
                    f"considerados dentro da meta.)"
                )

            st.markdown(
                f'<div class="kpi-card" style="border-left-color:{_cert_emp_cor};">'
                f'<div class="kpi-label">Equipe {_coord_emp_nome}</div>'
                f'<div class="kpi-value" style="color:{_cert_emp_cor}; font-size:1.25rem;">{_cert_emp_titulo}</div>'
                f'<div class="kpi-delta" style="color:{_cert_emp_cor};">{_cert_emp_msg}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            _cert_emp_cols = st.columns(2)
            with _cert_emp_cols[0]:
                _etit_emp_val = f"{_cert_emp_etit_pct:.1f}" if _cert_emp_etit_pct is not None else "—"
                _c_etit_emp_cor = (
                    COR_INFO if _cert_emp_etit_pct is None
                    else COR_SUCESSO if _cert_emp_etit_pct >= 90.0
                    else COR_PERIGO
                )
                st.markdown(
                    kpi_card("ETIT por Evento %", _etit_emp_val, _c_etit_emp_cor),
                    unsafe_allow_html=True,
                )
            with _cert_emp_cols[1]:
                _dpa_emp_val = f"{_cert_emp_dpa_pct:.1f}" if _cert_emp_dpa_pct is not None else "—"
                _c_dpa_emp_cor = COR_INFO if _cert_emp_dpa_pct is None else _dpa_color(_cert_emp_dpa_pct)
                st.markdown(
                    kpi_card("DPA Individual %", _dpa_emp_val, _c_dpa_emp_cor),
                    unsafe_allow_html=True,
                )

            st.markdown("")

        # ── Status de Certificação — Residencial (Nelson / Luiz / Vinícius) ──
        _is_nelson_res     = (_user_setor == "RESIDENCIAL")
        _is_luiz_team      = _mat_up in {m.upper() for m in COORD_ANALYSTS_MAP.get("LUIZ", set())}
        _is_vinicius_team  = _mat_up in {m.upper() for m in COORD_ANALYSTS_MAP.get("VINICIUS", set())}
        _is_cert_res_elig  = _is_nelson_res or _is_luiz_team or _is_vinicius_team

        if _is_cert_res_elig:
            def _res_pct(df_src, ind_nome):
                if df_src is None or df_src.empty or RES_COL_INDICADOR_NOME not in df_src.columns:
                    return None
                _sub = df_src[df_src[RES_COL_INDICADOR_NOME] == ind_nome]
                if _sub.empty or RES_COL_VOLUME not in _sub.columns:
                    return None
                _vol = float(_sub[RES_COL_VOLUME].sum())
                if _vol <= 0:
                    return None
                _ad_col = "ADERENTE" if "ADERENTE" in _sub.columns else RES_COL_IND_VAL
                if _ad_col not in _sub.columns:
                    return None
                _ad = float(_sub[_ad_col].sum())
                return (_ad / _vol) * 100.0

            _cert_res_etit_hfc_pct    = _res_pct(df_res_filtrado, RES_IND_ETIT_FIBRA_HFC)    if res_ind_loaded else None
            _cert_res_assert_hfc_pct  = _res_pct(df_res_filtrado, RES_IND_ASSERT_FIBRA_HFC)  if res_ind_loaded else None
            _cert_res_assert_gpon_pct = _res_pct(df_res_filtrado, RES_IND_ASSERT_GPON)       if res_ind_loaded else None

            if _cert_res_assert_hfc_pct is not None and _cert_res_assert_gpon_pct is not None:
                _cert_res_media_assert = (_cert_res_assert_hfc_pct + _cert_res_assert_gpon_pct) / 2.0
            elif _cert_res_assert_hfc_pct is not None:
                _cert_res_media_assert = _cert_res_assert_hfc_pct
            elif _cert_res_assert_gpon_pct is not None:
                _cert_res_media_assert = _cert_res_assert_gpon_pct
            else:
                _cert_res_media_assert = None

            _cert_res_dpa_pct = None
            if dpa_loaded and not df_dpa_filtrado.empty and "DPA_Pct_Oficial" in df_dpa_filtrado.columns:
                _dpa_val_r = df_dpa_filtrado["DPA_Pct_Oficial"].iloc[0]
                if pd.notna(_dpa_val_r):
                    _cert_res_dpa_pct = float(_dpa_val_r)
            if _cert_res_dpa_pct is None and not df_filtrado.empty:
                _resumo_cert_res = resumo_geral(df_filtrado)
                if not _resumo_cert_res.empty:
                    _dpa_calc_r = _resumo_cert_res.iloc[0].get("DPA_Media", None)
                    if _dpa_calc_r is not None and pd.notna(_dpa_calc_r):
                        _cert_res_dpa_pct = float(_dpa_calc_r)

            _coord_res_nome = (
                "Nelson (Residencial)" if _is_nelson_res else
                "Luiz" if _is_luiz_team else
                "Vinícius"
            )

            st.markdown("---")
            st.markdown("##### 🎯 Status de Certificação — ETIT Fibra HFC &amp; DPA &amp; Assertividade")

            # Dados ausentes são tratados como dentro da meta
            _etit_hfc_ok    = (_cert_res_etit_hfc_pct  is None) or (_cert_res_etit_hfc_pct  >= 90.0)
            _dpa_res_ok     = (_cert_res_dpa_pct       is None) or (_cert_res_dpa_pct       >= 90.0)
            _dpa_res_alerta = (_cert_res_dpa_pct is not None) and (85.0 <= _cert_res_dpa_pct < 90.0)
            _assert_res_ok  = (_cert_res_media_assert  is None) or (_cert_res_media_assert  >= 85.0)

            _assumidos_res = []
            if _cert_res_etit_hfc_pct is None: _assumidos_res.append("ETIT Fibra HFC")
            if _cert_res_dpa_pct      is None: _assumidos_res.append("DPA")
            if _cert_res_media_assert is None: _assumidos_res.append("Média Assertividade")

            if _etit_hfc_ok and _dpa_res_ok and _assert_res_ok:
                _cert_res_titulo = "✅ Você está Certificando"
                _cert_res_msg    = "ETIT Fibra HFC, DPA individual e média de Assertividade dentro das metas."
                _cert_res_cor    = COR_SUCESSO
            elif _etit_hfc_ok and _dpa_res_alerta and _assert_res_ok:
                _cert_res_titulo = "⚠️ Você está Certificando"
                _cert_res_msg    = "Porém o DPA individual não está dentro da meta (85% ≤ DPA &lt; 90%)."
                _cert_res_cor    = COR_ALERTA
            else:
                _cert_res_titulo = "❌ Você NÃO está Certificando"
                _motivos_res = []
                if (_cert_res_etit_hfc_pct is not None) and (_cert_res_etit_hfc_pct < 90.0):
                    _motivos_res.append(f"ETIT Fibra HFC abaixo de 90% ({_cert_res_etit_hfc_pct:.1f}%)")
                if (_cert_res_dpa_pct is not None) and (_cert_res_dpa_pct < 85.0):
                    _motivos_res.append(f"DPA individual abaixo de 85% ({_cert_res_dpa_pct:.1f}%)")
                if (_cert_res_media_assert is not None) and (_cert_res_media_assert < 85.0):
                    _motivos_res.append(f"Média Assertividade abaixo de 85% ({_cert_res_media_assert:.1f}%)")
                _cert_res_msg = "Indicadores fora da meta — " + " · ".join(_motivos_res) + "."
                _cert_res_cor = COR_PERIGO

            if _assumidos_res:
                _cert_res_msg = (
                    f"{_cert_res_msg} (Sem dados de {', '.join(_assumidos_res)} — "
                    f"considerados dentro da meta.)"
                )

            st.markdown(
                f'<div class="kpi-card" style="border-left-color:{_cert_res_cor};">'
                f'<div class="kpi-label">Equipe {_coord_res_nome}</div>'
                f'<div class="kpi-value" style="color:{_cert_res_cor}; font-size:1.25rem;">{_cert_res_titulo}</div>'
                f'<div class="kpi-delta" style="color:{_cert_res_cor};">{_cert_res_msg}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            _cert_res_cols = st.columns(5)
            with _cert_res_cols[0]:
                _etit_val = f"{_cert_res_etit_hfc_pct:.1f}" if _cert_res_etit_hfc_pct is not None else "—"
                _etit_cor = (
                    COR_INFO if _cert_res_etit_hfc_pct is None
                    else COR_SUCESSO if _cert_res_etit_hfc_pct >= 90.0
                    else COR_PERIGO
                )
                st.markdown(
                    kpi_card("ETIT Fibra HFC %", _etit_val, _etit_cor),
                    unsafe_allow_html=True,
                )
            with _cert_res_cols[1]:
                _dpa_val = f"{_cert_res_dpa_pct:.1f}" if _cert_res_dpa_pct is not None else "—"
                _dpa_cor = COR_INFO if _cert_res_dpa_pct is None else _dpa_color(_cert_res_dpa_pct)
                st.markdown(
                    kpi_card("DPA Individual %", _dpa_val, _dpa_cor),
                    unsafe_allow_html=True,
                )
            with _cert_res_cols[2]:
                _hfc_val = f"{_cert_res_assert_hfc_pct:.1f}" if _cert_res_assert_hfc_pct is not None else "—"
                _hfc_cor = (
                    COR_SUCESSO if (_cert_res_assert_hfc_pct is not None and _cert_res_assert_hfc_pct >= 85.0)
                    else COR_PERIGO if _cert_res_assert_hfc_pct is not None
                    else COR_INFO
                )
                st.markdown(
                    kpi_card("Assert. Fibra HFC %", _hfc_val, _hfc_cor),
                    unsafe_allow_html=True,
                )
            with _cert_res_cols[3]:
                _gpon_val = f"{_cert_res_assert_gpon_pct:.1f}" if _cert_res_assert_gpon_pct is not None else "—"
                _gpon_cor = (
                    COR_SUCESSO if (_cert_res_assert_gpon_pct is not None and _cert_res_assert_gpon_pct >= 85.0)
                    else COR_PERIGO if _cert_res_assert_gpon_pct is not None
                    else COR_INFO
                )
                st.markdown(
                    kpi_card("Assert. GPON %", _gpon_val, _gpon_cor),
                    unsafe_allow_html=True,
                )
            with _cert_res_cols[4]:
                _ma_val = f"{_cert_res_media_assert:.1f}" if _cert_res_media_assert is not None else "—"
                _ma_cor = (
                    COR_INFO if _cert_res_media_assert is None
                    else COR_SUCESSO if _cert_res_media_assert >= 85.0
                    else COR_PERIGO
                )
                st.markdown(
                    kpi_card("Média Assertividade %", _ma_val, _ma_cor),
                    unsafe_allow_html=True,
                )

            st.markdown("")

        _hl_items = []

        # Produtividade
        if not df_filtrado.empty:
            _resumo_hl = resumo_geral(df_filtrado)
            if not _resumo_hl.empty:
                _r = _resumo_hl.iloc[0]
                _u_vol_hl   = _r.get(COL_VOL_TOTAL, 0)
                _u_media_hl = _r.get("Media_Diaria", 0)
                _c_vol = COR_SUCESSO if (_tm_vol_medio and _u_vol_hl >= _tm_vol_medio) else COR_ALERTA
                _c_med = COR_SUCESSO if (_tm_media_diaria and _u_media_hl >= _tm_media_diaria) else COR_ALERTA
                _hl_items.append(("Vol. Total Produt.", f"{_u_vol_hl:,.0f}", _c_vol))
                _hl_items.append(("Média/Dia Produt.", f"{_u_media_hl:,.1f}", _c_med))

        # ETIT
        if etit_loaded and not df_etit_filtrado.empty:
            _etit_ev = df_etit_filtrado[ETIT_COL_VOLUME].sum()
            _etit_ad = df_etit_filtrado[ETIT_COL_INDICADOR_VAL].sum()
            _etit_pct = (_etit_ad / _etit_ev * 100) if _etit_ev > 0 else 0
            _c_etit = COR_SUCESSO if _etit_pct >= 90 else (COR_ALERTA if _etit_pct >= 70 else COR_PERIGO)
            _hl_items.append(("Eventos ETIT", f"{int(_etit_ev):,}", COR_INFO))
            _hl_items.append(("Aderência ETIT %", f"{_etit_pct:.1f}", _c_etit))

        # DPA oficial
        if dpa_loaded and not df_dpa_filtrado.empty and "DPA_Pct_Oficial" in df_dpa_filtrado.columns:
            _u_dpa_of = df_dpa_filtrado["DPA_Pct_Oficial"].iloc[0]
            _hl_items.append(("DPA Oficial %", f"{_u_dpa_of:.1f}", _dpa_color(_u_dpa_of)))

        # TOA
        if toa_loaded and not df_toa.empty:
            _df_canc_hl = toa_canceladas_por_analista(df_toa)
            _u_canc_hl = int(_df_canc_hl["Canceladas"].sum()) if not _df_canc_hl.empty else 0
            _c_canc = COR_SUCESSO if _u_canc_hl == 0 else (COR_ALERTA if _u_canc_hl <= 2 else COR_PERIGO)
            _hl_items.append(("Canceladas TOA", str(_u_canc_hl), _c_canc))
            _df_val_hl = toa_validacao_por_analista(df_toa)
            if not _df_val_hl.empty and "Aderencia_Pct" in _df_val_hl.columns:
                _u_val_hl = _df_val_hl["Aderencia_Pct"].mean()
                _c_val = COR_SUCESSO if _u_val_hl >= 90 else (COR_ALERTA if _u_val_hl >= 70 else COR_PERIGO)
                _hl_items.append(("Ader. Validação TOA %", f"{_u_val_hl:.1f}", _c_val))

        # Fechamento
        if fech_sir_loaded and not df_fech_sir.empty:
            _n_total_hl = int(df_fech_sir[FECH_SIR_COL_VOLUME].sum())
            _n_asser_hl = int(df_fech_sir["ASSERTIVO"].sum()) if "ASSERTIVO" in df_fech_sir.columns else 0
            _pct_hl = (_n_asser_hl / _n_total_hl * 100) if _n_total_hl > 0 else 0
            _c_fech = COR_SUCESSO if _pct_hl >= 90 else (COR_ALERTA if _pct_hl >= 70 else COR_PERIGO)
            _hl_items.append(("Assertiv. Madrugada %", f"{_pct_hl:.1f}", _c_fech))

        # Chat TOA
        if chat_toa_loaded and not df_chat_toa.empty:
            _ct_kpis_hl = chat_toa_kpis_gerais(df_chat_toa)
            _c_tma_hl = COR_SUCESSO if _ct_kpis_hl.get("tma_pct", 0) >= 90 else (COR_ALERTA if _ct_kpis_hl.get("tma_pct", 0) >= 70 else COR_PERIGO)
            _hl_items.append(("Chat TMA %", f"{_ct_kpis_hl.get('tma_pct', 0):.1f}", _c_tma_hl))

        if _hl_items:
            _hl_n = min(len(_hl_items), 4)
            _hl_rows = [_hl_items[i:i+_hl_n] for i in range(0, len(_hl_items), _hl_n)]
            for _row in _hl_rows:
                _row_cols = st.columns(len(_row))
                for _ci, (_lbl, _val, _cor) in enumerate(_row):
                    with _row_cols[_ci]:
                        st.markdown(kpi_card(_lbl, _val, _cor), unsafe_allow_html=True)
                st.markdown("")

            # ── Leitura do desempenho (feedback textual construtivo) ──
            _hl_fb = build_highlight_feedback(_hl_items)
            st.markdown("---")
            st.markdown("##### 🧭 Leitura do seu desempenho")
            st.markdown(
                f'<div class="kpi-card" style="border-left-color:{COR_PRIMARIA};">'
                f'<div class="kpi-delta" style="color:inherit; font-size:0.95rem; opacity:0.95;">{_hl_fb["resumo"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown("")

            _fb_cards = [
                ("✅ Ponto Forte", _hl_fb["ponto_forte"], COR_SUCESSO),
                ("⚠️ Ponto de Atenção", _hl_fb["ponto_atencao"], COR_ALERTA),
                ("💡 Sugestão", _hl_fb["sugestao"], COR_INFO),
            ]
            _fb_cols = st.columns(3)
            for _ci, (_titulo, _texto, _cor) in enumerate(_fb_cards):
                with _fb_cols[_ci]:
                    st.markdown(
                        f'<div class="kpi-card" style="border-left-color:{_cor};">'
                        f'<div class="kpi-label" style="color:{_cor};">{_titulo}</div>'
                        f'<div class="kpi-delta" style="font-size:0.9rem; opacity:0.95; line-height:1.45;">{_texto}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            st.caption(
                "Leitura automática baseada nos seus indicadores do período. "
                "Use como apoio para planejar seus próximos passos."
            )
        else:
            st.info("Carregue os arquivos de dados para ver seus highlights.")


# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
footer_parts = [
    "Dashboard de Produtividade COP Rede",
    f"{len(df_filtrado)} registros",
    f"{n_analistas} analistas",
    f"Dados de {data_min.strftime('%d/%m/%Y') if pd.notna(data_min) else '?'} "
    f"a {data_max.strftime('%d/%m/%Y') if pd.notna(data_max) else '?'}",
]
if etit_loaded:
    footer_parts.append(f"ETIT: {len(df_etit_filtrado)} eventos")
if res_ind_loaded:
    footer_parts.append(f"Ind. Residencial: {len(df_res_filtrado):,} registros")
if toa_loaded:
    footer_parts.append(f"TOA {toa_anomes}: {len(df_toa)} registros")
if dpa_loaded:
    footer_parts.append(f"DPA Oficial: {len(df_dpa_filtrado)} analistas · {dpa_mes_info.get('mes_nome','?')} 2026")
if fech_sir_loaded:
    footer_parts.append(f"Fech. TOA x SIR {fech_sir_anomes} (Madrugada): {len(df_fech_sir)} registros")
if chat_toa_loaded:
    footer_parts.append(f"Chat TOA {chat_toa_anomes}: {len(df_chat_toa)} chats")
st.caption(" · ".join(footer_parts))
