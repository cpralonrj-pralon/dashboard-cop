import pandas as pd

# =====================================================
# EQUIPE - Matrículas e Nomes
# =====================================================
EQUIPE = [
    # EMPRESARIAL
    ("N6088107", "LEANDRO GONÇALVES DE CARVALHO", "EMPRESARIAL"),
    ("N5619600", "BRUNO COSTA BUCARD", "EMPRESARIAL"),
    ("N0189105", "IGOR MARCELINO DE MARINS", "EMPRESARIAL"),
    ("N5737414", "SANDRO DA SILVA CARVALHO", "EMPRESARIAL"),
    ("N5713690", "GABRIELA TAVARES DA SILVA", "EMPRESARIAL"),
    ("N5802257", "MAGNO FERRAREZ DE MORAIS", "EMPRESARIAL"),
    ("F201714", "FERNANDA MESQUITA DE FREITAS", "EMPRESARIAL"),
    ("N6173055", "JEFFERSON LUIS GONÇALVES COITINHO", "EMPRESARIAL"),
    ("N0125317", "ROBERTO SILVA DO NASCIMENTO", "EMPRESARIAL"),
    ("F218860", "ALDENES MARQUES IDALINO DA SILVA", "EMPRESARIAL"),
    ("N5819183", "RODRIGO PIRES BERNARDINO", "EMPRESARIAL"),
    ("N5926003", "SUELLEN HERNANDEZ DA SILVA", "EMPRESARIAL"),
    ("N5932064", "MONICA DA SILVA RODRIGUES", "EMPRESARIAL"),
    # RESIDENCIAL
    ("N0238475", "MARLEY MARQUES RIBEIRO", "RESIDENCIAL"),
    ("N5923221", "KELLY PINHEIRO LIRA", "RESIDENCIAL"),
    ("N5772086", "THIAGO PEREIRA DA SILVA", "RESIDENCIAL"),
    ("N0239871", "LEONARDO FERREIRA LIMA DE ALMEIDA", "RESIDENCIAL"),
    ("N5577565", "MARISTELLA MARCIA DOS SANTOS", "RESIDENCIAL"),
    ("N5972428", "CRISTIANE HERMOGENES DA SILVA", "RESIDENCIAL"),
    ("N4014011", "ALAN MARINHO DIAS", "RESIDENCIAL"),
    ("F106664", "RAISSA LIMA DE OLIVEIRA", "RESIDENCIAL"),
]

BASE_EQUIPE = pd.DataFrame(EQUIPE, columns=["Matricula", "Nome", "Setor"])
EQUIPE_IDS = set(BASE_EQUIPE["Matricula"].tolist())
EMPRESARIAL_IDS = set(
    BASE_EQUIPE[BASE_EQUIPE["Setor"] == "EMPRESARIAL"]["Matricula"].tolist()
)

# Líderes (supervisores)
LIDERES_IDS = {
    # Equipe Nelson / coords existentes
    "N0238475", "N5923221", "N6088107", "N5619600",             # Marley, Kelly, Leandro, Bruno
    "N5931149", "N5772610", "N5755246", "F194004",             # Daniel, Fabio, Thiago, Roberta
    # Equipe ALEXANDRE SAMPAIO (N0150817)
    "N5755480", "N0136536", "N5748944", "N5693151",             # Erika, Saulo, Thiago, Rafael
    # Equipe PATRICK SARMENTO (N5768308)
    "N5565237", "N6105199", "N6070655", "F117873",             # Antonio Clelton, Gregori, Juliana, Andressa
    # Equipe THIAGO PAROLI (TPAROLI)
    "F201734", "N5969641", "N5963374", "N5705710",             # Brenda, Carlos Alexandre, Thiago Rodrigues, Ulysses
}

# IDs dos coordenadores (sub-admins: upload sem ETIT Empresarial, sem seção ETIT)
# LUIZ/VINICIUS: coords clássicos (não veem ETIT). N0150817/N5768308/TPAROLI: sub-admins
# empresariais (veem ETIT, não veem Indicadores Residencial — ver SUB_ADMIN_EMP_IDS).
COORD_IDS = {"LUIZ", "VINICIUS", "N0150817", "N5768308", "TPAROLI"}

