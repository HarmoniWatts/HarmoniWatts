package com.harmoniwatts.electro.domain.vision;

/** Salida cruda del modelo de visión (antes de cruce con catálogo). */
public record VisionRawResult(
    String marcaDetectada,
    String modeloDetectado,
    String tipoSugerido,
    /** Consumo energético promedio diario en kWh; null si solo hay W sin horas de uso. */
    Double consumoKwhDiaEstimado,
    double confianza,
    String fuenteConsumo) {}
