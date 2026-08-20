"""Módulo de autenticação do dashboard COP Rede."""
import hashlib, json, os, secrets, time
import streamlit as st
from pathlib import Path
from src import storage

DATA_DIR = Path(os.environ.get("APP_DATA_DIR", "data"))
PASSWORDS_FILE = DATA_DIR / "passwords.json"
UPLOADS_DIR = DATA_DIR / "uploads"
_R2_PASSWORDS = "passwords.json"
_R2_UPLOADS   = "uploads/"
DEFAULT_PASSWORD = "claro123"
AUTH_ADMIN_ID = "ADMIN"

UPLOAD_FILE_MAP: dict = {
    "uploaded_bytes":          "produtividade.xlsx",
    "uploaded_etit_bytes":     "etit.xlsx",
    "uploaded_res_ind_bytes":  "residencial_indicadores.xlsx",
    "uploaded_toa_bytes":      "toa.xlsx",
    "uploaded_dpa_bytes":      "dpa.xlsx",
    "uploaded_fech_sir_bytes": "fechamento_toa_sir.xlsx",
    "uploaded_chat_toa_bytes": "chat_toa.xlsx",
}

def _hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000).hex()
    return hashed, salt

def _load_passwords() -> dict:
    if storage.r2_available():
        raw = storage.download(_R2_PASSWORDS)
        if raw is None: return {}
        try: return json.loads(raw.decode("utf-8"))
        except: return {}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PASSWORDS_FILE.exists(): return {}
    try: return json.loads(PASSWORDS_FILE.read_text(encoding="utf-8"))
    except: return {}

def _save_passwords(data: dict) -> bool:
    payload = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    if storage.r2_available():
        return bool(storage.upload(_R2_PASSWORDS, payload))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PASSWORDS_FILE.write_bytes(payload)
    return True

def ensure_users_initialized(equipe_ids: set) -> int:
    """Cria entradas faltantes em passwords.json com senha padrão.
    Retorna o número de matrículas adicionadas nesta execução.
    Levanta RuntimeError se a persistência falhar (R2 upload indisponível)."""
    from src.config import COORD_IDS, PRALON_ID, EVANDRO_ID
    data = _load_passwords(); added = 0
    for uid in list(equipe_ids) + [AUTH_ADMIN_ID] + list(COORD_IDS) + [PRALON_ID, EVANDRO_ID]:
        uid_up = uid.upper()
        if uid_up not in data:
            hashed, salt = _hash_password(DEFAULT_PASSWORD)
            data[uid_up] = {"hash": hashed, "salt": salt, "must_change": True}
            added += 1
    # Se FORCE_ADMIN_PASSWORD definido, força redefinição da senha do admin no R2
    force_pwd = storage.get_env_or_secret("FORCE_ADMIN_PASSWORD")
    force_admin = False
    if force_pwd:
        hashed, salt = _hash_password(force_pwd)
        data[AUTH_ADMIN_ID] = {"hash": hashed, "salt": salt, "must_change": False}
        force_admin = True
    if added or force_admin:
        if not _save_passwords(data):
            raise RuntimeError(
                "Falha ao persistir passwords.json no R2. "
                "Verifique credenciais/bucket (R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME)."
            )
    return added


def list_missing_tracked_ids(tracked_ids: set) -> list:
    """Retorna matrículas de tracked_ids que NÃO estão em passwords.json (ordenado)."""
    data = _load_passwords()
    missing = [uid for uid in tracked_ids if uid.upper() not in data]
    return sorted(missing)

def verify_login(username: str, password: str):
    uid = username.strip().upper()
    # Override de emergência para admin via variável de ambiente ou Streamlit Secrets
    if uid == AUTH_ADMIN_ID:
        override = storage.get_env_or_secret("ADMIN_PASSWORD_OVERRIDE")
        if override and password == override:
            return True, False
    data = _load_passwords()
    if uid not in data: return False, False
    user_data = data[uid]
    hashed, _ = _hash_password(password, user_data["salt"])
    if hashed == user_data["hash"]: return True, user_data.get("must_change", False)
    return False, False