# Sub-admins empresariais: coordenadores que VEEM ETIT Empresarial e NÃO veem a aba
# "Indicadores Residencial" (nem eles nem seus líderes/analistas).
SUB_ADMIN_EMP_IDS = {"N0150817", "N5768308", "TPAROLI"}

# ID do super-observador: pode ver as visões de Nelson, Luiz, Vinicius e Todos
PRALON_ID = "PRALON"

# ID do super-observador empresarial: vê todos os analistas dos 3 sub-admins empresariais
# com capacidade de segmentar por equipe (Alexandre, Patrick ou Thiago Paroli).
EVANDRO_ID = "EVANDRO"

# Mapa de analistas por coordenador — preencher com as matrículas de cada equipe
# (set vazio = coordenador vê todos os analistas como fallback)
COORD_ANALYSTS_MAP: dict = {
    "LUIZ": {
        "F106663", "N5650628", "N5724716", "F105097", "N4025723",
        "N5927784", "N6027086", "N5734436", "N5923996", "N5812006",
        "F250588", "F194004", "N5973848", "N5708231", "F101864",
        "N5927655", "N5755246",
    },
    "VINICIUS": {
        "N5691268", "N0051944", "N5931149", "N5772610", "N5927887",
        "F193194", "F117879", "F250585", "N5927605", "LEOCOEM",
        "N5946675", "F118457", "N5925243", "F247715", "F104784",
        "N6028389", "N5934323",
    },
    # Sub-admin empresarial: ALEXANDRE SAMPAIO (líderes + analistas)
    "N0150817": {
        # Líderes
        "N5755480", "N0136536", "N5748944", "N5693151",
        # Analistas
        "N5780198", "N6172219", "F117877", "F119335", "N5711056",
        "F120501", "N5946649", "N6027115", "N6111746",
    },
    # Sub-admin empresarial: PATRICK SARMENTO CARNEIRO TAVARES (líderes + analistas)
    "N5768308": {
        # Líderes
        "N5565237", "N6105199", "N6070655", "F117873",
        # Analistas
        "N5577632", "N5705734", "N0067383", "N5775686", "F201801",
        "N5695123", "F101976", "N5963881", "F196679", "F257252",
    },
    # Sub-admin empresarial: THIAGO PAROLI (líderes + analistas)
    "TPAROLI": {
        # Líderes
        "F201734", "N5969641", "N5963374", "N5705710",
        # Analistas
        "N6026848", "N6172922", "N5946041", "N5739694", "F265309",
        "F236059", "N5932208", "F119481", "F282772", "F251397",
    },
}

# Todas as matrículas monitoradas: equipe fixa + analistas dos coordenadores
ALL_TRACKED_IDS = EQUIPE_IDS | {m for ids in COORD_ANALYSTS_MAP.values() for m in ids}

# Analistas visíveis para Pralon: RESIDENCIAL do Nelson + todos de Luiz e Vinicius
PRALON_ANALYSTS = (
    set(BASE_EQUIPE[BASE_EQUIPE["Setor"] == "RESIDENCIAL"]["Matricula"].tolist())
    | COORD_ANALYSTS_MAP.get("LUIZ", set())
    | COORD_ANALYSTS_MAP.get("VINICIUS", set())
)

# Analistas visíveis para Evandro: todos os 3 sub-admins empresariais
# (Chave por admin usado para segmentação no sidebar)
EVANDRO_ANALYSTS_MAP: dict = {
    "N0150817": COORD_ANALYSTS_MAP.get("N0150817", set()) | {"N0150817", "ADMIN"},
    "N5768308": COORD_ANALYSTS_MAP.get("N5768308", set()) | {"N5768308", "ADMIN"},
    "TPAROLI":  COORD_ANALYSTS_MAP.get("TPAROLI",  set()) | {"TPAROLI",  "ADMIN"},
    "ADMIN":    EMPRESARIAL_IDS | {"ADMIN"},  # Nelson — apenas EMPRESARIAL
}
EVANDRO_ANALYSTS = (
    EVANDRO_ANALYSTS_MAP["N0150817"]
    | EVANDRO_ANALYSTS_MAP["N5768308"]
    | EVANDRO_ANALYSTS_MAP["TPAROLI"]
    | EVANDRO_ANALYSTS_MAP["ADMIN"]
)

