package com.harmoniwatts.electro.adapter.vision;

import com.harmoniwatts.electro.domain.vision.VisionRawResult;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Extrae campos desde texto libre cuando el modelo no devuelve JSON válido. */
final class VisionTextFallback {

  private static final Pattern MODELO =
      Pattern.compile("\\b([A-Z][A-Z0-9]{7,20})\\b");
  private static final Pattern KWH_MES =
      Pattern.compile(
          "(\\d+(?:[.,]\\d+)?)\\s*kWh\\s*/\\s*(mes|month|año|year)", Pattern.CASE_INSENSITIVE);
  private static final Pattern KWH_DIA =
      Pattern.compile(
          "(\\d+(?:[.,]\\d+)?)\\s*kWh\\s*/\\s*(día|dia|day)", Pattern.CASE_INSENSITIVE);
  private static final Pattern KWH_PLAIN =
      Pattern.compile("(\\d+(?:[.,]\\d+)?)\\s*kWh\\b", Pattern.CASE_INSENSITIVE);
  private static final Pattern LINE_FIELD =
      Pattern.compile(
          "^(Marca|Modelo|Tipo|ConsumoKwhDia|Consumo|PotenciaW|Potencia|Confianza)\\s*[:=]\\s*(.+)$",
          Pattern.CASE_INSENSITIVE | Pattern.MULTILINE);
  private static final Pattern MARCA_ES =
      Pattern.compile(
          "Marca\\s+(?:es\\s+)?[:=]?\\s*([A-Za-z0-9][A-Za-z0-9 &-]{1,30})",
          Pattern.CASE_INSENSITIVE);
  private static final Pattern MODELO_ES =
      Pattern.compile(
          "Modelo\\s+(?:es\\s+)?[:=]?\\s*([A-Z0-9][A-Z0-9-]{4,25})", Pattern.CASE_INSENSITIVE);

  private VisionTextFallback() {}

  static VisionRawResult parseFreeText(String text, List<String> tipoCodigos) {
    if (text == null || text.isBlank()) {
      throw new VisionAdapterException(VisionClientMessages.EMPTY_RESPONSE);
    }
    VisionRawResult structured = tryStructuredLines(text, tipoCodigos);
    if (structured != null) {
      return structured;
    }
    String upper = text.toUpperCase(Locale.ROOT);
    String marca = detectMarca(upper, text);
    String modelo = detectModelo(text);
    String tipo = detectTipo(upper, tipoCodigos);
    Double consumo = estimateConsumoKwhDia(text);
    if (marca == null && modelo == null && tipo == null && consumo == null) {
      throw new VisionAdapterException(VisionClientMessages.ANALYSIS_FAILED);
    }
    double confianza = (marca != null && modelo != null) ? 0.65 : 0.45;
    return new VisionRawResult(marca, modelo, tipo, consumo, confianza, "etiqueta_ocr");
  }