def change_password(username: str, new_password: str) -> None:
    data = _load_passwords(); uid = username.strip().upper()
    hashed, salt = _hash_password(new_password)
    data[uid] = {"hash": hashed, "salt": salt, "must_change": False}
    _save_passwords(data)

def reset_user_passwords(usernames) -> int:
    """Reseta em uma única gravação apenas os usuários informados.

    IDs inexistentes são ignorados. Uma falha de persistência é reportada ao
    chamador para que a interface não anuncie um reset que não foi salvo.
    """
    target_ids = {
        str(username).strip().upper()
        for username in usernames
        if str(username).strip()
    }
    if not target_ids:
        return 0

    data = _load_passwords()
    count = 0
    for uid in sorted(target_ids):
        if uid not in data:
            continue
        hashed, salt = _hash_password(DEFAULT_PASSWORD)
        data[uid] = {"hash": hashed, "salt": salt, "must_change": True}
        count += 1

    if count and not _save_passwords(data):
        raise RuntimeError("Falha ao persistir o reset de senhas.")
    return count


def reset_non_admin_passwords(preserve_ids: set = None) -> int:
    """Reseta senhas de todos os usuários fora de preserve_ids para o padrão.
    Retorna o número de usuários resetados."""
    if preserve_ids is None:
        preserve_ids = {"ADMIN"}
    preserve_upper = {p.upper() for p in preserve_ids}
    data = _load_passwords()
    count = 0
    for uid in list(data.keys()):
        if uid.upper() not in preserve_upper:
            hashed, salt = _hash_password(DEFAULT_PASSWORD)
            data[uid] = {"hash": hashed, "salt": salt, "must_change": True}
            count += 1
    _save_passwords(data)
    return count


def reset_user_password(username: str) -> bool:
    """Reseta a senha de um único usuário para o padrão com troca obrigatória.
    Retorna True se o usuário foi encontrado."""
    data = _load_passwords()
    uid = username.strip().upper()
    if uid not in data:
        return False
    hashed, salt = _hash_password(DEFAULT_PASSWORD)
    data[uid] = {"hash": hashed, "salt": salt, "must_change": True}
    _save_passwords(data)
    return True


def save_uploaded_file(session_key: str, file_bytes: bytes) -> None:
    if session_key not in UPLOAD_FILE_MAP: return
    filename = UPLOAD_FILE_MAP[session_key]
    ts = str(time.time())
    if storage.r2_available():
        file_ok = storage.upload(f"{_R2_UPLOADS}{filename}", file_bytes)
        if file_ok:
            # Só atualiza o version após confirmar que o arquivo foi gravado.
            # Evita que outros sessões baixem o arquivo antigo com versão nova.
            storage.upload(f"{_R2_UPLOADS}{filename}.version", ts.encode())
            # Sincroniza a versão no session_state para que load_saved_files_to_session
            # não re-baixe do R2 e sobrescreva os bytes recém enviados.
            st.session_state[session_key + "_r2_version"] = ts
        _get_file_version.clear()
        return
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOADS_DIR / filename).write_bytes(file_bytes)
    (UPLOADS_DIR / (filename + ".version")).write_bytes(ts.encode())
    # Sincroniza versão local no session_state para evitar re-leitura do disco.
    st.session_state[session_key + "_local_version"] = ts


def get_upload_timestamp(filename: str = "produtividade.xlsx") -> str | None:
    """Retorna a data/hora do último upload do arquivo, formatada, ou None se não disponível."""
    from datetime import datetime
    ver = _get_file_version(filename)
    if ver == "0":
        return None
    try:
        return datetime.fromtimestamp(float(ver)).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def _get_file_version(filename: str) -> str:
    """Lê o timestamp de versão do arquivo (TTL=5 min) para cache-busting entre sessões."""
    if storage.r2_available():
        raw = storage.download(f"{_R2_UPLOADS}{filename}.version")
        if raw is None:
            return "0"
        try:
            return raw.decode("utf-8").strip()
        except Exception:
            return "0"
    # Modo local: lê o arquivo .version gravado junto ao upload no disco
    ver_path = DATA_DIR / "uploads" / (filename + ".version")
    if ver_path.exists():
        try:
            return ver_path.read_text(encoding="utf-8").strip()
        except Exception:
            return "0"
    return "0"

