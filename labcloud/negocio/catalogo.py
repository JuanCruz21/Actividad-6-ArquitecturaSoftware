"""Catálogo de exámenes ofrecidos por el laboratorio."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Examen:
    clave: str
    nombre: str
    tipo_muestra: str
    reactivo: str
    unidad: str
    referencia: str


EXAMENES: dict[str, Examen] = {
    e.clave: e
    for e in [
        Examen("hemograma", "Hemograma (hemoglobina)", "Sangre total (EDTA)", "Reactivo hematología", "g/dL", "12.0 - 16.0"),
        Examen("glucosa", "Glucosa en ayunas", "Suero", "Reactivo glucosa", "mg/dL", "70 - 100"),
        Examen("colesterol", "Colesterol total", "Suero", "Reactivo colesterol", "mg/dL", "< 200"),
        Examen("creatinina", "Creatinina", "Suero", "Reactivo creatinina", "mg/dL", "0.6 - 1.2"),
        Examen("tsh", "TSH", "Suero", "Reactivo TSH", "µUI/mL", "0.4 - 4.0"),
        Examen("uroanalisis", "Uroanálisis", "Orina", "Tiras reactivas de orina", "", "Normal"),
    ]
}


def listar_examenes() -> list[dict]:
    return [asdict(e) for e in EXAMENES.values()]
