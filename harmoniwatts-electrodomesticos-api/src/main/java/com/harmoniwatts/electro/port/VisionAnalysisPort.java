package com.harmoniwatts.electro.port;

import com.harmoniwatts.electro.domain.vision.VisionRawResult;

/** Puerto de salida: análisis de imagen con cadena de providers en la nube (o uno solo). */
public interface VisionAnalysisPort {

  /**
   * Analiza una imagen JPEG/PNG y devuelve extracción estructurada sin validar catálogo.
   *
   * @param imageBytes bytes de imagen ya preprocesados (resize)
   * @param mimeType   p. ej. image/jpeg
   * @param tipoCodigos códigos de tipo válidos del catálogo (para el prompt)
   * @param marcaNombres nombres de marca válidos del catálogo
   */
  VisionRawResult analyze(
      byte[] imageBytes, String mimeType, java.util.List<String> tipoCodigos, java.util.List<String> marcaNombres);
}
