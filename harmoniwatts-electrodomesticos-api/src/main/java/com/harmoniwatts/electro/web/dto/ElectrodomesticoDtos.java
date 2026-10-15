package com.harmoniwatts.electro.web.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.harmoniwatts.electro.domain.Electrodomestico;
import com.harmoniwatts.electro.domain.ElectrodomesticoTipoPredefinido;
import com.harmoniwatts.electro.domain.MarcaPredefinida;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

public final class ElectrodomesticoDtos {

  private ElectrodomesticoDtos() {}

  public record TipoCatalogoItem(
      Integer id, String codigo, String nombreEs, short orden, boolean activo) {}

  public record MarcaCatalogoItem(
      Integer id, String nombre, short orden, boolean activo) {}

  public record CatalogosResponse(
      java.util.List<TipoCatalogoItem> tipos, java.util.List<MarcaCatalogoItem> marcas) {}

  public record ElectrodomesticoCreateRequest(
      @NotNull Integer idTipoPredefinido,
      Integer idMarcaPredefinida,
      @Size(max = 100) String marcaOtro,
      @Size(max = 100) String nombre,
      @NotNull @Positive Double consumoKwhDia,
      @NotNull @Min(0) @Max(168) Integer usoSemanal,
      /** Opcional. Formato hora local ISO, p. ej. `18:30` o `18:30:00` → columna `horario_habitual`. */
      String horarioHabitual,
      Boolean esDesplazable) {}

  public record ElectrodomesticoUpdateRequest(
      @NotNull Integer idTipoPredefinido,
      Integer idMarcaPredefinida,
      @Size(max = 100) String marcaOtro,
      @Size(max = 100) String nombre,
      @NotNull @Positive Double consumoKwhDia,
      @NotNull @Min(0) @Max(168) Integer usoSemanal,
      String horarioHabitual,
      Boolean esDesplazable,
      Boolean activo) {}

  @JsonInclude(JsonInclude.Include.NON_NULL)
  public record ElectrodomesticoResponse(
      Long id,
      Long idVivienda,
      Integer idTipoPredefinido,
      String tipoCodigo,
      String tipoNombre,
      Integer idMarcaPredefinida,
      String marcaNombre,
      String marcaOtro,
      String nombre,
      Double consumoKwhDia,
      Integer usoSemanal,
      String horarioHabitual,
      Boolean esDesplazable,
      Boolean activo) {

    public static ElectrodomesticoResponse from(Electrodomestico e, long idVivienda) {
      ElectrodomesticoTipoPredefinido t = e.getTipoPredefinido();
      MarcaPredefinida m = e.getMarcaPredefinida();
      return new ElectrodomesticoResponse(
          e.getId(),
          idVivienda,
          t != null ? t.getId() : null,
          t != null ? t.getCodigo() : null,
          t != null ? t.getNombreEs() : null,
          m != null ? m.getId() : null,
          m != null ? m.getNombre() : null,
          e.getMarcaOtro(),
          e.getNombre(),
          e.getConsumoKwhDia(),
          e.getUsoSemanal(),
          e.getHorarioHabitual() != null ? e.getHorarioHabitual().toString() : null,
          e.getDesplazable(),
          e.getActivo());
    }
  }

  /** Respuesta del análisis IA para prellenar el formulario de registro. */
  @JsonInclude(JsonInclude.Include.NON_NULL)
  public record VisionAnalysisResponse(
      String marcaDetectada,
      String modeloDetectado,
      String tipoSugerido,
      Double consumoKwhDiaEstimado,
      Double confianza,
      String fuenteConsumo,
      Integer idTipoPredefinido,
      String tipoNombre,
      Integer idMarcaPredefinida,
      String marcaOtro,
      String nombreSugerido,
      Boolean bajaConfianza,
      String advertencia) {}
}
