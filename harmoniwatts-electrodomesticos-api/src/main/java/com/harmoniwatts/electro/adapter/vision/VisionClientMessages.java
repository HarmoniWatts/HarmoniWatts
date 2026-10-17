package com.harmoniwatts.electro.adapter.vision;

/** Mensajes orientados al usuario final (sin referencias a logs ni backend). */
public final class VisionClientMessages {

  public static final String ANALYSIS_FAILED =
      "No se pudo analizar la imagen. Intenta con una foto más clara del electrodoméstico o su etiqueta de potencia.";

  static final String EMPTY_RESPONSE = ANALYSIS_FAILED;

  static final String ECHO_EXAMPLE = ANALYSIS_FAILED;

  private VisionClientMessages() {}
}
