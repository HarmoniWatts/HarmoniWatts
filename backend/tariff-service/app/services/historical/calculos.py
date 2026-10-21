# app/services/historical/calculos.py
"""Funciones puras de cálculo del módulo histórico (sin acceso a la base de datos)."""

from typing import Any, Dict, Iterable, List, Optional, Tuple

Periodo = Tuple[int, int]  # (anio, mes)


def mayus(valor: Optional[str]) -> Optional[str]:
    """Normaliza códigos de entrada ('cali ' -> 'CALI'); None se conserva."""
    return valor.strip().upper() if valor and valor.strip() else None


def a_float(valor) -> Optional[float]:
    return None if valor is None else float(valor)


def redondear(valor, decimales: int = 2) -> Optional[float]:
    return None if valor is None else round(float(valor), decimales)


def diferencia(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """b - a, o None si falta alguno."""
    if a is None or b is None:
        return None
    return round(float(b) - float(a), 2)


def porcentaje(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """
    Variación porcentual de a hacia b: (b - a) / a * 100.
    None si falta algún valor o si a es 0 (evita dividir entre cero).
    """
    if a is None or b is None or float(a) == 0:
        return None
    return round((float(b) - float(a)) / float(a) * 100, 2)


def variacion(a: Optional[float], b: Optional[float]) -> Dict[str, Any]:
    """Estructura estándar de variación entre dos valores."""
    return {
        "a": redondear(a),
        "b": redondear(b),
        "diferencia": diferencia(a, b),
        "porcentaje": porcentaje(a, b),
    }


def promedio(valores: Iterable[Optional[float]]) -> Optional[float]:
    lista = [float(v) for v in valores if v is not None]
    return sum(lista) / len(lista) if lista else None


def indice_mes(anio: int, mes: int) -> int:
    """Número de mes consecutivo (permite restar períodos y detectar huecos)."""
    return anio * 12 + (mes - 1)


def periodo_desde_indice(indice: int) -> Periodo:
    return indice // 12, indice % 12 + 1


def meses_entre(desde: Periodo, hasta: Periodo) -> List[Periodo]:
    """Todos los meses entre dos períodos, ambos incluidos."""
    return [
        periodo_desde_indice(i)
        for i in range(indice_mes(*desde), indice_mes(*hasta) + 1)
    ]