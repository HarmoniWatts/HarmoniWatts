package com.harmoniwatts.electro.adapter.vision;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.harmoniwatts.electro.domain.vision.VisionRawResult;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Utilidades compartidas para adaptadores de visión (prompt y parseo JSON). */
final class VisionPromptSupport {

  private static final Logger log = LoggerFactory.getLogger(VisionPromptSupport.class);
  private static final ObjectMapper MAPPER = new ObjectMapper();
  private static final int LOG_MAX_CHARS = 4000;

  private static final Pattern MARCA =
      Pattern.compile("\"marca_detectada\"\\s*:\\s*\"([^\"]*)\"", Pattern.CASE_INSENSITIVE);
  private static final Pattern MODELO =
      Pattern.compile("\"modelo_detectado\"\\s*:\\s*\"([^\"]*)\"", Pattern.CASE_INSENSITIVE);
  private static final Pattern TIPO =
      Pattern.compile("\"tipo_sugerido\"\\s*:\\s*\"([^\"]*)\"", Pattern.CASE_INSENSITIVE);
  private static final Pattern CONSUMO =
      Pattern.compile(
          "\"consumo_kwh_dia\"\\s*:\\s*([\\d.]+|null)", Pattern.CASE_INSENSITIVE);
  private static final Pattern CONFIANZA =
      Pattern.compile("\"confianza\"\\s*:\\s*([\\d.]+|null)", Pattern.CASE_INSENSITIVE);
  private static final Pattern FUENTE =
      Pattern.compile("\"fuente_consumo\"\\s*:\\s*\"([^\"]*)\"", Pattern.CASE_INSENSITIVE);

  private static final String ECHO_SAMSUNG_RT38K =
      "\"marca_detectada\":\"Samsung\",\"modelo_detectado\":\"RT38K\"";

  private VisionPromptSupport() {}

  static String buildPrompt(List<String> tipoCodigos, List<String> marcaNombres) {
    String tipos = String.join(", ", tipoCodigos);
    return """
        Observa la imagen adjunta (etiqueta RETIQ, etiqueta energética o frontal del electrodoméstico).
        Extrae marca, modelo, tipo y el consumo energético promedio DIARIO en kWh leyendo el texto visible.

        Unidades y conversión (obligatorio):
        - Si la etiqueta muestra kWh/mes (o kWh/month): consumo_kwh_dia = (kWh/mes) / 30.
        - Si ya muestra kWh/día (o kWh/day): usa ese valor en consumo_kwh_dia.
        - Si solo muestra potencia en W (watts) y NO indica horas de uso: deja consumo_kwh_dia en null
          (no inventes horas; el usuario calculará W × horas_día / 1000 en la app).
        - Si muestra W y también horas de uso: consumo_kwh_dia = (W × horas) / 1000.

        Devuelve un objeto JSON con: marca_detectada, modelo_detectado, tipo_sugerido,
        consumo_kwh_dia, confianza, fuente_consumo.
        tipo_sugerido debe ser uno de: %s
        fuente_consumo: etiqueta_kwh_mes | etiqueta_kwh_dia | etiqueta_w_con_horas | null
        Usa null si no puedes leer un campo. No inventes datos.
        """
        .formatted(tipos);
  }

  /** Prompt corto en líneas; Moondream responde mejor que con JSON. */
  static String buildMoondreamPrompt() {
    return """
        Extract the visible text from the image, numerical values, electrical variables; do not describe the image, just extract the characters within the image.
        """;
  }

  static VisionRawResult parseResponse(String raw, List<String> tipoCodigos) {
    if (raw == null || raw.isBlank()) {
      throw new VisionAdapterException(VisionClientMessages.EMPTY_RESPONSE);
    }
    if (isFieldNameEcho(raw)) {
      log.warn("Respuesta IA sin valores (solo nombres de campo): {}", truncate(raw));
      throw new VisionAdapterException(VisionClientMessages.ANALYSIS_FAILED);
    }
    if (raw.contains(ECHO_SAMSUNG_RT38K)) {
      log.warn("Respuesta IA detectada como eco Samsung/RT38K: {}", truncate(raw));
      throw new VisionAdapterException(VisionClientMessages.ECHO_EXAMPLE);
    }
    // Priorizar JSON: el fallback de texto libre no debe “ganar” sobre un JSON válido
    // (antes se perdían consumo_kwh_dia y confianza del modelo).
    if (looksLikeJson(raw)) {
      return parseJson(raw, tipoCodigos);
    }
    VisionRawResult structured = VisionTextFallback.parseFreeText(raw, tipoCodigos);
    log.info(
        "Texto/líneas parseadas: marca={}, modelo={}, tipo={}, kWh/día={}, confianza={}",
        structured.marcaDetectada(),
        structured.modeloDetectado(),
        structured.tipoSugerido(),
        structured.consumoKwhDiaEstimado(),
        structured.confianza());
    return structured;
  }

