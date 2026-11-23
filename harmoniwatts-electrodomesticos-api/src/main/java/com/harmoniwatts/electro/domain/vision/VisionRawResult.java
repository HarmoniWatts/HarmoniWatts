package com.harmoniwatts.electro.domain.vision;

/** Salida cruda del modelo de visión (antes de cruce con catálogo). */
public record VisionRawResult(
    String marcaDetectada,
    String modeloDetectado,
    String tipoSugerido,
    /** Potencia nominal en W leída de la placa/etiqueta; null si no aparece. */
    Double potenciaW,
    /** Consumo mensual en kWh leído de la etiqueta energética (RETIQ); null si no aparece. */
    Double consumoKwhMes,
    double confianza,
    String fuenteConsumo) {}