@st.cache_data(ttl=1800, show_spinner=False)
def _r2_cached_download(filename: str, version: str) -> bytes | None:
    return storage.download(f"{_R2_UPLOADS}{filename}")

_R2_CHECK_INTERVAL_SEC = 300  # ~5 min entre verificações de versão R2 por sessão

def load_saved_files_to_session(excluded_keys: set | None = None) -> None:
    """Carrega arquivos salvos do R2/disco para o session_state.

    Para evitar 'RUNNING' constante a cada interação do usuário, a verificação
    de versão no R2 só ocorre quando:
      • é a primeira carga da sessão (algum arquivo ausente do session_state); ou
      • passou mais de _R2_CHECK_INTERVAL_SEC desde a última checagem.
    Caso contrário, retorna sem fazer chamadas de rede.
    """
    excluded = set(excluded_keys or set())
    active_file_map = {
        key: filename
        for key, filename in UPLOAD_FILE_MAP.items()
        if key not in excluded
    }

    # Evita reaproveitar dados de uma conta anterior na mesma sessão do navegador.
    for key in excluded:
        st.session_state.pop(key, None)
        st.session_state.pop(key + "_name", None)

    if storage.r2_available():
        _now = time.time()
        _last = st.session_state.get("_r2_last_check_ts", 0.0)
        _all_loaded = all(k in st.session_state for k in active_file_map)
        if _all_loaded and (_now - _last) < _R2_CHECK_INTERVAL_SEC:
            return  # nada a fazer — sem rede, sem spinner

        # Verifica versões e baixa apenas o que mudou
        for key, filename in active_file_map.items():
            version = _get_file_version(filename)
            version_key = key + "_r2_version"
            if st.session_state.get(version_key) != version:
                data = _r2_cached_download(filename, version)
                if data is not None:
                    st.session_state[key] = data
                    st.session_state[version_key] = version
            elif key not in st.session_state:
                data = _r2_cached_download(filename, version)
                if data is not None:
                    st.session_state[key] = data
                    st.session_state[version_key] = version
        st.session_state["_r2_last_check_ts"] = _now
        return

    # Modo local — verifica arquivo .version para detectar uploads feitos pelo admin
    for key, filename in active_file_map.items():
        ver_path = DATA_DIR / "uploads" / (filename + ".version")
        version_key = key + "_local_version"
        disk_version = ver_path.read_text(encoding="utf-8").strip() if ver_path.exists() else "0"
        if st.session_state.get(version_key) == disk_version and key in st.session_state:
            continue  # arquivo não mudou, mantém bytes em memória
        path = UPLOADS_DIR / filename
        if path.exists():
            st.session_state[key] = path.read_bytes()
            st.session_state[version_key] = disk_version

def saved_files_exist() -> bool:
    if storage.r2_available(): return storage.exists(f"{_R2_UPLOADS}produtividade.xlsx")
    return (UPLOADS_DIR / "produtividade.xlsx").exists()


# ── Páginas de autenticação ─────────────────────────────────────────────────

