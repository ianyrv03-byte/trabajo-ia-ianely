"""Interfaz Gradio de «Medidas Cautelares del Estado de Sonora»: chat formal con la identidad del Gobierno de Sonora.

Paleta tomada del portal https://seguridad.sonora.gob.mx/ (Secretaría de Seguridad y Protección Ciudadana):
guinda #6E0A3D / #610936 · vino #410324 · magenta #960E53 · naranja #DC7F37 · dorado #947043 · blanco #FFFFFF.
Neutros derivados: fondo #F7F5F2, superficie #FFFFFF, línea #E4DCD3, texto #2B2326, texto secundario #6B5E63.
Contraste (WCAG 2.1): texto #2B2326 sobre blanco ≈14:1 · blanco sobre #6E0A3D ≈11:1 · #6B5E63 sobre #F7F5F2 ≈5.9:1 ·
icono blanco sobre dorado #947043 ≈4.6:1 · enlaces #960E53 sobre blanco ≈8:1.
Se fuerza el tema claro también cuando el sistema está en modo oscuro: la identidad institucional es clara.
"""
from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Callable

import gradio as gr

from .config import BASE, settings

log = logging.getLogger("medidascautelares")

GUINDA, GUINDA2, VINO, MAGENTA = "#6E0A3D", "#610936", "#410324", "#960E53"
NARANJA, DORADO, WHITE = "#DC7F37", "#947043", "#FFFFFF"
BG, SURFACE, SURFACE2, LINE = "#F7F5F2", "#FFFFFF", "#F4EFE9", "#E4DCD3"
INK, GRAY, LINK = "#2B2326", "#6B5E63", "#960E53"

APP_NOMBRE = "Medidas Cautelares del Estado de Sonora"
SALUDO = ("Bienvenida, bienvenido al asistente de **Medidas Cautelares del Estado de Sonora**. "
          "Escriba su pregunta sobre medidas cautelares, su supervisión o la suspensión condicional del proceso "
          "y le responderé con la información oficial disponible.")
LEGAL = ("Este asistente ofrece información general con base en el Código Nacional de Procedimientos Penales y la Ley de "
         "Ejecución de Sanciones Penales y Medidas de Seguridad del Estado de Sonora; no sustituye la asesoría de su defensa "
         "ni las resoluciones del Juez de Control. Sus preguntas se procesan con un servicio de inteligencia artificial de un "
         "tercero: no escriba datos personales, números de causa ni detalles de su caso. Existe un límite diario de consultas "
         "con IA por persona. En caso de emergencia llame al 911; denuncia anónima 089.")
MSG_RITMO = ("Está enviando consultas con mucha rapidez. Para que el servicio funcione adecuadamente para todas las personas, "
             "espere un minuto antes de continuar. Gracias por su comprensión.")
INFO_FALLBACK = "**MEDIDAS CAUTELARES DEL ESTADO DE SONORA**\nSecretaría de Seguridad y Protección Ciudadana"
N_EJEMPLOS = 4

HEAD = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
        f'<meta name="theme-color" content="{GUINDA2}">'
        '<meta name="description" content="Preguntas frecuentes sobre medidas cautelares en el Estado de Sonora.">')

# Ornamento escalonado del portal (naranja ascendente, magenta descendente), en SVG para que escale nítido.
_PASOS = "".join(
    f'<rect x="{i * 10}" y="{50 - i * 10}" width="8" height="8" fill="{NARANJA}"/>' for i in range(5)) + "".join(
    f'<rect x="{50 + i * 10}" y="{i * 10}" width="8" height="8" fill="{MAGENTA}"/>' for i in range(6))
ORNAMENTO = f'<svg class="orn" viewBox="0 0 108 58" aria-hidden="true" focusable="false">{_PASOS}</svg>'


def _both(d: dict) -> dict:
    """La paleta clara se aplica igual en claro y oscuro: si el navegador activara .dark, nada queda ilegible."""
    return {**d, **{k + "_dark": v for k, v in d.items()}}