# Nome completo dos analistas dos coordenadores (login → nome)
# Usado como fallback em planilhas que não têm coluna de nome (ex: TOA, DPA)
COORD_ANALYSTS_NAMES: dict = {
    # Equipe VINICIUS
    "N5691268": "ANGELITA MARIA FIGUEIREDO NOGUEIRA",
    "N0051944": "CLAUDIO HENRIQUES ARAUJO",
    "N5931149": "DANIEL SOUZA DA SILVA",
    "N5772610": "FABIO DE OLIVEIRA MIRANDA",
    "N5927887": "FLAVIO ALVES DA COSTA",
    "F193194":  "GABRIEL PEREIRA RODRIGUES",
    "F117879":  "GABRIELE SIMM DE ALMEIDA",
    "F250585":  "JULIA SILVA WANDERLEY RIBEIRO",
    "N5927605": "LEANDRO DA SILVA",
    "LEOCOEM":  "LEONARDO COELHO DE MACEDO",
    "N5946675": "LEONARDO GARCIA CHACON PEREIRA SILVA",
    "F118457":  "LUCAS ALVES",
    "N5925243": "LUCAS CARDOSO",
    "F247715":  "NELCI STOFEL",
    "F104784":  "PHILIPE SILVA FARIAS",
    "N6028389": "THAIS ATAIDE BARRETO",
    "N5934323": "VANESSA MACEDO ZORANTE LYRA",
    # Equipe LUIZ
    "F106663":  "AMANDA DOS SANTOS SILVA",
    "N5650628": "ANDERSON GARCIA RODRIGUES",
    "N5724716": "ARMANDO PEREIRA DUARTE",
    "F105097":  "CAIO LUCIDI BOURGUIGNON",
    "N4025723": "CLAUDIA CARLA BARROS DOS SANTOS",
    "N5927784": "ELIZANGELA DE SOUZA RABELO",
    "N6027086": "ERIKA ALBUQUERQUE DIAS",
    "N5734436": "EVELYN DA SILVA",
    "N5923996": "JULIO CESAR SANTOS SOARES",
    "N5812006": "MAGNO FRANCA ASSIS",
    "F250588":  "MELISSA GUIMARAES GITAHY",
    "F194004":  "ROBERTA MATHEUS DE SOUZA",
    "N5973848": "SANDRO BREIA DE FARIA",
    "N5708231": "TATIANA GONZAGA DOS SANTOS",
    "F101864":  "TATIANE COSTA DURVAL",
    "N5927655": "THIAGO RIBEIRO DE ALMEIDA",
    "N5755246": "THIAGO SPINELLI MOTTA",
    # Equipe ALEXANDRE SAMPAIO (N0150817)
    "N5755480": "ERIKA",
    "N0136536": "SAULO",
    "N5748944": "THIAGO",
    "N5693151": "RAFAEL",
    "N5780198": "ALZINETE",
    "N6172219": "CLAUDIA",
    "F117877":  "CLAUDILENE",
    "F119335":  "DEBORAH",
    "N5711056": "ELIDA",
    "F120501":  "JAKEISE",
    "N5946649": "JULIANA",
    "N6027115": "LARISSA",
    "N6111746": "LUCIANA",
    # Equipe PATRICK SARMENTO CARNEIRO TAVARES (N5768308)
    "N5565237": "ANTONIO CLELTON FILHO",
    "N6105199": "GREGORI LIMA DE SOUZA",
    "N6070655": "JULIANA RODRIGUES MOREIRA ORLANDO",
    "F117873":  "ANDRESSA CARVALHO BARRETO LOUCHARD",
    "N5577632": "ALINE LOURENCO ALVES ANDRADE",
    "N5705734": "MICHELE GUARANHO ANSELMO PEREIRA",
    "N0067383": "RAPHAEL DE MELO FERREIRA",
    "N5775686": "ELIAS DA SILVA DE GOBBI",
    "F201801":  "ADRIANO BOAS NASCIMENTO",
    "N5695123": "SIMONE ASSIS DA COSTA",
    "F101976":  "TAYLISSA ELOIZA ROSA MESSIAS",
    "N5963881": "TIAGO ALMEIDA TIBURCIO DE SOUZA",
    "F196679":  "PHELIPE PACHECO DE CARVALHO",
    "F257252":  "PABLO HENRIQUE ALVES ALMEIDA",
    # Equipe THIAGO PAROLI (TPAROLI)
    "F201734":  "BRENDA FERNANDA DA SILVA DAVID",
    "N5969641": "CARLOS ALEXANDRE COSTA DE OLIVEIRA",
    "N5963374": "THIAGO RODRIGUES LOPES",
    "N5705710": "ULYSSES FERREIRA DOS SANTOS",
    "N6026848": "BRUNO RIBEIRO ARAUJO",
    "N6172922": "DJALMIR SILVA DE SENA",
    "N5946041": "FABIO ANGELO MAGELA DE ALMEIDA",
    "N5739694": "GUILHERME SCALON DA SILVA COELHO",
    "F265309":  "HELLITON DOS SANTOS SILVA",
    "F236059":  "KELSON RICARDO CRUZ MACEDO",
    "N5932208": "KETLIN MACIELE DOS SANTOS TEIXEIRA ROCHA",
    "F119481":  "LAYSSA MENDES DE LIMA",
    "F282772":  "JOAO GABRIEL DE ALMEIDA FERREIRA",
    "F251397":  "YAN RIBEIRO DE BARROS LIMA",
}

