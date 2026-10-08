package com.harmoniwatts.electro.service;

import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.MarcaCatalogoItem;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.TipoCatalogoItem;
import java.text.Normalizer;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Component;

/** Cruce fuzzy entre salida IA y catálogos de tipos/marcas. */
@Component
public class CatalogMatcher {

  private static final Map<String, String> TIPO_ALIASES =
      Map.ofEntries(
          Map.entry("REFRIGERADOR", "NEVERA"),
          Map.entry("REFRIGERATOR", "NEVERA"),
          Map.entry("FRIDGE", "NEVERA"),
          Map.entry("FREEZER", "CONGELADOR"),
          Map.entry("WASHING_MACHINE", "LAVADORA"),
          Map.entry("WASHER", "LAVADORA"),
          Map.entry("DISHWASHER", "LAVAVAJILLAS"),
          Map.entry("OVEN", "HORNO"),
          Map.entry("MICROWAVE", "MICROONDAS"),
          Map.entry("DRYER", "SECADORA"),
          Map.entry("TV", "TELEVISOR"),
          Map.entry("TELEVISION", "TELEVISOR"),
          Map.entry("AC", "AIRE_ACONDICIONADO"),
          Map.entry("AIR_CONDITIONER", "AIRE_ACONDICIONADO"),
          Map.entry("EV", "VEHICULO_ELECTRICO"),
          Map.entry("CALENTADOR", "TERMO_ELECTRICO"),
          Map.entry("TERMO", "TERMO_ELECTRICO"));

  public Optional<TipoCatalogoItem> matchTipo(String raw, List<TipoCatalogoItem> tipos) {
    if (raw == null || raw.isBlank()) {
      return Optional.empty();
    }
    String normalized = normalize(raw);
    String alias = TIPO_ALIASES.getOrDefault(normalized, normalized);

    Optional<TipoCatalogoItem> exact =
        tipos.stream().filter(t -> normalize(t.codigo()).equals(alias)).findFirst();
    if (exact.isPresent()) {
      return exact;
    }

    return tipos.stream()
        .filter(
            t ->
                normalize(t.codigo()).contains(alias)
                    || alias.contains(normalize(t.codigo()))
                    || normalize(t.nombreEs()).contains(normalized)
                    || normalized.contains(normalize(t.nombreEs())))
        .findFirst();
  }

  public MarcaMatch matchMarca(String raw, List<MarcaCatalogoItem> marcas) {
    if (raw == null || raw.isBlank()) {
      return MarcaMatch.empty();
    }
    String normalized = normalize(raw);

    Optional<MarcaCatalogoItem> exact =
        marcas.stream().filter(m -> normalize(m.nombre()).equals(normalized)).findFirst();
    if (exact.isPresent()) {
      return new MarcaMatch(exact.get().id(), null, false);
    }

    MarcaCatalogoItem best = null;
    int bestDist = Integer.MAX_VALUE;
    for (MarcaCatalogoItem m : marcas) {
      int d = levenshtein(normalized, normalize(m.nombre()));
      if (d < bestDist) {
        bestDist = d;
        best = m;
      }
    }
    if (best != null && bestDist <= 3) {
      return new MarcaMatch(best.id(), null, false);
    }

    MarcaCatalogoItem otro =
        marcas.stream().filter(m -> normalize(m.nombre()).equals("OTRO")).findFirst().orElse(null);
    if (otro != null) {
      return new MarcaMatch(otro.id(), raw.trim(), true);
    }
    return new MarcaMatch(null, raw.trim(), true);
  }

  public record MarcaMatch(Integer idMarcaPredefinida, String marcaOtro, boolean textoLibre) {
    static MarcaMatch empty() {
      return new MarcaMatch(null, null, false);
    }
  }

  private static String normalize(String s) {
    String n =
        Normalizer.normalize(s.trim().toUpperCase(Locale.ROOT), Normalizer.Form.NFD)
            .replaceAll("\\p{M}", "");
    return n.replaceAll("[^A-Z0-9_ ]", "").replace(' ', '_');
  }

  private static int levenshtein(String a, String b) {
    int[][] dp = new int[a.length() + 1][b.length() + 1];
    for (int i = 0; i <= a.length(); i++) {
      dp[i][0] = i;
    }
    for (int j = 0; j <= b.length(); j++) {
      dp[0][j] = j;
    }
    for (int i = 1; i <= a.length(); i++) {
      for (int j = 1; j <= b.length(); j++) {
        int cost = a.charAt(i - 1) == b.charAt(j - 1) ? 0 : 1;
        dp[i][j] =
            Math.min(Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1), dp[i - 1][j - 1] + cost);
      }
    }
    return dp[a.length()][b.length()];
  }
}