  private static VisionRawResult tryStructuredLines(String text, List<String> tipoCodigos) {
    String marca = null;
    String modelo = null;
    String tipo = null;
    Double consumo = null;
    Double confianza = null;
    String pendingKey = null;

    for (String rawLine : text.split("\\r?\\n")) {
      String line = rawLine.trim();
      if (line.isEmpty()) {
        continue;
      }
      Matcher inline = LINE_FIELD.matcher(line);
      if (inline.matches()) {
        pendingKey = inline.group(1).toLowerCase(Locale.ROOT);
        String value = cleanValue(inline.group(2));
        if (value != null) {
          marca = applyMarca(pendingKey, value, marca);
          modelo = applyModelo(pendingKey, value, modelo);
          tipo = applyTipo(pendingKey, value, tipoCodigos, tipo);
          consumo = applyConsumo(pendingKey, value, consumo);
          confianza = applyConfianza(pendingKey, value, confianza);
          pendingKey = null;
        }
        continue;
      }
      if (pendingKey != null) {
        String value = cleanValue(line);
        marca = applyMarca(pendingKey, value, marca);
        modelo = applyModelo(pendingKey, value, modelo);
        tipo = applyTipo(pendingKey, value, tipoCodigos, tipo);
        consumo = applyConsumo(pendingKey, value, consumo);
        confianza = applyConfianza(pendingKey, value, confianza);
        pendingKey = null;
      }
    }

    Matcher m = LINE_FIELD.matcher(text);
    while (m.find()) {
      String key = m.group(1).toLowerCase(Locale.ROOT);
      String value = cleanValue(m.group(2));
      if (value == null) {
        continue;
      }
      marca = applyMarca(key, value, marca);
      modelo = applyModelo(key, value, modelo);
      tipo = applyTipo(key, value, tipoCodigos, tipo);
      consumo = applyConsumo(key, value, consumo);
      confianza = applyConfianza(key, value, confianza);
    }
    if (marca == null) {
      Matcher marcaEs = MARCA_ES.matcher(text);
      if (marcaEs.find()) {
        marca = tidy(marcaEs.group(1));
      }
    }
    if (modelo == null) {
      Matcher modeloEs = MODELO_ES.matcher(text);
      if (modeloEs.find()) {
        modelo = modeloEs.group(1).trim();
      }
    }
    if (consumo == null) {
      consumo = estimateConsumoKwhDia(text);
    }
    if (marca == null && modelo == null && tipo == null && consumo == null) {
      return null;
    }
    double conf = confianza != null ? Math.max(0, Math.min(1, confianza)) : 0.55;
    return new VisionRawResult(marca, modelo, tipo, consumo, conf, "etiqueta_ocr");
  }

  private static String mapTipoToCodigo(String value, List<String> tipoCodigos) {
    String upper = value.toUpperCase(Locale.ROOT);
    if (upper.contains("LAVADORA")) {
      return pickCodigo(tipoCodigos, "LAVADORA");
    }
    if (upper.contains("NEVERA") || upper.contains("REFRIGERADOR")) {
      return pickCodigo(tipoCodigos, "NEVERA");
    }
    return detectTipo(upper, tipoCodigos);
  }

  private static String applyMarca(String key, String value, String current) {
    return "marca".equals(key) ? value : current;
  }

  private static String applyModelo(String key, String value, String current) {
    return "modelo".equals(key) ? value : current;
  }

  private static String applyTipo(String key, String value, List<String> tipoCodigos, String current) {
    return "tipo".equals(key) ? mapTipoToCodigo(value, tipoCodigos) : current;
  }

  private static Double applyConsumo(String key, String value, Double current) {
    if ("consumokwhdia".equals(key) || "consumo".equals(key)) {
      return parseDoubleSafe(value);
    }
    // Potencia en W sola → no convertir sin horas
    return current;
  }

  private static Double applyConfianza(String key, String value, Double current) {
    return "confianza".equals(key) ? parseDoubleSafe(value) : current;
  }

  private static String cleanValue(String raw) {
    if (raw == null) {
      return null;
    }
    String v = raw.trim();
    if (v.isEmpty()
        || v.equalsIgnoreCase("null")
        || v.startsWith("(")
        || v.equalsIgnoreCase("desconocido")
        || v.equalsIgnoreCase("n/a")) {
      return null;
    }
    return v.replaceAll("[\\[\\]]", "").trim();
  }