# Turnos que cada coordenador cobre nos Indicadores Residencial
# (usados quando a planilha não tem coluna de login)
COORD_TURNOS_MAP: dict = {
    "LUIZ":     {"Manhã", "Tarde"},
    "VINICIUS": {"Manhã", "Tarde"},
}

# Matrículas alternativas → matrícula canônica (mesmo analista, login diferente)
LOGIN_ALIASES = {
    "N6105010": "N6173055",  # alias do Jefferson Luis Gonçalves Coitinho
}

# Lookup consolidado Matricula → Nome (equipe fixa + todos os analistas dos coordenadores)
LOGIN_TO_NOME: dict = {
    **{row.Matricula: row.Nome for row in BASE_EQUIPE.itertuples()},
    **COORD_ANALYSTS_NAMES,
}

def name_for_login(mat) -> str:
    """Retorna o nome completo da matrícula, se mapeada; caso contrário, a própria matrícula."""
    if mat is None:
        return ""
    s = str(mat).strip()
    if not s:
        return ""
    key = LOGIN_ALIASES.get(s.upper(), s.upper())
    return LOGIN_TO_NOME.get(key, s)

# =====================================================
# COLUNAS ESPERADAS NA PLANILHA DE PRODUTIVIDADE
# =====================================================
COL_LOGIN = "USUARIO_LOGIN"
COL_NOME = "USUARIO_NOME"
COL_BASE = "USUARIO_BASE"
COL_COORD = "USUARIO_COORD"
COL_CARGO = "USUARIO_CARGO"
COL_PERIODO = "USUARIO_PERIODO"
COL_DATA = "DATA"
COL_MES = "MESNOME"
COL_ANOMES = "ANOMES"

# Volumes
VOL_COLS = {
    "VOL_AB_NM": "Abertura New Monitor",
    "VOL_FE_NM": "Fechamento New Monitor",
    "VOL_FE_NM_MANOBRA": "Fechamento NM Manobra",
    "VOL_AB_SGO": "Abertura SGO",
    "VOL_TRAT_SGO": "Tratamento SGO",
    "VOL_AC_SGO": "Aceite SGO",
    "VOL_FE_SGO": "Fechamento SGO",
    "VOL_AB_OSS": "Abertura Remedy",
    "VOL_FE_OSS": "Fechamento OSS",
    "VOL_AC_OSS": "Aceite OSS",
    "VOL_RAL": "Tratativa RAL",
    "VOL_REC": "Tratativa REC",
    "VOL_AB_RAL": "Abertura RAL",
    "VOL_REMEDY_MOVEL": "Remedy Móvel",
    "VOL_TOA_PRIM_INT": "Primeira Interação TOA",
    "VOL_TOA_FORM": "Fechamento Tarefa TOA",
    "VOL_TELEFONIA_RECEBIDO": "Telefonia Recebido",
    "VOL_TELEFONIA_ATENDIDO": "Telefonia Atendido",
    "VOL_TELEFONIA_REALIZADO": "Ligações Realizadas",
}

