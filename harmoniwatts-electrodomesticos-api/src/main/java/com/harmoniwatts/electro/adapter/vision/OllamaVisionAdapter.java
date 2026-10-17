package com.harmoniwatts.electro.adapter.vision;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.harmoniwatts.electro.config.VisionProperties;
import com.harmoniwatts.electro.domain.vision.VisionRawResult;
import java.time.Duration;
import java.util.Base64;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

/**
 * Ollama local (opcional). Solo se registra si {@code harmoniwatts.vision.ollama.enabled=true}.
 * No forma parte del stack Docker por defecto.
 */
@Component
@ConditionalOnProperty(name = "harmoniwatts.vision.ollama.enabled", havingValue = "true")
public class OllamaVisionAdapter implements VisionProviderAdapter {

  private static final Logger log = LoggerFactory.getLogger(OllamaVisionAdapter.class);
  private static final ObjectMapper MAPPER = new ObjectMapper();

  private final VisionProperties properties;
  private final RestClient restClient;

  public OllamaVisionAdapter(VisionProperties properties) {
    this.properties = properties;
    String baseUrl = properties.getOllama().getBaseUrl().replaceAll("/$", "");
    var requestFactory = new org.springframework.http.client.SimpleClientHttpRequestFactory();
    requestFactory.setConnectTimeout(Duration.ofSeconds(15));
    requestFactory.setReadTimeout(Duration.ofSeconds(properties.getOllama().getTimeoutSeconds()));
    this.restClient = RestClient.builder().baseUrl(baseUrl).requestFactory(requestFactory).build();
  }

  @Override
  public String providerId() {
    return "ollama";
  }

  @Override
  public boolean isConfigured() {
    return restClient != null;
  }

  @Override
  public VisionRawResult analyze(
      byte[] imageBytes, String mimeType, List<String> tipoCodigos, List<String> marcaNombres) {
    String prompt =
        isMoondream(properties.getOllama().getModel())
            ? VisionPromptSupport.buildMoondreamPrompt()
            : VisionPromptSupport.buildPrompt(tipoCodigos, marcaNombres);
    log.info(
        "Llamando Ollama modelo={} imagenBytes={} mimeType={}",
        properties.getOllama().getModel(),
        imageBytes.length,
        mimeType);

    String base64 = Base64.getEncoder().encodeToString(imageBytes);

    ObjectNode body = MAPPER.createObjectNode();
    body.put("model", properties.getOllama().getModel());
    body.put("stream", false);
    if (!isMoondream(properties.getOllama().getModel())) {
      body.put("format", "json");
    }

    ObjectNode message = MAPPER.createObjectNode();
    message.put("role", "user");
    message.put("content", prompt);
    ArrayNode images = MAPPER.createArrayNode();
    images.add(base64);
    message.set("images", images);

    ArrayNode messages = MAPPER.createArrayNode();
    messages.add(message);
    body.set("messages", messages);

    try {
      String responseBody =
          restClient
              .post()
              .uri("/api/chat")
              .contentType(MediaType.APPLICATION_JSON)
              .body(body.toString())
              .retrieve()
              .body(String.class);

      JsonNode root = MAPPER.readTree(responseBody);
      String content = root.path("message").path("content").asText(null);
      if (content == null || content.isBlank()) {
        throw new VisionAdapterException(VisionClientMessages.EMPTY_RESPONSE);
      }
      log.info(
          "Respuesta cruda Ollama (modelo={}): {}",
          properties.getOllama().getModel(),
          VisionPromptSupport.truncateForLog(content));
      return VisionPromptSupport.parseResponse(content, tipoCodigos);
    } catch (VisionAdapterException e) {
      throw e;
    } catch (RestClientResponseException e) {
      log.warn("Error HTTP Ollama {}: {}", e.getStatusCode().value(), e.getResponseBodyAsString());
      throw new VisionAdapterException(VisionClientMessages.ANALYSIS_FAILED, e);
    } catch (Exception e) {
      log.error("Error conectando con Ollama en {}", properties.getOllama().getBaseUrl(), e);
      throw new VisionAdapterException(VisionClientMessages.ANALYSIS_FAILED, e);
    }
  }

  private static boolean isMoondream(String model) {
    return model != null && model.toLowerCase().contains("moondream");
  }
}
