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

/** Mistral Pixtral (API en nube). */
@Component
public class MistralVisionAdapter implements VisionProviderAdapter {

  private static final Logger log = LoggerFactory.getLogger(MistralVisionAdapter.class);
  private static final ObjectMapper MAPPER = new ObjectMapper();

  private final VisionProperties properties;
  private final RestClient restClient;

  public MistralVisionAdapter(VisionProperties properties) {
    this.properties = properties;
    String apiKey = properties.getMistral().getApiKey();
    if (apiKey == null || apiKey.isBlank()) {
      this.restClient = null;
      return;
    }
    String baseUrl = properties.getMistral().getBaseUrl().replaceAll("/$", "");
    var requestFactory = new org.springframework.http.client.SimpleClientHttpRequestFactory();
    requestFactory.setConnectTimeout(Duration.ofSeconds(15));
    requestFactory.setReadTimeout(Duration.ofSeconds(properties.getMistral().getTimeoutSeconds()));
    this.restClient =
        RestClient.builder()
            .baseUrl(baseUrl)
            .defaultHeader("Authorization", "Bearer " + apiKey.trim())
            .requestFactory(requestFactory)
            .build();
  }

  @Override
  public String providerId() {
    return "mistral";
  }

  @Override
  public boolean isConfigured() {
    return restClient != null;
  }

  @Override
  public VisionRawResult analyze(
      byte[] imageBytes, String mimeType, List<String> tipoCodigos, List<String> marcaNombres) {
    if (!isConfigured()) {
      throw new VisionAdapterException("Mistral no está configurado (falta MISTRAL_API_KEY)");
    }
    String prompt = VisionPromptSupport.buildPrompt(tipoCodigos, marcaNombres);
    String safeMime = mimeType != null && !mimeType.isBlank() ? mimeType : "image/jpeg";
    String dataUrl =
        "data:" + safeMime + ";base64," + Base64.getEncoder().encodeToString(imageBytes);

    log.info(
        "Llamando Mistral modelo={} imagenBytes={}",
        properties.getMistral().getModel(),
        imageBytes.length);

    ObjectNode body = MAPPER.createObjectNode();
    body.put("model", properties.getMistral().getModel());

    ObjectNode message = MAPPER.createObjectNode();
    message.put("role", "user");

    ArrayNode content = MAPPER.createArrayNode();
    ObjectNode textPart = MAPPER.createObjectNode();
    textPart.put("type", "text");
    textPart.put("text", prompt);
    content.add(textPart);

    ObjectNode imagePart = MAPPER.createObjectNode();
    imagePart.put("type", "image_url");
    ObjectNode imageUrl = MAPPER.createObjectNode();
    imageUrl.put("url", dataUrl);
    imagePart.set("image_url", imageUrl);
    content.add(imagePart);

    message.set("content", content);

    ArrayNode messages = MAPPER.createArrayNode();
    messages.add(message);
    body.set("messages", messages);
    body.put("response_format", MAPPER.createObjectNode().put("type", "json_object"));

    try {
      String responseBody =
          restClient
              .post()
              .uri("/v1/chat/completions")
              .contentType(MediaType.APPLICATION_JSON)
              .body(body.toString())
              .retrieve()
              .body(String.class);

      JsonNode root = MAPPER.readTree(responseBody);
      String contentText =
          root.path("choices").path(0).path("message").path("content").asText(null);
      if (contentText == null) {
        throw new VisionAdapterException(VisionClientMessages.ANALYSIS_FAILED);
      }
      return VisionPromptSupport.parseResponse(contentText, tipoCodigos);
    } catch (VisionAdapterException e) {
      throw e;
    } catch (Exception e) {
      log.error("Error al llamar a Mistral API", e);
      throw new VisionAdapterException(VisionClientMessages.ANALYSIS_FAILED, e);
    }
  }
}