VOL_COLS_RESIDENCIAL = {
    "VOL_AB_NM": "Ab. New Monitor",
    "VOL_FE_NM": "Fech. New Monitor",
    "VOL_AB_SGO": "Ab. SGO",
    "VOL_FE_SGO": "Fech. SGO",
}

VOL_COLS_EMPRESARIAL = {
    "VOL_RAL": "Trat. RAL",
    "VOL_REC": "Trat. REC",
}

VOL_COLS_AMBOS = {
    "VOL_AB_OSS": "Ab. Remedy",
    "VOL_TELEFONIA_REALIZADO": "Ligações Realiz.",
    "VOL_TOA_PRIM_INT": "1ª Interação TOA",
    "VOL_TOA_FORM": "Fech. Tarefa TOA",
}

COL_VOL_TOTAL = "VOL_TOTAL"
COL_VOL_MEDIA = "VOL_TOTAL_MEDIA_POR_DIA"

# DPA (Ocupação)
COL_DPA_USO = "DPA_TEMPO_USO_SEC"
COL_DPA_JORNADA = "DPA_HORARIO_JORNADA_SEC"
COL_DPA_RESULTADO = "DPA_RESULTADO"

# Header row na planilha (0-indexed)
HEADER_ROW = 10

# Nome da aba (fallback: primeira aba)
SHEET_NAME_CANDIDATES = [
    "Analítico Produtividade 2026",
    "Analítico Produtividade",
    "Produtividade",
]

# =====================================================
# ETIT POR EVENTO — Colunas da planilha Analítico Empresarial
# =====================================================
ETIT_INDICADOR_FILTRO = "ETIT POR EVENTO"
ETIT_COL_INDICADOR = "INDICADOR_NOME"
ETIT_COL_LOGIN = "LOGIN_ACIONAMENTO"
ETIT_COL_DEMANDA = "DEMANDA"
ETIT_COL_NOTA = "NOTA"
ETIT_COL_VOLUME = "VOLUME"
ETIT_COL_INDICADOR_VAL = "INDICADOR"
ETIT_COL_STATUS = "INDICADOR_STATUS"
ETIT_COL_TIPO = "TIPO"
ETIT_COL_AREA = "AREA_ENVOLVIDA"
ETIT_COL_CAUSA = "CAUSA"
ETIT_COL_REGIONAL = "IN_REGIONAL"
ETIT_COL_GRUPO = "IN_GRUPO"
ETIT_COL_CIDADE = "IN_CIDADE_UF"
ETIT_COL_UF = "IN_UF"
ETIT_COL_TOA = "ENVIADO_TOA"
ETIT_COL_DT_INICIO = "DT_INICIO"
ETIT_COL_DT_FIM = "DT_FIM"
ETIT_COL_DT_EMISSAO = "DT_EMISSAO"
ETIT_COL_DT_ACIONAMENTO = "DT_ACIONAMENTO"
ETIT_COL_TURNO = "TURNO"
ETIT_COL_TMA = "TMA"
ETIT_COL_TMR = "TMR"
ETIT_COL_ANOMES = "ANOMES"

ETIT_SHEET_CANDIDATES = ["Empresarial", "ETIT", "Analítico"]

# =====================================================
# INDICADORES RESIDENCIAL — Planilha Analítico Indicadores
# =====================================================
RES_IND_ETIT_FIBRA_HFC        = "ETIT FIBRA HFC"
RES_IND_ETIT_GPON              = "ETIT GPON"
RES_IND_REPROG_GPON            = "REPROGRAMAÇÃO GPON"          # mantido por compatibilidade
RES_IND_LOG_REPROG_GPON        = "LOG REPROGRAMAÇÃO GPON"
RES_IND_ASSERT_FIBRA_HFC       = "ASSERTIVIDADE ACIONAMENTO FIBRA HFC"
RES_IND_ASSERT_GPON            = "ASSERTIVIDADE ACIONAMENTO GPON"

