# app/models/schemas/active_schemas.py

from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from typing import Optional, List


# =====================================================
# SCHEMAS BASE (reutilizables)
# =====================================================

class TarifaInfo(BaseModel):
    """Información básica de una tarifa."""
    model_config = ConfigDict(from_attributes=True)
    
    id_tarifa: int = Field(..., description="ID único de la tarifa")
    codigo_tarifa: str = Field(..., description="Código único de la tarifa")
    nombre_tarifa: Optional[str] = Field(None, description="Nombre descriptivo")
    cod_comercializadora: str = Field(..., description="Código de la comercializadora")
    cod_mercado: str = Field(..., description="Código del mercado")
    cod_nivel: str = Field(..., description="Código del nivel de tensión")
    cod_tipo_tarifa: Optional[str] = Field(None, description="Tipo de tarifa (A, B, C, D)")
    resolucion_regulatoria: Optional[str] = Field(None, description="Resolución regulatoria aplicable")


class PeriodoInfo(BaseModel):
    """Información del período tarifario vigente."""
    model_config = ConfigDict(from_attributes=True)
    
    id_periodo_tarifario: int
    anio: int = Field(..., description="Año del período")
    mes: int = Field(..., ge=1, le=12, description="Mes del período")
    fecha_inicio: date = Field(..., description="Fecha de inicio de vigencia")
    fecha_fin: date = Field(..., description="Fecha de fin de vigencia")
    numero_version: int = Field(..., description="Número de versión")
    estado: str = Field(..., description="Estado: BORRADOR, PUBLICADA, SUPERADA, ANULADA")
    fecha_publicacion: Optional[date] = Field(None, description="Fecha de publicación")
    
class MonomiaInfo(BaseModel):
    """Información de la monomía (tarifa sin franjas)."""
    valor: float = Field(..., description="Valor unitario de la monomía")
    unidad: str = Field(..., description="Unidad de medida (COP/kWh, etc.)")
    tipo: str = Field(..., description="Tipo de monomía (por ejemplo, 'CU')")


class ValorFranja(BaseModel):
    """Valor de una franja horaria."""
    hora: int = Field(None, ge=1, le=24, description="Hora del día (1-24)")
    codigo_franja: str = Field(None, description="Código de la franja (F1, F2, ...)")
    tipo_hora: Optional[str] = Field(None, description="Tipo de hora: PUNTA, LLANA, VALLE")
    valor: float = Field(None, ge=0, description="Valor en la unidad especificada")
    unidad: str = Field(None, description="Unidad de medida (COP/kWh, etc.)")


class ComponenteCU(BaseModel):
    """Componente del Costo Unitario."""
    cod_componente: str = Field(..., description="Código del componente (Gm, Tm, Dm, etc.)")
    valor: float = Field(..., description="Valor del componente")


class PrecioHora(BaseModel):
    """Precio de una hora específica."""
    hora: int = Field(..., ge=1, le=24, description="Hora (1=00:00-01:00, 24=23:00-24:00)")
    codigo_franja: Optional[str] = Field(None, description="Código de la franja aplicable")
    tipo_hora: Optional[str] = Field(None, description="Tipo: PUNTA, LLANA, VALLE")
    precio: Optional[float] = Field(None, ge=0, description="Precio unitario")
    unidad: Optional[str] = Field(None, description="Unidad de medida")


# =====================================================
# 1. TARIFA ACTIVA COMPLETA
# =====================================================

class TarifaActivaResponse(BaseModel):
    """
    Respuesta del endpoint GET /tariff/active/current/{id_cliente}
    
    Contiene la tarifa completa vigente del cliente:
    - Cabecera de la tarifa
    - Período tarifario vigente
    - Valores por franja horaria
    - Componentes del CU (G, T, D, Cv, PR, R)
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_cliente": 123,
                "fecha_consulta": "2024-01-15",
                "tarifa": {
                    "id_tarifa": 1,
                    "codigo_tarifa": "CALI-N1_1-A-202401",
                    "nombre_tarifa": "Tarifa CALI Nivel 1.1 Tipo A - Enero 2024",
                    "cod_comercializadora": "ENERTOTAL",
                    "cod_mercado": "CALI",
                    "cod_nivel": "N1_1",
                    "cod_tipo_tarifa": "A",
                    "resolucion_regulatoria": "CREG 119/2007"
                },
                "periodo": {
                    "id_periodo_tarifario": 1,
                    "anio": 2024,
                    "mes": 1,
                    "fecha_inicio": "2024-01-01",
                    "fecha_fin": "2024-01-31",
                    "numero_version": 1,
                    "estado": "PUBLICADA",
                    "fecha_publicacion": "2024-01-01"
                },
                "monomia": {
                    "valor": 874.09,
                    "unidad": "COP/kWh",
                    "tipo": "CU"
                },
                "valores": [
                    {"hora": 1, "codigo_franja": "F1", "tipo_hora": "VALLE", "valor": 874.09, "unidad": "COP/kWh"},
                    {"hora": 2, "codigo_franja": "F2", "tipo_hora": "VALLE", "valor": 888.56, "unidad": "COP/kWh"}
                ],
                "componentes": [
                    {"cod_componente": "Gm", "valor": 387.07},
                    {"cod_componente": "Tm", "valor": 54.32}
                ]
            }
        }
    )
    
    id_cliente: int = Field(..., description="ID del cliente consultado")
    fecha_consulta: date = Field(..., description="Fecha en que se realizó la consulta")
    tarifa: TarifaInfo = Field(..., description="Información de la tarifa")
    periodo: PeriodoInfo = Field(..., description="Período tarifario vigente")
    monomia: Optional[MonomiaInfo] = Field(None, description="Información de la monomía (si aplica)")
    valores: List[ValorFranja] = Field(default_factory=list, description="Valores por franja horaria")
    componentes: List[ComponenteCU] = Field(default_factory=list, description="Componentes del CU")


# =====================================================
# 2. PRECIOS DEL DÍA
# =====================================================

class PreciosDiaResponse(BaseModel):
    """
    Respuesta del endpoint GET /tariff/active/daily-bands/{id_cliente}
    
    Contiene la curva de precios de las 24 horas del día.
    Útil para el gráfico del dashboard con franjas de fondo.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_cliente": 123,
                "fecha": "2024-01-15",
                "precios": [
                    {"hora": 1, "codigo_franja": "F1", "tipo_hora": "VALLE", "precio": 752.15, "unidad": "COP/kWh"},
                    {"hora": 2, "codigo_franja": "F1", "tipo_hora": "VALLE", "precio": 752.15, "unidad": "COP/kWh"},
                    {"hora": 24, "codigo_franja": "F5", "tipo_hora": "VALLE", "precio": 771.51, "unidad": "COP/kWh"}
                ]
            }
        }
    )
    
    id_cliente: int = Field(..., description="ID del cliente")
    fecha: date = Field(..., description="Fecha de los precios")
    precios: List[PrecioHora] = Field(
        default_factory=list,
        description="Lista de precios por hora (24 elementos)"
    )


