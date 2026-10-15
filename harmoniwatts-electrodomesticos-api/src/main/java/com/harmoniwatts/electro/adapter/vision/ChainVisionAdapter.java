package com.harmoniwatts.electro.adapter.vision;

import com.harmoniwatts.electro.config.VisionProperties;
import com.harmoniwatts.electro.domain.vision.VisionRawResult;
import com.harmoniwatts.electro.port.VisionAnalysisPort;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientResponseException;

/**
 * Orquesta Gemini → OpenAI → Mistral (orden configurable). Si un provider falla (cuota, 429,
 * red, etc.), prueba el siguiente configurado con API key.
 */
@Component
@Primary
public class ChainVisionAdapter implements VisionAnalysisPort {

  private static final Logger log = LoggerFactory.getLogger(ChainVisionAdapter.class);

  private final VisionProperties properties;
  private final Map<String, VisionProviderAdapter> byId;

  public ChainVisionAdapter(VisionProperties properties, List<VisionProviderAdapter> providers) {
    this.properties = properties;
    this.byId = new LinkedHashMap<>();
    for (VisionProviderAdapter p : providers) {
      byId.put(p.providerId().toLowerCase(Locale.ROOT), p);
    }
    log.info(
        "Visión: providers registrados={} | modo={} | chainOrder={}",
        byId.keySet(),
        properties.getProvider(),
        properties.getChainOrder());
  }

  @Override
  public VisionRawResult analyze(
      byte[] imageBytes, String mimeType, List<String> tipoCodigos, List<String> marcaNombres) {
    List<VisionProviderAdapter> sequence = resolveSequence();
    if (sequence.isEmpty()) {
      throw new VisionAdapterException(
          "Ningún provider de visión tiene API key. Configura GEMINI_API_KEY, OPENAI_API_KEY y/o MISTRAL_API_KEY.");
    }

    List<String> errors = new ArrayList<>();
    for (int i = 0; i < sequence.size(); i++) {
      VisionProviderAdapter provider = sequence.get(i);
      String id = provider.providerId();
      try {
        log.info("Visión cadena: intentando provider={} ({}/{})", id, i + 1, sequence.size());
        VisionRawResult result = provider.analyze(imageBytes, mimeType, tipoCodigos, marcaNombres);
        log.info("Visión cadena: OK con provider={}", id);
        return result;
      } catch (Exception e) {
        String detail = summarizeError(e);
        errors.add(id + ": " + detail);
        boolean hasNext = i < sequence.size() - 1;
        if (hasNext) {
          log.warn(
              "Visión cadena: falló provider={} ({}). Probando siguiente…", id, detail);
        } else {
          log.error(
              "Visión cadena: falló provider={} y no hay más alternativas. Errores: {}",
              id,
              String.join(" | ", errors));
        }
      }
    }

    throw new VisionAdapterException(VisionClientMessages.ANALYSIS_FAILED);
  }

  private List<VisionProviderAdapter> resolveSequence() {
    String mode = properties.getProvider() == null ? "chain" : properties.getProvider().trim().toLowerCase(Locale.ROOT);
    List<String> orderIds;
    if ("chain".equals(mode) || mode.isBlank()) {
      orderIds = parseOrder(properties.getChainOrder());
      if (orderIds.isEmpty()) {
        orderIds = List.of("gemini", "openai", "mistral");
      }
    } else {
      // Forzar un solo provider (sin failover)
      orderIds = List.of(mode);
    }

    List<VisionProviderAdapter> out = new ArrayList<>();
    for (String id : orderIds) {
      VisionProviderAdapter p = byId.get(id.toLowerCase(Locale.ROOT));
      if (p == null) {
        log.debug("Visión cadena: provider '{}' no registrado, se omite", id);
        continue;
      }
      if (!p.isConfigured()) {
        log.info("Visión cadena: provider={} sin API key, se omite", id);
        continue;
      }
      out.add(p);
    }
    return out;
  }

  private static List<String> parseOrder(String raw) {
    if (raw == null || raw.isBlank()) {
      return List.of();
    }
    return java.util.Arrays.stream(raw.split("[,\\s]+"))
        .map(String::trim)
        .filter(s -> !s.isEmpty())
        .map(s -> s.toLowerCase(Locale.ROOT))
        .collect(Collectors.toList());
  }

  private static String summarizeError(Exception e) {
    if (e instanceof RestClientResponseException http) {
      return "HTTP " + http.getStatusCode().value();
    }
    Throwable cause = e.getCause();
    if (cause instanceof RestClientResponseException http) {
      return "HTTP " + http.getStatusCode().value();
    }
    String msg = e.getMessage();
    if (msg == null || msg.isBlank()) {
      return e.getClass().getSimpleName();
    }
    return msg.length() > 160 ? msg.substring(0, 160) + "…" : msg;
  }
}