# Apenas estes indicadores são exibidos no dashboard
RES_INDICADORES_FILTRO = [
    RES_IND_ETIT_FIBRA_HFC,
    RES_IND_ETIT_GPON,
    RES_IND_ASSERT_FIBRA_HFC,
    RES_IND_ASSERT_GPON,
]

RES_IND_LABELS = {
    RES_IND_ETIT_FIBRA_HFC:    "ETIT Fibra HFC",
    RES_IND_ETIT_GPON:         "ETIT GPON",
    RES_IND_ASSERT_FIBRA_HFC:  "Assert. Acion. Fibra HFC",
    RES_IND_ASSERT_GPON:       "Assert. Acion. GPON",
}

RES_IND_COLORS = {
    RES_IND_ETIT_FIBRA_HFC:    "#E67E22",
    RES_IND_ETIT_GPON:         "#8E44AD",
    RES_IND_ASSERT_FIBRA_HFC:  "#2E86C1",
    RES_IND_ASSERT_GPON:       "#27AE60",
}

# Invertidos: INDICADOR=0 → ADERENTE (reservado para indicadores onde 0 é bom)
RES_IND_INVERTIDOS: set = set()

RES_COL_INDICADOR_NOME  = "INDICADOR_NOME_ICG"
RES_COL_ID_MOSTRA       = "ID_MOSTRA"
RES_COL_LOGIN_FO        = "LOGIN_PRIMEIRO_ACIONAMENTO_FO"
RES_COL_LOGIN_GPON      = "LOGIN_PRIMEIRO_ACIONAMENTO_GPON"
# Layout 202608: a origem consolidou as duas colunas acima em uma única coluna.
# O loader mantém suporte simultâneo ao schema legado e ao consolidado.
RES_COL_LOGIN_UNIFIED   = "LOGIN_PRIMEIRO_ACIONAMENTO"
RES_COL_LOGIN           = "RES_LOGIN"   # coluna unificada de login (calculada no loader)
RES_COL_VOLUME          = "VOLUME"
RES_COL_INDICADOR_VAL   = "INDICADOR"
RES_COL_STATUS          = "INDICADOR_STATUS"
RES_COL_REGIONAL        = "IN_REGIONAL"
RES_COL_GRUPO           = "IN_GRUPO"
RES_COL_CIDADE          = "IN_CIDADE_UF"
RES_COL_UF              = "IN_UF"
RES_COL_TECNOLOGIA      = "TECNOLOGIA"
RES_COL_SERVICO         = "SERVICO"
RES_COL_NATUREZA        = "NATUREZA"
RES_COL_SINTOMA         = "SINTOMA"
RES_COL_FERRAMENTA      = "FERRAMENTA_ABERTURA"
RES_COL_FECHAMENTO      = "FECHAMENTO"
RES_COL_SOLUCAO         = "SOLUCAO"
RES_COL_IMPACTO         = "IMPACTO"
RES_COL_ENVIADO_TOA     = "ENVIADO_TOA"
RES_COL_DT_INICIO       = "DT_INICIO"
RES_COL_DT_FIM          = "DT_FIM"
RES_COL_DT_FIM_SISTEMA  = "DT_FIM_SISTEMA_PRIMEIRO_FECHAMENTO"
RES_COL_TMA             = "TMA"
RES_COL_TMR             = "TMR"
RES_COL_ANOMES          = "ANOMES"
RES_COL_TURNO           = "TURNO"   # coluna calculada a partir do horário do evento

RES_SHEET_CANDIDATES = ["Analitico", "Analítico", "Residencial", "Sheet1"]

# =====================================================
# OCUPAÇÃO DPA — Planilha Ocupação_DPA_2026
# =====================================================

# Nomes das abas na planilha de Ocupação DPA
DPA_SHEET_ANALISTAS   = "Analistas"
DPA_SHEET_CONSOLIDADO = "Consolidado"

# Lista de meses em português (para detectar o mês mais recente)
DPA_MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

# Thresholds de semáforo para DPA%
DPA_THRESHOLD_OK      = 90.0   # >= verde
DPA_THRESHOLD_ALERTA  = 85.0   # >= amarelo, < verde
# abaixo de DPA_THRESHOLD_ALERTA = vermelho

