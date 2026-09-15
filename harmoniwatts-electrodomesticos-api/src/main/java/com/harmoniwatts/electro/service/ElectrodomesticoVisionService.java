package com.harmoniwatts.electro.service;

import com.harmoniwatts.electro.adapter.vision.VisionAdapterException;
import com.harmoniwatts.electro.config.VisionProperties;
import com.harmoniwatts.electro.domain.vision.VisionRawResult;
import com.harmoniwatts.electro.port.VisionAnalysisPort;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.MarcaCatalogoItem;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.TipoCatalogoItem;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.VisionAnalysisResponse;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Orquesta preproceso, inferencia IA y cruce con catálogos. */
@Service
public class ElectrodomesticoVisionService {

  private static final Logger log = LoggerFactory.getLogger(ElectrodomesticoVisionService.class);
  private static final String TIPO_OTRO = "OTRO";

  private final VisionAnalysisPort visionPort;
  private final ElectrodomesticoCatalogoService catalogoService;
  private final ImagePreprocessor imagePreprocessor;
  private final CatalogMatcher catalogMatcher;
  private final VisionProperties visionProperties;

  public ElectrodomesticoVisionService(
      VisionAnalysisPort visionPort,
      ElectrodomesticoCatalogoService catalogoService,
      ImagePreprocessor imagePreprocessor,
      CatalogMatcher catalogMatcher,
      VisionProperties visionProperties) {
    this.visionPort = visionPort;
    this.catalogoService = catalogoService;
    this.imagePreprocessor = imagePreprocessor;
    this.catalogMatcher = catalogMatcher;
    this.visionProperties = visionProperties;
  }

  @Transactional(readOnly = true)
  public VisionAnalysisResponse analizarImagen(byte[] imageBytes, String mimeType) {
    if (imageBytes == null || imageBytes.length == 0) {
      throw new IllegalArgumentException("La imagen está vacía");
    }
    if (imageBytes.length > 8 * 1024 * 1024) {
      throw new IllegalArgumentException("La imagen supera el límite de 8 MB");
    }

    var catalogos = catalogoService.listarActivos();
    List<TipoCatalogoItem> tipos = catalogos.tipos();
    List<MarcaCatalogoItem> marcas = catalogos.marcas();
    List<String> tipoCodigos = tipos.stream().map(TipoCatalogoItem::codigo).toList();
    List<String> marcaNombres = marcas.stream().map(MarcaCatalogoItem::nombre).toList();

    ImagePreprocessor.ProcessedImage processed = imagePreprocessor.preprocess(imageBytes, mimeType);
    log.info(
        "Visión IA: imagen original={} bytes, preprocesada={} bytes ({}x escala max {})",
        imageBytes.length,
        processed.bytes().length,
        mimeType,
        visionProperties.getMaxImageLongSide());

    VisionRawResult raw;
    try {
      raw =
          visionPort.analyze(
              processed.bytes(), processed.mimeType(), tipoCodigos, marcaNombres);
    } catch (VisionAdapterException e) {
      throw e;
    }

    log.info(
        "Visión IA cruda: marca={}, modelo={}, tipo={}, kWh/día={}, confianza={}, fuente={}",
        raw.marcaDetectada(),
        raw.modeloDetectado(),
        raw.tipoSugerido(),
        raw.consumoKwhDiaEstimado(),
        raw.confianza(),
        raw.fuenteConsumo());

    var tipoMatch = catalogMatcher.matchTipo(raw.tipoSugerido(), tipos);
    var marcaMatch = catalogMatcher.matchMarca(raw.marcaDetectada(), marcas);

    Integer idTipo = tipoMatch.map(TipoCatalogoItem::id).orElse(null);
    String tipoCodigo = tipoMatch.map(TipoCatalogoItem::codigo).orElse(raw.tipoSugerido());
    String tipoNombre = tipoMatch.map(TipoCatalogoItem::nombreEs).orElse(null);

    if (idTipo == null && tipos.stream().anyMatch(t -> TIPO_OTRO.equals(t.codigo()))) {
      var otro = tipos.stream().filter(t -> TIPO_OTRO.equals(t.codigo())).findFirst().orElse(null);
      if (otro != null) {
        idTipo = otro.id();
        tipoCodigo = otro.codigo();
        tipoNombre = otro.nombreEs();
      }
    }

    String nombreSugerido = null;
    if (TIPO_OTRO.equals(tipoCodigo)) {
      if (raw.modeloDetectado() != null && !raw.modeloDetectado().isBlank()) {
        nombreSugerido = raw.modeloDetectado().trim();
      } else if (raw.tipoSugerido() != null && !raw.tipoSugerido().isBlank()) {
        nombreSugerido = raw.tipoSugerido().trim();
      }
    }

    boolean bajaConfianza = raw.confianza() < visionProperties.getLowConfidenceThreshold();
    String advertencia = null;
    if (bajaConfianza) {
      advertencia =
          "La confianza del análisis es baja. Revisa marca, tipo y consumo (kWh/día) antes de guardar.";
    }
    if (raw.consumoKwhDiaEstimado() == null) {
      String hint =
          "No se pudo obtener kWh/día (p. ej. solo hay watts). Usa la calculadora: W × horas/día ÷ 1000.";
      advertencia = advertencia == null ? hint : advertencia + " " + hint;
    }

    log.info(
        "Visión IA mapeada a catálogo: idTipo={}, tipoCodigo={}, idMarca={}, marcaOtro={}, kWh/día={}",
        idTipo,
        tipoCodigo,
        marcaMatch.idMarcaPredefinida(),
        marcaMatch.marcaOtro(),
        raw.consumoKwhDiaEstimado());

    return new VisionAnalysisResponse(
        raw.marcaDetectada(),
        raw.modeloDetectado(),
        tipoCodigo,
        raw.consumoKwhDiaEstimado(),
        raw.confianza(),
        raw.fuenteConsumo(),
        idTipo,
        tipoNombre,
        marcaMatch.idMarcaPredefinida(),
        marcaMatch.marcaOtro(),
        nombreSugerido,
        bajaConfianza,
        advertencia);
  }
}