  private static boolean looksLikeJson(String raw) {
    String t = raw.trim();
    return t.startsWith("{")
        || t.contains("\"marca_detectada\"")
        || t.contains("\"consumo_kwh_dia\"")
        || t.contains("```json");
  }

  static VisionRawResult parseJson(String raw, List<String> tipoCodigos) {
    String json = sanitizeJson(extractJsonObject(raw.trim()));
    try {
      VisionRawResult parsed = fromJsonNode(MAPPER.readTree(json));
      log.info(
          "JSON parseado de visión IA: marca={}, modelo={}, tipo={}, kWh/día={}, confianza={}",
          parsed.marcaDetectada(),
          parsed.modeloDetectado(),
          parsed.tipoSugerido(),
          parsed.consumoKwhDiaEstimado(),
          parsed.confianza());
      return parsed;
    } catch (Exception first) {
      log.warn("Fallo parseo JSON, intentando regex. Respuesta cruda: {}", truncate(raw));
      try {
        return parseWithRegex(json);
      } catch (Exception second) {
        log.warn("Fallo regex, intentando texto libre. Respuesta cruda: {}", truncate(raw));
        try {
          return VisionTextFallback.parseFreeText(raw, tipoCodigos);
        } catch (Exception third) {
          log.error("No se interpretó la respuesta IA. Texto completo: {}", truncate(raw));
          throw new VisionAdapterException(VisionClientMessages.ANALYSIS_FAILED, first);
        }
      }
    }
  }

  static String truncateForLog(String raw) {
    return truncate(raw);
  }

  private static boolean isFieldNameEcho(String raw) {
    String t = raw.trim();
    if (t.contains("{") || t.contains("\"marca_detectada\"")) {
      return false;
    }
    boolean hasFieldNames =
        t.toLowerCase(Locale.ROOT).contains("marca_detectada")
            || t.toLowerCase(Locale.ROOT).contains("tipo_sugerido");
    if (!hasFieldNames) {
      return false;
    }
    // Valores reales suelen traer ":" con texto después (Marca: Electrolux)
    if (Pattern.compile(":\\s*\\S.{2,}", Pattern.CASE_INSENSITIVE).matcher(t).find()) {
      return false;
    }
    return true;
  }

  private static String truncate(String raw) {
    if (raw == null) {
      return "";
    }
    if (raw.length() <= LOG_MAX_CHARS) {
      return raw;
    }
    return raw.substring(0, LOG_MAX_CHARS) + "...[truncado]";
  }

  private static VisionRawResult fromJsonNode(JsonNode node) {
    String marca = textOrNull(node, "marca_detectada");
    String modelo = textOrNull(node, "modelo_detectado");
    String tipo = textOrNull(node, "tipo_sugerido");
    Double consumo = doubleOrNull(node, "consumo_kwh_dia");
    double confianza = doubleOrDefault(node, "confianza", 0.5);
    String fuente = textOrNull(node, "fuente_consumo");
    if (fuente == null) {
      fuente = textOrNull(node, "fuente_potencia");
    }
    if (fuente == null) {
      fuente = "inferencia";
    }
    return new VisionRawResult(marca, modelo, tipo, consumo, confianza, fuente);
  }

  private static VisionRawResult parseWithRegex(String json) {
    String marca = groupOrNull(MARCA, json);
    String modelo = groupOrNull(MODELO, json);
    String tipo = groupOrNull(TIPO, json);
    Double consumo = doubleGroupOrNull(CONSUMO, json);
    double confianza = doubleGroupOrDefault(CONFIANZA, json, 0.5);
    String fuente = groupOrNull(FUENTE, json);
    if (fuente == null) {
      fuente = "inferencia";
    }
    if (marca == null && modelo == null && tipo == null && consumo == null) {
      throw new VisionAdapterException("No se encontraron campos reconocibles en la respuesta");
    }
    return new VisionRawResult(marca, modelo, tipo, consumo, confianza, fuente);
  }

  /** Corrige JSON casi válido que suelen devolver modelos pequeños (0. , .82, etc.). */
  private static String sanitizeJson(String json) {
    String s = json;
    s = s.replaceAll("(\\d+)\\.(?=\\s*[,}\\]])", "$1");
    s = s.replaceAll(":\\s*\\.(\\d+)", ": 0.$1");
    s = s.replaceAll(",\\s*}", "}");
    s = s.replaceAll(",\\s*]", "]");
    return s;
  }