THEME = gr.themes.Base(
    font=["Montserrat", "system-ui", "Segoe UI", "Helvetica Neue", "Arial", "sans-serif"],
    radius_size=gr.themes.sizes.radius_md,
).set(**_both({
    "body_background_fill": BG, "body_text_color": INK, "body_text_color_subdued": GRAY,
    "background_fill_primary": SURFACE, "background_fill_secondary": SURFACE2,
    "block_background_fill": "transparent", "block_border_color": "transparent", "block_border_width": "0px",
    "block_shadow": "none", "block_label_text_color": GRAY, "block_title_text_color": INK,
    "panel_background_fill": SURFACE, "border_color_primary": LINE,
    "input_background_fill": SURFACE, "input_border_color": LINE, "input_border_color_focus": GUINDA,
    "input_placeholder_color": GRAY,
    "button_primary_background_fill": GUINDA, "button_primary_background_fill_hover": VINO,
    "button_primary_text_color": WHITE, "button_primary_border_color": GUINDA,
    "button_secondary_background_fill": SURFACE, "button_secondary_background_fill_hover": SURFACE2,
    "button_secondary_text_color": INK, "button_secondary_border_color": LINE,
    "link_text_color": LINK, "color_accent_soft": SURFACE2,
}))

CSS = f"""
body, .gradio-container {{ background:{BG} !important; color:{INK}; }}
.gradio-container {{ max-width: 860px !important; margin: 0 auto !important; padding: 0 16px !important; overflow: visible !important; }}
/* Las franjas de encabezado y pie ocupan todo el ancho de la ventana sin provocar desplazamiento horizontal. */
html, body {{ overflow-x: hidden; }}
.gradio-container .main.fillable {{ padding-top:0 !important; padding-bottom:0 !important; }}
footer {{ display:none !important; }}

/* Franja institucional guinda, a todo el ancho, como el encabezado del portal. */
#top {{ align-items:center !important; flex-wrap:nowrap !important; gap:.75rem; position:relative;
  margin:0 calc(50% - 50vw) !important; padding:.85rem max(16px, calc(50vw - 414px)) !important; width:100vw;
  background:linear-gradient(100deg,{VINO} 0%,{GUINDA2} 45%,{GUINDA} 100%) !important; border-bottom:4px solid {DORADO}; }}
#brand {{ display:flex; align-items:center; gap:1rem; min-width:0; }}
#brand img {{ height:50px; width:auto; flex:0 0 auto; }}
#brand .sep {{ width:1px; align-self:stretch; background:rgba(255,255,255,.55); }}
#brand .t {{ display:flex; flex-direction:column; line-height:1.15; min-width:0; }}
#brand .t b {{ font-size:1.32rem; font-weight:800; letter-spacing:.04em; color:{WHITE}; text-transform:uppercase; }}
#brand .t span {{ font-size:.7rem; font-weight:600; letter-spacing:.06em; color:rgba(255,255,255,.88); text-transform:uppercase; }}
@media (max-width: 560px) {{ #brand {{ gap:.6rem; }} #brand img {{ height:30px; }} #brand .t b {{ font-size:.95rem; white-space:nowrap; }}
  #brand .t span {{ font-size:.55rem; letter-spacing:.03em; }} }}
@media (max-width: 380px) {{ #brand .t span {{ display:none; }} }}

#info-btn {{ flex:0 0 40px !important; min-width:40px !important; width:40px !important; height:40px; padding:0 !important;
  border-radius:50% !important; background:transparent !important; color:{WHITE} !important;
  border:1.5px solid rgba(255,255,255,.75) !important; font:italic 700 1.05rem Georgia, serif !important; }}
#info-btn:hover {{ background:rgba(255,255,255,.12) !important; }}
#info-panel {{ position:fixed; top:84px; right:14px; z-index:100; width:min(92vw,360px); padding:1.1rem 1.2rem !important;
  background:{SURFACE} !important; border:1px solid {LINE} !important; border-top:4px solid {GUINDA} !important; border-radius:10px;
  box-shadow:0 18px 50px rgba(65,3,36,.22); }}
#info-panel, #info-panel * {{ color:{INK}; font-size:.9rem; line-height:1.5; }}
#info-panel strong {{ color:{VINO}; }}
#info-panel a {{ color:{LINK}; font-weight:600; }}

#miga {{ font-size:.8rem; color:{GRAY}; padding:.9rem 0 .2rem; }}
#miga a {{ color:{GRAY}; text-decoration:none; }} #miga a:hover {{ color:{LINK}; text-decoration:underline; }}
#miga b {{ color:{INK}; font-weight:700; }}
#intro {{ text-align:center; padding:.6rem 0 .2rem; }}
#intro .orn {{ width:92px; height:auto; display:block; margin:0 auto .45rem; }}
#intro h1 {{ margin:0; font-size:1.55rem; font-weight:800; color:{VINO}; letter-spacing:.01em; }}
#intro p {{ margin:.3rem auto 0; max-width:560px; font-size:.92rem; color:{GRAY}; }}
#intro .bar {{ width:72px; height:3px; background:{DORADO}; margin:.75rem auto 0; border-radius:2px; }}

#chat {{ border:1px solid {LINE} !important; background:{SURFACE} !important; border-radius:12px !important;
  box-shadow:0 2px 10px rgba(65,3,36,.05) !important; }}
#chat .bubble-wrap {{ padding:18px 16px 18px 14px !important; scrollbar-width:thin; scrollbar-color:{DORADO} transparent; background:{SURFACE} !important; }}
#chat .bubble-wrap::-webkit-scrollbar {{ width:8px; }}
#chat .bubble-wrap::-webkit-scrollbar-track {{ background:transparent; }}
#chat .bubble-wrap::-webkit-scrollbar-thumb {{ background:{DORADO}; border-radius:8px; }}
#chat .icon-button-wrapper, #chat .icon-buttons {{ display:none !important; }}
#chat .message-buttons {{ display:none !important; }}

/* UN solo marco por mensaje (.message.bot / .message.user); el interior no lleva borde ni fondo para no duplicarlo. */
#chat .message.bot, #chat .message.user {{ padding:14px 20px !important; line-height:1.6; }}
@media (max-width: 560px) {{ #chat .message-row {{ max-width:100% !important; margin-left:0 !important; margin-right:0 !important; }}
  #chat .bubble-wrap {{ padding:12px 10px !important; }} #chat .message.bot, #chat .message.user {{ padding:12px 14px !important; }}
  #intro h1 {{ font-size:1.3rem; }} }}
#chat .message.bot {{ background:{SURFACE2} !important; border:1px solid {LINE} !important; border-left:4px solid {GUINDA} !important;
  border-radius:4px 14px 14px 14px !important; box-shadow:none !important; }}
#chat .message.user {{ background:{GUINDA} !important; border:0 !important;
  border-radius:14px 14px 4px 14px !important; box-shadow:none !important; }}
#chat [data-testid="bot"], #chat [data-testid="user"] {{ background:transparent !important; border:0 !important; box-shadow:none !important;
  padding:0 !important; margin:0 !important; border-radius:0 !important; }}
#chat .message-content {{ padding:0 !important; min-height:0 !important; }}
#chat .message.bot, #chat .message.bot * {{ color:{INK}; }}
#chat .message.bot strong {{ color:{VINO}; }}
#chat .message.user, #chat .message.user * {{ color:{WHITE} !important; }}
#chat .message p {{ margin:.35rem 0 !important; }}
#chat .message ul, #chat .message ol {{ margin:.35rem 0 !important; padding-left:1.2rem; }}
#chat a {{ color:{LINK} !important; font-weight:600; }}

#chips-t-wrap {{ flex:1 1 100% !important; min-width:100% !important; }}
#chips-t {{ font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:{DORADO}; padding-top:.4rem; }}
#chips {{ flex-wrap:wrap !important; gap:.5rem !important; }}
.chip {{ flex:0 1 auto !important; min-width:0 !important; border-radius:999px !important; background:{SURFACE} !important;
  border:1.5px solid {DORADO} !important; color:{VINO} !important; font-size:.86rem !important; font-weight:600 !important;
  padding:.45rem 1rem !important; }}
.chip:hover {{ background:{SURFACE2} !important; border-color:{GUINDA} !important; }}

#report-row {{ align-items:center !important; gap:.75rem; }}
#report-btn {{ flex:0 0 auto !important; border-radius:999px !important; background:{SURFACE} !important; color:{GUINDA} !important;
  border:1.5px solid {GUINDA} !important; font-size:.86rem !important; font-weight:600 !important; }}
#report-btn:hover {{ background:{SURFACE2} !important; }}
#report-note {{ font-size:.78rem; color:{GRAY}; }}

#msg {{ background:{SURFACE} !important; border:1.5px solid {LINE} !important; border-radius:28px !important;
  padding:.25rem .4rem .25rem 1rem !important; box-shadow:0 2px 8px rgba(65,3,36,.05) !important; }}
#msg {{ --input-border-color-focus: {GUINDA}; --input-shadow-focus: none; }}
#msg:focus-within {{ border-color:{GUINDA} !important; box-shadow:0 0 0 3px rgba(110,10,61,.12) !important; }}
#msg textarea:focus, #msg textarea:focus-visible {{ outline:none !important; box-shadow:none !important; border:0 !important; }}
#msg button:focus-visible {{ outline:2px solid {GUINDA} !important; outline-offset:2px; }}
#msg textarea {{ background:transparent !important; border:0 !important; box-shadow:none !important; color:{INK} !important; font-size:1rem; }}
#msg button {{ background:{DORADO} !important; color:{WHITE} !important; border:0 !important;
  border-radius:50% !important; min-width:42px; min-height:42px; }}
#msg button:hover {{ background:{GUINDA} !important; }}
#msg button svg {{ color:{WHITE} !important; fill:{WHITE} !important; stroke:{WHITE} !important; }}

#uso {{ font-size:.78rem; color:{GRAY}; text-align:center; }}
#uso p {{ color:{GRAY}; margin:.15rem 0; }}
/* Pie institucional en vino, a todo el ancho. */
#pie {{ margin:1rem calc(50% - 50vw) 0 !important; width:100vw; background:{VINO} !important; border-top:4px solid {DORADO};
  padding:1.1rem max(16px, calc(50vw - 414px)) .9rem !important; }}
#pie, #pie * {{ color:rgba(255,255,255,.86) !important; font-size:.76rem; line-height:1.55; text-align:center; }}
#pie p {{ margin:.2rem 0; }}
#pie a {{ color:{WHITE} !important; font-weight:600; }}
#pie .firma {{ font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:{WHITE} !important; font-size:.72rem; }}
#admin-link {{ text-align:center; font-size:.72rem; padding:.3rem 0 .2rem; }}
#admin-link a {{ color:rgba(255,255,255,.6) !important; text-decoration:none; }}
#admin-link a:hover {{ color:{WHITE} !important; text-decoration:underline; }}
button:focus-visible, textarea:focus-visible, a:focus-visible {{ outline:3px solid {DORADO} !important; outline-offset:2px; }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation:none !important; transition:none !important; }} }}
"""