# Abas possíveis (candidatos, caso os nomes mudem)
DPA_SHEET_CANDIDATES = ["Analistas", "Analisats", "Analistas DPA"]

# =====================================================
# INDICADORES TOA — Planilha Analitico_Indicadores_TOA
# =====================================================

# Aba da planilha (candidatos por ordem de preferência)
TOA_IND_SHEET = "TOA"
TOA_SHEET_CANDIDATES = ["TOA", "Planilha1", "Sheet1", "Analitico", "Analítico", "INDICADORES"]

# Nomes dos indicadores que queremos (exatamente como aparecem na coluna)
TOA_IND_CANCELADAS  = "TAREFAS CANCELADAS"
TOA_IND_VALIDACAO   = "TEMPO DE VALIDAÇÃO DO FORMULÁRIO"

TOA_INDICADORES_FILTRO = [TOA_IND_CANCELADAS, TOA_IND_VALIDACAO]

# Rótulos curtos
TOA_IND_LABELS = {
    TOA_IND_CANCELADAS: "Tarefas Canceladas",
    TOA_IND_VALIDACAO:  "Tempo Validação Form.",
}

# Cores por indicador
TOA_IND_COLORS = {
    TOA_IND_CANCELADAS: "#E74C3C",   # vermelho — menor = melhor
    TOA_IND_VALIDACAO:  "#16A085",   # verde-azulado — aderência
}

# Para TAREFAS CANCELADAS: INDICADOR=1 = CANCELADA = ruim (indicador invertido)
# Para TEMPO DE VALIDAÇÃO: INDICADOR=1 = ADERENTE = bom
TOA_IND_INVERTIDOS = {TOA_IND_CANCELADAS}

# Colunas da planilha TOA
TOA_COL_INDICADOR_NOME  = "INDICADOR_NOME"
TOA_COL_ID_ATIVIDADE    = "ID_ATIVIDADE"
TOA_COL_LOGIN           = "LOGIN"
TOA_COL_RESPONSAVEL     = "RESPONSAVEL"
TOA_COL_REGIONAL        = "IN_REGIONAL"
TOA_COL_GRUPO           = "IN_GRUPO"
TOA_COL_CIDADE          = "IN_CIDADE_UF"
TOA_COL_UF              = "IN_UF"
TOA_COL_TIPO_ATIVIDADE  = "TIPO_ATIVIDADE"
TOA_COL_TIPO_INCIDENTE  = "TIPO_INCIDENTE"
TOA_COL_REDE            = "REDE"
TOA_COL_MERCADO         = "MERCADO"
TOA_COL_NATUREZA        = "NATUREZA"
TOA_COL_MDU             = "MDU"
TOA_COL_FECHAMENTO      = "FECHAMENTO"
TOA_COL_SOLUCAO         = "SOLUCAO"
TOA_COL_DATA            = "DATA"
TOA_COL_DT_ROTEAMENTO   = "DT_ROTEAMENTO"
TOA_COL_DT_INICIO_FORM  = "DT_INICIO_FORM"
TOA_COL_DT_FIM_FORM     = "DT_FIM_FORM"
TOA_COL_DT_CANCELAMENTO = "DT_CANCELAMENTO"
TOA_COL_TMR             = "TMR"
TOA_COL_AGING           = "AGING"
TOA_COL_INDICADOR       = "INDICADOR"
TOA_COL_STATUS          = "INDICADOR_STATUS"
TOA_COL_ANOMES          = "ANOMES"

# Ordenação dos faixas de AGING (do menor para o maior)
TOA_AGING_ORDER = [
    "Até 1 Min", "Até 5 Min", "Até 15 Min", "Até 30 Min",
    "Até 60 Min", "Até 04 Horas", "Até 08 Horas", "Até 12 Horas",
    "Até 24 Horas", "Até 48 Horas", "Maior 48 Horas",
]

# =====================================================
# FECHAMENTO TOA x SIR — Planilha Fechamento_TOA_x_SIR
# =====================================================
# Dados extraídos do pivot cache interno (não das abas visíveis)

FECH_SIR_TURNO_MADRUGADA = "Madrugada"

