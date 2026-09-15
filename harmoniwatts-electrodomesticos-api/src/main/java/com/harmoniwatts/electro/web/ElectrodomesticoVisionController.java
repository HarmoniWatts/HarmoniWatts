package com.harmoniwatts.electro.web;

import com.harmoniwatts.electro.adapter.vision.VisionAdapterException;
import com.harmoniwatts.electro.adapter.vision.VisionClientMessages;
import com.harmoniwatts.electro.service.ElectrodomesticoVisionService;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.VisionAnalysisResponse;
import java.io.IOException;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/electrodomesticos/vision")
public class ElectrodomesticoVisionController {

  private static final Logger log = LoggerFactory.getLogger(ElectrodomesticoVisionController.class);

  private final ElectrodomesticoVisionService visionService;

  public ElectrodomesticoVisionController(ElectrodomesticoVisionService visionService) {
    this.visionService = visionService;
  }

  /**
   * Analiza una foto de electrodoméstico y devuelve sugerencias para prellenar el formulario.
   * multipart field: {@code imagen}
   */
  @PostMapping(value = "/analizar", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
  public VisionAnalysisResponse analizar(@RequestParam("imagen") MultipartFile imagen) {
    if (imagen == null || imagen.isEmpty()) {
      throw new IllegalArgumentException("Debes enviar un archivo en el campo «imagen»");
    }
    String contentType = imagen.getContentType();
    if (contentType != null
        && !contentType.startsWith("image/")
        && !"application/octet-stream".equals(contentType)) {
      throw new IllegalArgumentException("Solo se admiten imágenes (JPEG, PNG, WebP)");
    }
    try {
      return visionService.analizarImagen(imagen.getBytes(), contentType);
    } catch (IOException e) {
      throw new IllegalArgumentException("No se pudo leer la imagen subida", e);
    }
  }

  @ExceptionHandler(IllegalArgumentException.class)
  ResponseEntity<Map<String, String>> badRequest(IllegalArgumentException ex) {
    return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", ex.getMessage()));
  }

  @ExceptionHandler(VisionAdapterException.class)
  ResponseEntity<Map<String, String>> visionError(VisionAdapterException ex) {
    log.warn("Análisis de imagen fallido: {}", ex.getMessage());
    return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
        .body(Map.of("error", VisionClientMessages.ANALYSIS_FAILED));
  }
}