JS = """() => {
  document.documentElement.lang = 'es-MX';
  document.body.classList.remove('dark');
  const label = (sel, text) => { const t = setInterval(() => { const e = document.querySelector(sel);
    if (e) { e.setAttribute('aria-label', text); clearInterval(t); } }, 300); setTimeout(() => clearInterval(t), 8000); };
  label('#info-btn', 'Información de contacto');
  label('#msg button', 'Enviar pregunta');
}"""

_MD = re.compile(r"([\\`*_{}\[\]<>()#+!|~])")


def esc(s: str) -> str:
    """Escapa caracteres de Markdown/HTML: el contenido del corpus se muestra como texto, nunca como formato."""
    return _MD.sub(r"\\\1", s or "")


def format_reply(d: dict) -> str:
    """Convierte la respuesta del servicio en Markdown seguro."""
    texto = re.sub(r"\s*\[\d+\]", "", d.get("respuesta", ""))  # marcadores de cita internos: no se muestran
    parts = [esc(texto).replace("\n", "  \n")]
    for a in d.get("advertencias", []):
        parts.append(f"**Aviso:** {esc(a)}")
    for f in d.get("fichas", []):
        head = f"**{esc(f['titulo'])}**" + (f" — {esc(f['puesto'])}" if f.get("puesto") else "")
        rows = [("Responsable", f.get("responsable")), ("Ubicación", f.get("ubicacion")), ("Horario", f.get("horario")),
                ("Teléfono", f.get("telefono")), ("Correo", f.get("correo")), ("Web", f.get("web")),
                ("Actualizado", f.get("actualizado"))]
        lines = [f"- **{k}:** {esc(v)}" for k, v in rows if v]
        if f.get("desactualizado"):
            lines.append("- **Aviso:** esta información puede estar desactualizada; confirma con la oficina.")
        parts.append(head + "\n" + "\n".join(lines))
    return "\n\n".join(parts)