  private static String extractJsonObject(String text) {
    int start = text.indexOf('{');
    if (start < 0) {
      return text;
    }
    int depth = 0;
    boolean inString = false;
    boolean escaped = false;
    for (int i = start; i < text.length(); i++) {
      char c = text.charAt(i);
      if (inString) {
        if (escaped) {
          escaped = false;
        } else if (c == '\\') {
          escaped = true;
        } else if (c == '"') {
          inString = false;
        }
        continue;
      }
      if (c == '"') {
        inString = true;
      } else if (c == '{') {
        depth++;
      } else if (c == '}') {
        depth--;
        if (depth == 0) {
          return text.substring(start, i + 1);
        }
      }
    }
    int end = text.lastIndexOf('}');
    if (end > start) {
      return text.substring(start, end + 1);
    }
    return text;
  }

  private static String groupOrNull(Pattern pattern, String text) {
    Matcher m = pattern.matcher(text);
    if (!m.find()) {
      return null;
    }
    String v = m.group(1).trim();
    return v.isEmpty() ? null : v;
  }

  private static Integer intGroupOrNull(Pattern pattern, String text) {
    Matcher m = pattern.matcher(text);
    if (!m.find()) {
      return null;
    }
    String v = m.group(1).trim();
    if ("null".equalsIgnoreCase(v)) {
      return null;
    }
    return Integer.parseInt(v.replaceAll("[^0-9]", ""));
  }

  private static Double doubleGroupOrNull(Pattern pattern, String text) {
    Matcher m = pattern.matcher(text);
    if (!m.find()) {
      return null;
    }
    String v = m.group(1).trim();
    if ("null".equalsIgnoreCase(v) || v.isEmpty()) {
      return null;
    }
    if (v.startsWith(".")) {
      v = "0" + v;
    }
    if (v.endsWith(".")) {
      v = v.substring(0, v.length() - 1);
    }
    try {
      return Double.parseDouble(v);
    } catch (NumberFormatException e) {
      return null;
    }
  }

  private static double doubleGroupOrDefault(Pattern pattern, String text, double defaultValue) {
    Matcher m = pattern.matcher(text);
    if (!m.find()) {
      return defaultValue;
    }
    String v = m.group(1).trim();
    if ("null".equalsIgnoreCase(v) || v.isEmpty()) {
      return defaultValue;
    }
    if (v.startsWith(".")) {
      v = "0" + v;
    }
    if (v.endsWith(".")) {
      v = v.substring(0, v.length() - 1);
    }
    try {
      return Math.max(0, Math.min(1, Double.parseDouble(v)));
    } catch (NumberFormatException e) {
      return defaultValue;
    }
  }

  private static String textOrNull(JsonNode node, String field) {
    if (!node.has(field) || node.get(field).isNull()) {
      return null;
    }
    String v = node.get(field).asText().trim();
    return v.isEmpty() ? null : v;
  }

  private static Double doubleOrNull(JsonNode node, String field) {
    if (!node.has(field) || node.get(field).isNull()) {
      return null;
    }
    JsonNode n = node.get(field);
    if (n.isNumber()) {
      return n.asDouble();
    }
    String s = n.asText().trim();
    if ("null".equalsIgnoreCase(s) || s.isEmpty()) {
      return null;
    }
    if (s.startsWith(".")) {
      s = "0" + s;
    }
    if (s.endsWith(".")) {
      s = s.substring(0, s.length() - 1);
    }
    try {
      return Double.parseDouble(s.replace(',', '.'));
    } catch (NumberFormatException e) {
      return null;
    }
  }

  private static Integer intOrNull(JsonNode node, String field) {
    if (!node.has(field) || node.get(field).isNull()) {
      return null;
    }
    JsonNode n = node.get(field);
    if (n.isNumber()) {
      return n.asInt();
    }
    String s = n.asText().trim();
    if ("null".equalsIgnoreCase(s)) {
      return null;
    }
    s = s.replaceAll("[^0-9]", "");
    if (s.isEmpty()) {
      return null;
    }
    return Integer.parseInt(s);
  }

  private static double doubleOrDefault(JsonNode node, String field, double defaultValue) {
    if (!node.has(field) || node.get(field).isNull()) {
      return defaultValue;
    }
    JsonNode n = node.get(field);
    if (n.isNumber()) {
      return Math.max(0, Math.min(1, n.asDouble()));
    }
    String s = n.asText().trim();
    if (s.startsWith(".")) {
      s = "0" + s;
    }
    if (s.endsWith(".")) {
      s = s.substring(0, s.length() - 1);
    }
    try {
      return Math.max(0, Math.min(1, Double.parseDouble(s)));
    } catch (NumberFormatException e) {
      return defaultValue;
    }
  }
}
