package com.harmoniwatts.api.web.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.harmoniwatts.api.domain.Vivienda;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public final class ViviendaDtos {

  private ViviendaDtos() {}

  public record ViviendaCreateRequest(
      @NotBlank @Size(max = 50) String tipo,
      @NotNull @Min(1) @Max(99) Integer habitantes,
      @NotNull @Min(1) @Max(6) Integer estrato,
      @NotBlank @Size(max = 200) String ubicacion) {}

  public record ViviendaUpdateRequest(
      @NotBlank @Size(max = 50) String tipo,
      @NotNull @Min(1) @Max(99) Integer habitantes,
      @NotNull @Min(1) @Max(6) Integer estrato,
      @NotBlank @Size(max = 200) String ubicacion,
      @Size(max = 20) String zonaClimatica) {}

  @JsonInclude(JsonInclude.Include.NON_NULL)
  public record ViviendaResponse(
      Long id,
      String tipo,
      Integer habitantes,
      Integer estrato,
      String ubicacion,
      String zonaClimatica,
      String fechaRegistro) {

    public static ViviendaResponse from(Vivienda v) {
      return new ViviendaResponse(
          v.getId(),
          v.getTipo(),
          v.getHabitantes(),
          v.getEstrato(),
          v.getDireccion(),
          v.getZonaClimatica(),
          v.getFechaRegistro() != null ? v.getFechaRegistro().toString() : null);
    }
  }
}