def _parcial(texto: str) -> str:
    """Texto a medio escribir: sin marcadores de cita (completos o incompletos) y escapado."""
    return esc(re.sub(r"\s*\[[a-z0-9\-]*(\]|$)", "", texto))


def handle_stream(msg: str, history: list, cid: str, ip: str, service, previo: str | None = None):
    """Lógica del chat como generador (se prueba sin navegador).

    Emite tuplas (historial, texto de uso, pregunta sin respuesta, último tema, es_final). La pregunta del usuario
    aparece de inmediato y la respuesta se va escribiendo; la última tupla (es_final=True) trae la respuesta completa.
    """
    history = list(history or [])
    msg = " ".join((msg or "").split())[: settings.max_query_chars]
    if not msg:
        yield history, "", "", previo, True
        return
    base = history + [{"role": "user", "content": msg}]
    yield base, "", "", previo, False
    sin, uso, entrada = "", "", previo
    if not service.quota.rate_ok(ip, cid):
        reply = MSG_RITMO
    else:
        try:
            final = {}
            for kind, val in service.responder_stream(msg, "todos", ip, cid, previo):
                if kind == "parcial":
                    yield base + [{"role": "assistant", "content": _parcial(val)}], "", "", previo, False
                else:
                    final = val
            reply = format_reply(final)
            r = final.get("uso", {})
            uso = f"Consultas con IA restantes hoy: {r['consultas']}" if "consultas" in r else ""
            sin = msg if final.get("tipo") == "abstencion" else ""
            entrada = final.get("entrada_id") or previo
        except Exception:  # nunca mostrar un error técnico al usuario
            log.exception("error inesperado en el chat")
            reply = "Ocurrió un error. Inténtelo de nuevo en un momento."
    yield base + [{"role": "assistant", "content": reply}], uso, sin, entrada, True