def _login_css(dark: bool) -> str:
    """Retorna o bloco <style> completo para a tela de login."""
    if not dark:
        bg    = "#F4F4F4"
        t1    = "#111111"
        t2    = "#666666"
        brd   = "#E4E4E4"
        ib    = "#FAFAFA"
        it    = "#111111"
        ibr   = "#D8D8D8"
    else:
        bg    = "#0C0C0C"
        t1    = "#F0F0F0"
        t2    = "#909090"
        brd   = "#2C2C2C"
        ib    = "#1E1E1E"
        it    = "#F0F0F0"
        ibr   = "#303030"

    return f"""<style>
/* ── reset Streamlit chrome ── */
[data-testid="stSidebar"],[data-testid="stDecoration"],
header[data-testid="stHeader"],#MainMenu,footer,
[data-testid="stToolbar"],[data-testid="stStatusWidget"]{{display:none!important}}
.stApp{{background:{bg}!important;overflow:hidden}}
.stApp [data-testid="stAppViewContainer"]>section.main>div.block-container{{
    padding:0!important;max-width:100%!important
}}

/* ── split columns ── */
[data-testid="stHorizontalBlock"]{{
    gap:0!important;padding:0!important;margin:0!important;
    align-items:stretch!important;min-height:100vh!important
}}
[data-testid="stHorizontalBlock"]>[data-testid="stColumn"],
[data-testid="stHorizontalBlock"]>[data-testid="column"]{{padding:0!important}}

/* left col */
[data-testid="stColumn"]:first-child,
[data-testid="column"]:first-child{{
    background:linear-gradient(135deg,#ED1C24 0%,#C8161D 25%,#8B0B12 52%,#2D0305 78%,#0a0a0a 100%)!important;
    background-size:300% 300%!important;animation:gradShift 10s ease infinite!important;
    min-height:100vh;overflow:hidden;position:relative
}}
@keyframes gradShift{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}
[data-testid="stColumn"]:first-child::before,
[data-testid="column"]:first-child::before{{content:'';position:absolute;inset:0;
    background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);
    background-size:40px 40px;pointer-events:none}}
[data-testid="stColumn"]:first-child::after,
[data-testid="column"]:first-child::after{{content:'';position:absolute;width:420px;height:420px;border-radius:50%;
    background:radial-gradient(circle,rgba(255,255,255,.07) 0%,transparent 65%);
    top:-120px;right:-130px;pointer-events:none}}
[data-testid="stColumn"]:first-child>div,
[data-testid="column"]:first-child>div{{
    height:100%;display:flex!important;flex-direction:column!important;
    align-items:flex-start!important;justify-content:center!important;
    padding:3rem 3.5rem!important
}}

/* right col */
[data-testid="stColumn"]:last-child,
[data-testid="column"]:last-child{{
    background:{bg}!important;min-height:100vh
}}
[data-testid="stColumn"]:last-child>div,
[data-testid="column"]:last-child>div{{
    height:100%;display:flex!important;flex-direction:column!important;
    align-items:center!important;justify-content:center!important;padding:1.5rem 2.5rem!important;
    overflow:hidden!important
}}

/* ── branding ── */
.lp-logo-row{{display:flex;align-items:center;gap:12px;margin-bottom:2.8rem}}
.lp-dot-grid{{display:grid;grid-template-columns:1fr 1fr;gap:4px;width:28px;height:28px}}
.lp-dot-grid span{{display:block;width:11px;height:11px;border-radius:50%;background:rgba(255,255,255,.92)}}
.lp-dot-grid span:nth-child(2),.lp-dot-grid span:nth-child(4){{background:rgba(255,255,255,.42)}}
.lp-logo-name{{font-size:1.4rem;font-weight:700;color:#fff;letter-spacing:-.5px}}
.lp-heading{{font-size:2.4rem;font-weight:800;color:#fff;line-height:1.15;
             letter-spacing:-.5px;margin:0 0 1rem 0;max-width:320px}}
.lp-tagsub{{font-size:.88rem;color:rgba(255,255,255,.6);line-height:1.65;
            max-width:300px;margin:0 0 2.4rem 0}}
.lp-features{{display:flex;flex-direction:column;gap:10px}}
.lp-feat-item{{display:flex;align-items:center;gap:10px;
               font-size:.82rem;color:rgba(255,255,255,.72);font-weight:500}}
.lp-feat-icon{{width:30px;height:30px;border-radius:8px;background:rgba(255,255,255,.12);
               display:flex;align-items:center;justify-content:center;font-size:.78rem;flex-shrink:0}}
.lp-brand-footer{{margin-top:3rem;font-size:.66rem;color:rgba(255,255,255,.26);letter-spacing:.3px}}
.lp-brand-circle{{position:absolute;width:260px;height:260px;border-radius:50%;
    background:radial-gradient(circle,rgba(255,80,80,.14) 0%,transparent 70%);
    bottom:50px;left:-70px;pointer-events:none;animation:floatUp 8s ease-in-out infinite}}
@keyframes floatUp{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-14px)}}}}

/* ── form area ── */
.lp-rcard{{width:100%;max-width:400px}}
.lp-dm-row{{display:flex;justify-content:flex-end;margin-bottom:1rem}}
.lp-badge{{display:inline-flex;align-items:center;gap:6px;
           background:rgba(237,28,36,.1);border:1px solid rgba(237,28,36,.25);
           border-radius:20px;padding:4px 14px;font-size:.7rem;font-weight:600;
           color:#ED1C24;letter-spacing:.4px;margin-bottom:.8rem}}
.lp-form-title{{font-size:1.75rem;font-weight:800;color:{t1};
                letter-spacing:-.4px;margin:0 0 .3rem 0}}
.lp-form-sub{{font-size:.83rem;color:{t2};margin:0 0 1.2rem 0;line-height:1.5}}
.lp-lbl{{font-size:.7rem;font-weight:600;color:{t2};letter-spacing:.7px;
         text-transform:uppercase;margin-bottom:.3rem;margin-top:.1rem}}
.lp-divider{{height:1px;background:linear-gradient(90deg,transparent,{brd},transparent);
             margin:1.5rem 0;width:100%}}
.lp-footer-txt{{font-size:.72rem;color:{t2};text-align:center;line-height:1.6}}
.lp-footer-txt a{{color:#ED1C24;text-decoration:none;font-weight:500}}

/* ── inputs ── */
[data-testid="stColumn"]:last-child .stTextInput>div>div>input,
[data-testid="column"]:last-child .stTextInput>div>div>input{{
    background:{ib}!important;border:1.5px solid {ibr}!important;
    border-radius:10px!important;color:{it}!important;
    font-size:.9rem!important;padding:.65rem 1rem!important;height:auto!important;
    transition:border-color .2s ease,box-shadow .2s ease!important
}}
[data-testid="stColumn"]:last-child .stTextInput>div>div>input:focus,
[data-testid="column"]:last-child .stTextInput>div>div>input:focus{{
    border-color:#ED1C24!important;
    box-shadow:0 0 0 3px rgba(237,28,36,.12)!important;outline:none!important
}}
[data-testid="stColumn"]:last-child [data-testid="stWidgetLabel"],
[data-testid="stColumn"]:last-child [data-testid="InputInstructions"],
[data-testid="column"]:last-child [data-testid="stWidgetLabel"],
[data-testid="column"]:last-child [data-testid="InputInstructions"]{{
    display:none!important
}}

/* ── submit button ── */
[data-testid="stColumn"]:last-child [data-testid="stFormSubmitButton"]>button,
[data-testid="column"]:last-child [data-testid="stFormSubmitButton"]>button{{
    background:#ED1C24!important;color:#fff!important;border:none!important;
    border-radius:10px!important;font-size:.92rem!important;font-weight:700!important;
    padding:.75rem 1.5rem!important;height:auto!important;width:100%!important;
    letter-spacing:.2px!important;transition:all .2s ease!important;
    box-shadow:0 4px 16px rgba(237,28,36,.28)!important;margin-top:.5rem!important
}}
[data-testid="stColumn"]:last-child [data-testid="stFormSubmitButton"]>button:hover,
[data-testid="column"]:last-child [data-testid="stFormSubmitButton"]>button:hover{{
    background:#C8161D!important;
    box-shadow:0 6px 24px rgba(237,28,36,.42)!important;
    transform:translateY(-1px)!important
}}
[data-testid="stColumn"]:last-child [data-testid="stFormSubmitButton"]>button:active,
[data-testid="column"]:last-child [data-testid="stFormSubmitButton"]>button:active{{
    transform:translateY(0)!important;box-shadow:none!important
}}

/* ── dm toggle button ── */
[data-testid="stColumn"]:last-child .stButton>button,
[data-testid="column"]:last-child .stButton>button{{
    background:transparent!important;border:1.5px solid {brd}!important;
    border-radius:20px!important;color:{t2}!important;
    font-size:.75rem!important;font-weight:500!important;
    padding:.3rem .9rem!important;height:auto!important;
    transition:all .15s ease!important
}}
[data-testid="stColumn"]:last-child .stButton>button:hover,
[data-testid="column"]:last-child .stButton>button:hover{{
    border-color:#ED1C24!important;color:#ED1C24!important;
    background:rgba(237,28,36,.04)!important;transform:none!important
}}

/* ── form / alert ── */
[data-testid="stColumn"]:last-child .stForm,
[data-testid="stColumn"]:last-child [data-testid="stForm"],
[data-testid="column"]:last-child .stForm,
[data-testid="column"]:last-child [data-testid="stForm"]{{
    background:transparent!important;border:none!important;padding:0!important
}}
[data-testid="stColumn"]:last-child [data-testid="stAlert"],
[data-testid="column"]:last-child [data-testid="stAlert"]{{
    border-radius:8px!important;font-size:.82rem!important;margin-top:.25rem!important
}}

/* ── password-change extras ── */
.pc-rcard{{width:100%;max-width:400px}}
.pc-badge{{display:inline-flex;align-items:center;gap:6px;
           background:rgba(241,196,15,.1);border:1px solid rgba(241,196,15,.24);
           border-radius:20px;padding:4px 14px;font-size:.7rem;font-weight:600;
           color:#F1C40F;letter-spacing:.4px;margin-bottom:1.6rem}}
.pc-info{{background:{'rgba(41,128,185,.08)' if dark else '#EEF6FF'};
          border:1px solid {'rgba(41,128,185,.22)' if dark else '#B8D4EE'};
          border-radius:8px;padding:.75rem 1rem;font-size:.78rem;
          color:{'#5DADE2' if dark else '#2C5F8A'};line-height:1.55;margin-bottom:1.4rem;width:100%}}

/* ── responsive ── */
@media(max-width:768px){{
    [data-testid="stColumn"]:first-child,
    [data-testid="column"]:first-child{{display:none!important}}
    [data-testid="stColumn"]:last-child>div,
    [data-testid="column"]:last-child>div{{padding:2rem 1.5rem!important}}
}}
</style>"""


