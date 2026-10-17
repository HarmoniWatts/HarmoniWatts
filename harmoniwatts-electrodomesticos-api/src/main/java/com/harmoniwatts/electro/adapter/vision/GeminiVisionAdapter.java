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
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/** Google Gemini Flash (visión + OCR). */
@Component
public class GeminiVisionAdapter implements VisionProviderAdapter {

  private static final Logger log = LoggerFactory.getLogger(GeminiVisionAdapter.class);
  private static final ObjectMapper MAPPER = new ObjectMapper();

  private final VisionProperties properties;
  private final RestClient restClient;

  public GeminiVisionAdapter(VisionProperties properties) {
    this.properties = properties;
    String apiKey = properties.getGemini().getApiKey();
    if (apiKey == null || apiKey.isBlank()) {
      this.restClient = null;
      return;
    }
    String baseUrl = properties.getGemini().getBaseUrl().replaceAll("/$", "");
    var requestFactory = new org.springframework.http.client.SimpleClientHttpRequestFactory();
    requestFactory.setConnectTimeout(Duration.ofSeconds(15));
    requestFactory.setReadTimeout(Duration.ofSeconds(properties.getGemini().getTimeoutSeconds()));
    this.restClient =
        RestClient.builder()
            .baseUrl(baseUrl)
            .defaultHeader("x-goog-api-key", apiKey.trim())
            .requestFactory(requestFactory)
            .build();
  }

  @Override
  public String providerId() {
    return "gemini";
  }

  @Override
  public boolean isConfigured() {
    return restClient != null;
  }

  @Override
  public VisionRawResult analyze(
      byte[] imageBytes, String mimeType, List<String> tipoCodigos, List<String> marcaNombres) {
    if (!isConfigured()) {
      throw new VisionAdapterException("Gemini no está configurado (falta GEMINI_API_KEY)");
    }
    String prompt = VisionPromptSupport.buildPrompt(tipoCodigos, marcaNombres);
    String safeMime = mimeType != null && !mimeType.isBlank() ? mimeType : "image/jpeg";
    String base64 = Base64.getEncoder().encodeToString(imageBytes);
    String model = properties.getGemini().getModel();

    log.info("Llamando Gemini modelo={} imagenBytes={}", model, imageBytes.length);

    ObjectNode inlineData = MAPPER.createObjectNode();
    inlineData.put("mime_type", safeMime);
    inlineData.put("data", base64);

    ObjectNode imagePart = MAPPER.createObjectNode();
    imagePart.set("inline_data", inlineData);

    ObjectNode textPart = MAPPER.createObjectNode();
    textPart.put("text", prompt);

    ArrayNode parts = MAPPER.createArrayNode();
    parts.add(textPart);
    parts.add(imagePart);

    ObjectNode content = MAPPER.createObjectNode();
    content.set("parts", parts);

    ArrayNode contents = MAPPER.createArrayNode();
    contents.add(content);

    ObjectNode genConfig = MAPPER.createObjectNode();
    genConfig.put("responseMimeType", "application/json");
    genConfig.put("temperature", 0.2);

    ObjectNode body = MAPPER.createObjectNode();
    body.set("contents", contents);
    body.set("generationConfig", genConfig);

    try {
      String responseBody =
          restClient
              .post()
              .uri("/v1beta/models/{model}:generateContent", model)
              .contentType(MediaType.APPLICATION_JSON)
              .body(body.toString())
              .retrieve()
              .body(String.class);

      JsonNode root = MAPPER.readTree(responseBody);
      String contentText =
          root.path("candidates").path(0).path("content").path("parts").path(0).path("text").asText(null);
      if (contentText == null || contentText.isBlank()) {
        throw new VisionAdapterException(VisionClientMessages.ANALYSIS_FAILED);
      }
      log.info(
          "Respuesta cruda Gemini (modelo={}): {}",
          model,
          VisionPromptSupport.truncateForLog(contentText));
      return VisionPromptSupport.parseResponse(contentText, tipoCodigos);
    } catch (VisionAdapterException e) {
      throw e;
    } catch (Exception e) {
      log.error("Error al llamar a Gemini API", e);
      throw new VisionAdapterException(VisionClientMessages.ANALYSIS_FAILED, e);
    }
  }
}
