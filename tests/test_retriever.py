import pytest

from app.service import Service


@pytest.fixture
def idx(cfg):
    return Service(cfg).index


@pytest.mark.parametrize("q,esperado", [
    ("¿Qué son las medidas cautelares?", "que-son-medidas-cautelares"),
    ("cada cuanto tengo que ir a firmar", "presentacion-periodica"),
    ("se me descargo el brazalete", "localizador-electronico"),
    ("como me regresan la fianza", "garantia-economica"),
    ("quien supervisa las medidas en sonora", "autoridad-supervision-sonora"),
    ("que es la umeca", "autoridad-supervision-sonora"),
    ("puedo salir de mi casa con arresto domiciliario", "resguardo-domiciliario"),
    ("no tengo abogado", "defensa-y-asesoria"),
    ("quiero que me quiten la medida", "revision-modificacion"),
    ("puedo hablar con mi expareja por whatsapp", "prohibicion-de-acercarse"),
    ("que es la prision preventiva oficiosa", "prision-preventiva"),
    ("diferencia entre medidas de proteccion y cautelares", "medidas-de-proteccion"),
])
def test_top1(idx, q, esperado):
    assert idx.search(q, "todos")[0].entry.id == esperado


def test_perfil_prioriza_audiencia(idx):
    vic = idx.search("derechos", "victima")
    assert vic[0].entry.id == "derechos-de-la-victima"


def test_sin_terminos_no_devuelve_nada(idx):
    assert idx.search("que de la el", "todos") == []


def test_fuera_de_alcance_baja_relevancia(cfg):
    s = Service(cfg)
    hits = s.index.search("cuanto cuesta un boleto de avion a Paris", "todos")
    assert not s._relevant(hits)