def _left_panel_html() -> str:
    return """
    <div class="lp-brand-circle"></div>
    <div class="lp-logo-row">
        <div class="lp-dot-grid"><span></span><span></span><span></span><span></span></div>
        <span class="lp-logo-name">claro</span>
    </div>
    <div class="lp-heading">Produtividade<br>COP Rede</div>
    <div class="lp-tagsub">Análise e acompanhamento da equipe Regional Leste —<br>acesso seguro e individualizado.</div>
    <div class="lp-features">
        <div class="lp-feat-item"><div class="lp-feat-icon">📊</div>Dashboards de produtividade em tempo real</div>
        <div class="lp-feat-item"><div class="lp-feat-icon">⚡</div>ETIT, TOA, DPA e Indicadores Residencial</div>
        <div class="lp-feat-item"><div class="lp-feat-icon">🔒</div>Acesso individualizado por matrícula</div>
    </div>
    <div class="lp-brand-footer">CNPJ da Empresa Nelson Soares · 66.955.143/0001-65</div>"""


def show_login_page() -> None:
    """Exibe a tela de login split-screen. Ao autenticar, define session_state e chama st.rerun()."""
    dark = st.session_state.get("dark_mode", False)
    err  = st.session_state.pop("_lp_err", False)
    dm_icon, dm_label = ("☀️", "Modo claro") if dark else ("🌙", "Modo escuro")

    st.markdown(_login_css(dark), unsafe_allow_html=True)

    col_l, col_r = st.columns([44, 56], gap="small")

    # ── Lado esquerdo — branding ──────────────────────────────────────────────
    with col_l:
        st.markdown(_left_panel_html(), unsafe_allow_html=True)

    # ── Lado direito — formulário ─────────────────────────────────────────────
    with col_r:
        st.markdown('<div class="lp-rcard">', unsafe_allow_html=True)

        # Toggle de tema
        st.markdown('<div class="lp-dm-row">', unsafe_allow_html=True)
        if st.button(f"{dm_icon} {dm_label}", key="_lp_dm"):
            st.session_state["dark_mode"] = not dark
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Cabeçalho
        st.markdown(
            '<div class="lp-badge">🔐 &nbsp;Área Restrita</div>'
            '<div class="lp-form-title">Bem-vindo de volta</div>'
            '<div class="lp-form-sub">Informe sua matrícula e senha para continuar</div>',
            unsafe_allow_html=True,
        )

        # Formulário
        with st.form("_auth_login_form", clear_on_submit=False):
            st.markdown('<div class="lp-lbl">Matrícula</div>', unsafe_allow_html=True)
            username = st.text_input("_mat", label_visibility="collapsed",
                                     placeholder="Ex: N6088107")

            st.markdown('<div class="lp-lbl" style="margin-top:.6rem">Senha</div>',
                        unsafe_allow_html=True)
            password = st.text_input("_pwd", label_visibility="collapsed",
                                     type="password", placeholder="••••••••")

            if err:
                st.error("Matrícula ou senha incorretos. Verifique e tente novamente.")

            submitted = st.form_submit_button("Entrar →", use_container_width=True,
                                              type="primary")

        # Rodapé
        st.markdown(
            '<div class="lp-divider"></div>'
            '<div class="lp-footer-txt">Problemas para acessar? Fale com o administrador.<br>'
            'Primeiro acesso · use a senha padrão e crie a sua.</div>',
            unsafe_allow_html=True,
        )

        st.markdown('</div>', unsafe_allow_html=True)  # lp-rcard

    # ── Lógica de autenticação ────────────────────────────────────────────────
    if submitted:
        if not username.strip() or not password:
            st.session_state["_lp_err"] = True
            st.rerun()
        else:
            valid, must_change = verify_login(username, password)
            if valid:
                st.session_state["authenticated"] = True
                st.session_state["user_matricula"] = username.strip().upper()
                st.session_state["must_change_password"] = must_change
                st.rerun()
            else:
                st.session_state["_lp_err"] = True
                st.rerun()