FECH_SIR_COL_LOGIN      = "LOGIN_VALIDOU_FECHAMENTO"
FECH_SIR_COL_TURNO      = "TURNO"
FECH_SIR_COL_ANOMES     = "ANOMES"
FECH_SIR_COL_VOLUME     = "VOLUME"
FECH_SIR_COL_ASSERTIVO  = "FECHAMENTO_ASSERTIVO"
FECH_SIR_COL_NAO_ASSER  = "FECHAMENTO_NAO_ASSERTIVO"
FECH_SIR_COL_CAUSA_TOA  = "CAUSA_TOA"
FECH_SIR_COL_CAUSA_SIR  = "CAUSA_SIR"
FECH_SIR_COL_CAUSA_TRAT = "CAUSA_TOA_TRATADO"
FECH_SIR_COL_REGIONAL   = "IN_REGIONAL"
FECH_SIR_COL_GRUPO      = "IN_GRUPO"
FECH_SIR_COL_DEMANDA    = "DEMANDA"
FECH_SIR_COL_AREA       = "AREA"
FECH_SIR_COL_AREA_ENV   = "AREA_ENVOLVIDA"
FECH_SIR_COL_DIA        = "DIA"
FECH_SIR_COL_MES        = "MES"
FECH_SIR_COL_STATUS     = "STATUS"

FECH_SIR_COR = "#8E44AD"   # roxo — assertividade TOA x SIR

# =====================================================
# CHAT TOA — Planilha Analítico TOA Chat
# =====================================================
CHAT_TOA_SHEET          = "Analítico CHAT TOA"
CHAT_TOA_HEADER_ROW     = 3   # 0-indexed

CHAT_TOA_COL_ID         = "ID_CHAT"
CHAT_TOA_COL_INICIO     = "CHAT_INICIO"
CHAT_TOA_COL_FIM        = "CHAT_FIM"
CHAT_TOA_COL_FIM_ANAL   = "CHAT_FIM_ANALISTA"
CHAT_TOA_COL_ANOMES     = "ABERTURA_ANOMES"
CHAT_TOA_COL_MES        = "ABERTURA_MES"
CHAT_TOA_COL_DIA        = "ABERTURA_DIA"
CHAT_TOA_COL_HORA       = "ABERTURA_HORA"
CHAT_TOA_COL_ABERTURA_USER = "ABERTURA_USER"
CHAT_TOA_COL_PRIMEIRA_INT  = "PRIMEIRA_INTERACAO_COPREDE_LOGIN"
CHAT_TOA_COL_FILA_TIPO  = "FECHAMENTO_TIPO_FILA"
CHAT_TOA_COL_FILA       = "FECHAMENTO_FILA"
CHAT_TOA_COL_LOGIN      = "FECHAMENTO_COPREDE_LOGIN_ANALISTA"
CHAT_TOA_COL_BASE       = "FECHAMENTO_COPREDE_BASE_ANALISTA"
CHAT_TOA_COL_GESTAO     = "FECHAMENTO_COPREDE_GESTAO_ANALISTA"
CHAT_TOA_COL_MINUTOS_TMA = "MINUTOS_TMA"
CHAT_TOA_COL_IND_TMA    = "INDICADOR_TMA_DENTRO"
CHAT_TOA_COL_LEFT_CHAT  = "VOL_LEFTCHAT_ANALISTAS"
CHAT_TOA_COL_ENVOLV     = "QTD_ENVOLVIMENTO"

# Limites dos indicadores
CHAT_TMA_LIMITE_MIN  = 10    # TMA ≤ 10min = dentro do prazo (referência de meta)

# Cor do módulo Chat TOA
CHAT_TOA_COR = "#1ABC9C"  # verde-azulado

# =====================================================
# FILTRO REGIONAL
# =====================================================
# Filtra todos os dados para a regional Leste apenas.
# Altere aqui caso a regional mude.
REGIONAL_FILTRO = "Leste"

# =====================================================
# CORES DO DASHBOARD
# =====================================================
COR_PRIMARIA = "#1B4F72"
COR_SUCESSO = "#27AE60"
COR_ALERTA = "#F39C12"
COR_PERIGO = "#E74C3C"
COR_INFO = "#2980B9"
