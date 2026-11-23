package com.harmoniwatts.electro.web.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.harmoniwatts.electro.domain.Electrodomestico;
import com.harmoniwatts.electro.domain.ElectrodomesticoTipoPredefinido;
import com.harmoniwatts.electro.domain.MarcaPredefinida;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;
import java.util.List;

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
      Boolean esDesplazable,
      @Positive @Max(100000) Double potenciaW,
      @PositiveOrZero Double consumoAjustadoKwhMes,
      /** Franjas de uso; null = sin horarios. */
      @Size(max = 50) List<@Valid HorarioDto> horarios) {}

  public record ElectrodomesticoUpdateRequest(
      @NotNull Integer idTipoPredefinido,
      Integer idMarcaPredefinida,
      @Size(max = 100) String marcaOtro,
      @Size(max = 100) String nombre,
      @NotNull @Positive Double consumoKwhDia,
      @NotNull @Min(0) @Max(168) Integer usoSemanal,
      String horarioHabitual,
      Boolean esDesplazable,
      Boolean activo,
      @Positive @Max(100000) Double potenciaW,
      @PositiveOrZero Double consumoAjustadoKwhMes,
      /** Franjas de uso; null = no se modifican, [] = se eliminan. */
      @Size(max = 50) List<@Valid HorarioDto> horarios) {}

  /**
   * Franja de uso. {@code diaSemana}: 1 = lunes … 7 = domingo. Horas `HH:mm`; si {@code horaFin}
   * es menor o igual que {@code horaInicio} la franja cruza la medianoche (igual = 24 h).
   */
  public record HorarioDto(
      @NotNull @Min(1) @Max(7) Integer diaSemana,
      @NotNull String horaInicio,
      @NotNull String horaFin) {}

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
      Boolean activo,
      Double potenciaW,
      Double consumoAjustadoKwhMes,
      List<HorarioDto> horarios) {

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
          e.getActivo(),
          e.getPotenciaW(),
          e.getConsumoAjustadoKwhMes(),
          e.getHorarios().stream()
              .map(
                  h ->
                      new HorarioDto(
                          h.getDiaSemana(), hhmm(h.getHoraInicio()), hhmm(h.getHoraFin())))
              .toList());
    }

    private static String hhmm(java.time.LocalTime t) {
      return String.format("%02d:%02d", t.getHour(), t.getMinute());
    }
  }

  /** Respuesta del análisis IA para prellenar el formulario de registro. */
  @JsonInclude(JsonInclude.Include.NON_NULL)
  public record VisionAnalysisResponse(
      String marcaDetectada,
      String modeloDetectado,
      String tipoSugerido,
      /** Potencia leída de la placa (W); la app la combina con el horario del usuario. */
      Double potenciaWDetectada,
      /** Consumo de la etiqueta energética (kWh/mes); la app lo convierte a W con el horario. */
      Double consumoKwhMesDetectado,
      Double confianza,
      String fuenteConsumo,
      Integer idTipoPredefinido,
      String tipoNombre,
      Integer idMarcaPredefinida,
      String marcaOtro,
      String nombreSugerido,
      Boolean bajaConfianza,
      String advertencia) {}

  /** Estimación de consumo de un electrodoméstico (HAR-20). */
  public record EstimacionElectrodomestico(
      Long id,
      String nombre,
      String tipoCodigo,
      String tipoNombre,
      boolean activo,
      /** Desplazable en el tiempo → se puede optimizar moviéndolo a horas valle. */
      boolean optimizable,
      /** HORARIO_POTENCIA | HORARIO_CONSUMO | PROMEDIO_DIARIO | AJUSTE_USUARIO */
      String fuente,
      Double potenciaW,
      double horasSemana,
      double kwhDia,
      double kwhSemana,
      double kwhMes,
      /** kWh/mes calculado sin el ajuste del usuario (para comparar). */
      double kwhMesCalculado,
      /** Participación en el consumo total de la vivienda (0–100). */
      double porcentaje,
      int ranking,
      /** kWh por [día ISO-1][hora 0–23] en una semana típica. */
      double[][] perfilSemanal) {}

  public record EstimacionViviendaResponse(
      Long idVivienda,
      double diasPorMes,
      double totalKwhDia,
      double totalKwhMes,
      double[][] perfilSemanal,
      List<EstimacionElectrodomestico> electrodomesticos) {}
}