def show_change_password_page(username: str) -> None:
    """Exibe tela de troca obrigatória de senha no primeiro acesso."""
    dark = st.session_state.get("dark_mode", False)

    st.markdown(_login_css(dark), unsafe_allow_html=True)

    col_l, col_r = st.columns([44, 56], gap="small")

    with col_l:
        st.markdown(_left_panel_html(), unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="pc-rcard">', unsafe_allow_html=True)

        st.markdown(
            f'<div class="pc-badge">🔑 &nbsp;Primeiro acesso · {username}</div>'
            '<div class="lp-form-title">Crie sua senha</div>'
            '<div class="lp-form-sub">Defina uma senha pessoal para continuar</div>'
            '<div class="pc-info">Use <strong>pelo menos 6 caracteres</strong> e escolha '
            'algo diferente da senha padrão inicial.</div>',
            unsafe_allow_html=True,
        )

        with st.form("_auth_change_pwd_form"):
            st.markdown('<div class="lp-lbl">Nova senha</div>', unsafe_allow_html=True)
            new_pass = st.text_input("_np", label_visibility="collapsed",
                                     type="password", placeholder="Mínimo 6 caracteres")

            st.markdown('<div class="lp-lbl" style="margin-top:.6rem">Confirmar senha</div>',
                        unsafe_allow_html=True)
            confirm = st.text_input("_cp", label_visibility="collapsed",
                                    type="password", placeholder="Repita a senha")

            submitted = st.form_submit_button("Salvar e entrar →", use_container_width=True,
                                              type="primary")

        st.markdown(
            '<div class="lp-divider"></div>'
            '<div class="lp-footer-txt">Sua senha é armazenada de forma segura e criptografada.</div>',
            unsafe_allow_html=True,
        )

        st.markdown('</div>', unsafe_allow_html=True)  # pc-rcard

    if submitted:
        if not new_pass or not confirm:
            st.error("Preencha todos os campos.")
        elif len(new_pass) < 6:
            st.error("A senha deve ter pelo menos 6 caracteres.")
        elif new_pass != confirm:
            st.error("As senhas não coincidem. Tente novamente.")
        elif new_pass == DEFAULT_PASSWORD:
            st.error("A nova senha não pode ser igual à senha padrão inicial.")
        else:
            change_password(username, new_pass)
            st.session_state["must_change_password"] = False
            st.session_state["_flash_success"] = "Senha definida com sucesso!"
            st.rerun()