  private static Double parseDoubleSafe(String value) {
    String v = value.trim().replace(',', '.');
    v = v.replaceAll("[^0-9.]", "");
    if (v.isEmpty() || ".".equals(v)) {
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

  private static String detectMarca(String upper, String text) {
    if (upper.contains("ELECTROLUX")) {
      return "Electrolux";
    }
    if (upper.contains("SAMSUNG")) {
      return "Samsung";
    }
    if (upper.contains("WHIRLPOOL")) {
      return "Whirlpool";
    }
    if (upper.contains("BOSCH")) {
      return "Bosch";
    }
    if (upper.contains("MABE")) {
      return "Mabe";
    }
    if (upper.contains("LG")) {
      return "LG";
    }
    if (upper.contains("HAIER")) {
      return "Haier";
    }
    if (upper.contains("PANASONIC")) {
      return "Panasonic";
    }
    Matcher m = Pattern.compile("MARCA\\s*:?\\s*([A-Z][A-Z0-9 &-]{2,30})").matcher(upper);
    if (m.find()) {
      return tidy(m.group(1));
    }
    Matcher marcaEs = MARCA_ES.matcher(text);
    if (marcaEs.find()) {
      return tidy(marcaEs.group(1));
    }
    return null;
  }

  private static String detectModelo(String text) {
    Matcher modeloLabel =
        Pattern.compile("modelo\\s*:?\\s*([A-Z0-9][A-Z0-9-]{4,25})", Pattern.CASE_INSENSITIVE)
            .matcher(text);
    if (modeloLabel.find()) {
      return modeloLabel.group(1).trim();
    }
    Matcher modeloEs = MODELO_ES.matcher(text);
    if (modeloEs.find()) {
      return modeloEs.group(1).trim();
    }
    Matcher m = MODELO.matcher(text);
    while (m.find()) {
      String candidate = m.group(1);
      if (!candidate.equals("ELECTROLUX") && !candidate.equals("LAVADORA")) {
        return candidate;
      }
    }
    return null;
  }

  private static String detectTipo(String upper, List<String> tipoCodigos) {
    if (upper.contains("LAVADORA") || upper.contains("WASHING MACHINE")) {
      return pickCodigo(tipoCodigos, "LAVADORA");
    }
    if (upper.contains("NEVERA") || upper.contains("REFRIGERADOR") || upper.contains("REFRIGERATOR")) {
      return pickCodigo(tipoCodigos, "NEVERA");
    }
    if (upper.contains("LAVAVAJILLAS") || upper.contains("DISHWASHER")) {
      return pickCodigo(tipoCodigos, "LAVAVAJILLAS");
    }
    if (upper.contains("SECADORA") || upper.contains("DRYER")) {
      return pickCodigo(tipoCodigos, "SECADORA");
    }
    if (upper.contains("MICROONDAS") || upper.contains("MICROWAVE")) {
      return pickCodigo(tipoCodigos, "MICROONDAS");
    }
    if (upper.contains("HORNO") || upper.contains("OVEN")) {
      return pickCodigo(tipoCodigos, "HORNO");
    }
    if (upper.contains("AIRE ACONDICIONADO") || upper.contains("AIR CONDITIONER")) {
      return pickCodigo(tipoCodigos, "AIRE_ACONDICIONADO");
    }
    return null;
  }

  private static String pickCodigo(List<String> tipoCodigos, String preferred) {
    if (tipoCodigos.contains(preferred)) {
      return preferred;
    }
    return preferred;
  }

  /**
   * kWh/mes → /30; kWh/día → tal cual; solo W → null (sin horas).
   */
  private static Double estimateConsumoKwhDia(String text) {
    Matcher mes = KWH_MES.matcher(text);
    if (mes.find()) {
      String unit = mes.group(2).toLowerCase(Locale.ROOT);
      double val = Double.parseDouble(mes.group(1).replace(',', '.'));
      if (unit.startsWith("año") || unit.startsWith("year")) {
        return round4(val / 365.0);
      }
      return round4(val / 30.0);
    }
    Matcher dia = KWH_DIA.matcher(text);
    if (dia.find()) {
      return round4(Double.parseDouble(dia.group(1).replace(',', '.')));
    }
    Matcher plain = KWH_PLAIN.matcher(text);
    if (plain.find()) {
      double val = Double.parseDouble(plain.group(1).replace(',', '.'));
      // Valores grandes suelen ser mensuales sin "/mes" explícito
      if (val >= 30) {
        return round4(val / 30.0);
      }
      return round4(val);
    }
    // Solo watts sin horas → no estimar
    return null;
  }

  private static Double round4(double v) {
    return Math.round(v * 10000.0) / 10000.0;
  }

  private static String tidy(String value) {
    return value.trim().replaceAll("\\s+", " ");
  }
}
