"""Filtro de entrada determinista (0 tokens): emergencias y temas que requieren un profesional."""
import re

from .textutil import strip_accents

_PATTERNS = {
    "emergencia": r"emergenc|urgenc|ambulancia|incendio|sismo|temblor|balacera|disparos|"
                  r"suicid|me quiero (morir|matar)|quiero morir|autolesi|me estoy desangrando|infarto|desmay|"
                  r"me estan (golpeando|atacando|amenazando)",
    "salud": r"medicament|dosis|sintoma|diagnostic|enfermedad|dolor de|receta medica|embaraz|infeccion|"
             r"que me tomo|que puedo tomar",
    # En este asistente los temas jurídicos generales SÍ se responden con el catálogo; solo se deriva la estrategia de un caso concreto.
    "legal": r"amparo|demandar|demanda legal|que me conviene|como gano|me van a (dejar|meter|soltar)|voy a salir libre|"
             r"cuanto me van a dar|cuantos anos me|que pena me|me van a sentenciar|apelar|apelacion",
    "psico": r"ansiedad|depresion|ataque de panico|crisis nerviosa|me siento muy mal|terapia",
}
_COMPILED = {k: re.compile(v) for k, v in _PATTERNS.items()}

MENSAJES = {
    "salud": "No puedo dar orientación médica. Para temas de salud acuda a una institución de salud o a un profesional. "
             "En una urgencia llame al 911.",
    "legal": "No puedo valorar casos concretos ni anticipar resoluciones judiciales. Consulte a su defensor (público o particular) "
             "o a su asesor jurídico; si no cuenta con uno, tiene derecho a que se le asigne un defensor público gratuito.",
    "psico": "No puedo dar orientación psicológica. Hay personas que pueden acompañarle; "
             "acuda a un profesional de la salud mental. Si está en riesgo, llame al 911.",
}


def classify(texto: str) -> str | None:
    t = strip_accents(texto.lower())
    for tipo in ("emergencia", "salud", "psico", "legal"):
        if _COMPILED[tipo].search(t):
            return tipo
    return None