# =====================================================
# 3. FRANJA ACTUAL
# =====================================================

class FranjaActualResponse(BaseModel):
    """
    Respuesta del endpoint GET /tariff/active/current-franja/{id_cliente}
    
    Contiene la franja horaria vigente en el momento de la consulta.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_cliente": 123,
                "fecha": "2024-01-15",
                "hora_actual": 14,
                "codigo_franja": "F3",
                "tipo_hora": "PUNTA",
                "precio": 771.32,
                "unidad": "COP/kWh"
            }
        }
    )
    
    id_cliente: int = Field(..., description="ID del cliente")
    fecha: date = Field(..., description="Fecha de la consulta")
    hora_actual: int = Field(..., ge=1, le=24, description="Hora actual (1-24)")
    codigo_franja: Optional[str] = Field(None, description="Código de la franja actual")
    tipo_hora: Optional[str] = Field(None, description="Tipo de hora: PUNTA, LLANA, VALLE")
    precio: Optional[float] = Field(None, ge=0, description="Precio unitario de la franja actual")
    unidad: Optional[str] = Field(None, description="Unidad de medida (COP/kWh)")


# =====================================================
# 4. PRÓXIMA FRANJA ALTA
# =====================================================

class ProximaFranjaAltaResponse(BaseModel):
    """
    Respuesta del endpoint GET /tariff/active/high-franja/{id_cliente}
    
    Contiene la próxima ventana de alta tarifa detectada en el horizonte.
    
    Si no hay franja alta en el horizonte, `hay_franja_alta=False` y
    los campos de ventana son None.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Con franja alta detectada",
                    "value": {
                        "id_cliente": 123,
                        "fecha": "2024-01-15",
                        "hora_actual": 14,
                        "hay_franja_alta": True,
                        "codigo_franja": "F4",
                        "tipo_hora": "PUNTA",
                        "hora_inicio": 19,
                        "hora_fin": 21,
                        "duracion_horas": 3,
                        "precio_max": 899.04,
                        "precio_valle_referencia": 752.15,
                        "ahorro_potencial": 440.67,
                        "unidad": "COP/kWh",
                        "mensaje": "Franja de alta tarifa de 3 hora(s) desde las 19:00 hasta las 21:00. Ahorro potencial: 440.67 COP/kWh."
                    }
                },
                {
                    "summary": "Sin franja alta en el horizonte",
                    "value": {
                        "id_cliente": 123,
                        "fecha": "2024-01-15",
                        "hora_actual": 14,
                        "hay_franja_alta": False,
                        "mensaje": "No se detectó una franja de alta tarifa en el horizonte"
                    }
                }
            ]
        }
    )
    
    id_cliente: int = Field(..., description="ID del cliente")
    fecha: date = Field(..., description="Fecha de la consulta")
    hora_actual: int = Field(..., ge=1, le=24, description="Hora actual (1-24)")
    
    # Indicador de detección
    hay_franja_alta: bool = Field(
        ...,
        description="Indica si se detectó una ventana de alta tarifa"
    )
    
    # Datos de la ventana (solo si hay_franja_alta=True)
    codigo_franja: Optional[str] = Field(None, description="Código de la franja alta")
    tipo_hora: Optional[str] = Field(None, description="Tipo: PUNTA, LLANA, VALLE")
    hora_inicio: Optional[int] = Field(None, ge=1, le=24, description="Hora de inicio de la ventana")
    hora_fin: Optional[int] = Field(None, ge=1, le=24, description="Hora de fin de la ventana")
    duracion_horas: Optional[int] = Field(None, ge=1, le=24, description="Duración en horas")
    precio_max: Optional[float] = Field(None, ge=0, description="Precio máximo en la ventana")
    precio_valle_referencia: Optional[float] = Field(
        None, ge=0,
        description="Precio mínimo del día (referencia para calcular ahorro)"
    )
    ahorro_potencial: Optional[float] = Field(
        None, ge=0,
        description="Ahorro potencial estimado si se desplaza el consumo"
    )
    unidad: Optional[str] = Field(None, description="Unidad de medida")
    
    # Mensaje para el usuario
    mensaje: str = Field(
        ...,
        description="Mensaje descriptivo para mostrar al usuario"
    )