def handle(msg: str, history: list, cid: str, ip: str, service, previo: str | None = None) -> tuple[list, str, str]:
    """Versión sin streaming: devuelve (historial, texto de uso, pregunta sin respuesta)."""
    ultimo = None
    for ultimo in handle_stream(msg, history, cid, ip, service, previo):
        pass
    return ultimo[0], ultimo[1], ultimo[2]


def client_ip(request) -> str:
    if request is None:
        return "?"
    xff = request.headers.get("x-forwarded-for", "") if request.headers else ""
    return (xff.split(",")[0].strip() if xff else (request.client.host if request.client else "?"))[:64]


def _info_md() -> str:
    p = BASE / "data" / "info_institucion.md"
    return p.read_text("utf-8") if p.exists() else INFO_FALLBACK


def build_ui(get_service: Callable[[], object]) -> gr.Blocks:
    with gr.Blocks(title=f"{APP_NOMBRE} · Gobierno del Estado de Sonora", analytics_enabled=False) as demo:
        with gr.Row(elem_id="top"):
            gr.HTML('<div id="brand"><img src="/static/logo_dark.png" alt="Gobierno del Estado de Sonora">'
                    '<span class="sep" aria-hidden="true"></span>'
                    '<div class="t"><b>Medidas Cautelares</b>'
                    '<span>Secretaría de Seguridad y Protección Ciudadana</span></div></div>')
            info_btn = gr.Button("i", elem_id="info-btn", scale=0)
        with gr.Column(visible=False, elem_id="info-panel") as info_panel:
            gr.Markdown(_info_md())

        gr.HTML('<nav id="miga" aria-label="Ruta de navegación">'
                '<a href="https://seguridad.sonora.gob.mx/" rel="noopener">Seguridad Pública</a> / '
                '<b>Medidas Cautelares</b></nav>'
                f'<div id="intro">{ORNAMENTO}<h1>Preguntas frecuentes</h1>'
                '<p>Medidas cautelares, supervisión y suspensión condicional del proceso en el Estado de Sonora.</p>'
                '<div class="bar"></div></div>')
        chat = gr.Chatbot(value=[{"role": "assistant", "content": SALUDO}], elem_id="chat", height="50vh",
                          show_label=False, label="Conversación", buttons=[])
        with gr.Row(elem_id="chips") as chips:
            gr.HTML('<div id="chips-t">Consultas frecuentes</div>', elem_id="chips-t-wrap")
            ejemplos = [gr.Button("", elem_classes="chip", visible=False, size="sm") for _ in range(N_EJEMPLOS)]
        with gr.Row(visible=False, elem_id="report-row") as report_row:
            report_btn = gr.Button("Informar que falta esta información", elem_id="report-btn", size="sm", scale=0)
            gr.Markdown("Solo se envía su pregunta, sin datos personales.", elem_id="report-note")
        msg = gr.Textbox(elem_id="msg", container=False, show_label=False, label="Su pregunta", lines=1, max_lines=4,
                         placeholder="Escriba su pregunta…", max_length=settings.max_query_chars, submit_btn=True,
                         autofocus=True)
        uso = gr.Markdown("", elem_id="uso")
        with gr.Column(elem_id="pie"):
            gr.Markdown(LEGAL, elem_id="legal")
            gr.HTML('<p class="firma">Gobierno del Estado de Sonora · Secretaría de Seguridad y Protección Ciudadana</p>'
                    '<p><a href="https://seguridad.sonora.gob.mx/" rel="noopener">seguridad.sonora.gob.mx</a></p>')
            if settings.show_admin_link:
                gr.HTML('<a href="/admin/">Administración</a>', elem_id="admin-link")

        cid_state = gr.BrowserState(None)  # id anónimo (solo para los cupos de uso); la conversación NO se guarda
        sin_state = gr.State("")
        prev_state = gr.State(None)  # último tema consultado en ESTA conversación (se pierde al recargar)
        open_state = gr.State(False)

        def on_send(text, history, cid, previo, request: gr.Request):
            cid = cid or uuid.uuid4().hex
            n0 = len(history or [])
            for h, u, sin, ent, final in handle_stream(text, history, cid, client_ip(request), get_service(), previo):
                oculta = gr.update(visible=False) if len(h) > n0 else gr.update()
                if final:
                    yield (h, "", u, cid, oculta, gr.update(visible=bool(sin)), sin, ent)
                else:
                    yield (h, "", gr.update(), cid, oculta, gr.update(), gr.update(), gr.update())

        ins = [msg, chat, cid_state, prev_state]
        outs = [chat, msg, uso, cid_state, chips, report_row, sin_state, prev_state]
        msg.submit(on_send, ins, outs, api_name=False, concurrency_limit=8)
        for b in ejemplos:  # el valor del botón es la pregunta modelo
            b.click(on_send, [b, chat, cid_state, prev_state], outs, api_name=False, concurrency_limit=8)

        def on_report(sin, history, cid, request: gr.Request):
            _ok, texto = get_service().reportar(sin, client_ip(request), cid or "anon")
            history = list(history or []) + [{"role": "assistant", "content": esc(texto)}]
            return history, gr.update(visible=False), ""

        report_btn.click(on_report, [sin_state, chat, cid_state], [chat, report_row, sin_state], api_name=False)

        def on_info(opened):
            return gr.update(visible=not opened), not opened, gr.update(value="✕" if not opened else "i")

        info_btn.click(on_info, [open_state], [info_panel, open_state, info_btn], api_name=False)

        def cargar_ejemplos():  # se ejecuta en cada visita: siempre una conversación nueva y ejemplos actualizados
            ej = get_service().ejemplos(N_EJEMPLOS)
            return [gr.update(value=ej[i], visible=True) if i < len(ej) else gr.update(visible=False)
                    for i in range(N_EJEMPLOS)]

        demo.load(cargar_ejemplos, None, ejemplos, api_name=False)
        demo.queue(max_size=32)
    return demo
