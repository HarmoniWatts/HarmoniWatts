package com.harmoniwatts.api.web.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.harmoniwatts.api.domain.Cliente;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

public final class ClienteDtos {

  private ClienteDtos() {}

  /** El email sale del JWT, no del cuerpo. */
  public record ClienteCreateRequest(
      @NotBlank @Size(max = 100) String nombre,
      @NotBlank @Size(max = 20) String noContrato,
      @Size(max = 20) String telefono,
      @NotBlank @Size(min = 1, max = 1) String codTipoCliente,
      @Min(1) @Max(6) Short estrato,
      @NotBlank @Size(max = 15) String codNivel,
      @NotNull @Positive Short idZona,
      @NotBlank @Size(max = 30) String codMercado,
      @NotBlank @Size(max = 20) String codComercializadora) {}

  public record ClienteUpdateRequest(
      @NotBlank @Size(max = 100) String nombre,
      @NotBlank @Size(max = 20) String noContrato,
      @Size(max = 20) String telefono,
      @NotBlank @Size(min = 1, max = 1) String codTipoCliente,
      @Min(1) @Max(6) Short estrato,
      @NotBlank @Size(max = 15) String codNivel,
      @NotNull @Positive Short idZona,
      @NotBlank @Size(max = 30) String codMercado,
      @NotBlank @Size(max = 20) String codComercializadora,
      Boolean activo) {}

  @JsonInclude(JsonInclude.Include.NON_NULL)
  public record ClienteResponse(
      Long id,
      String nombre,
      String noContrato,
      String email,
      String telefono,
      String codTipoCliente,
      Short estrato,
      String codNivel,
      Short idZona,
      String codMercado,
      String codComercializadora,
      BigDecimal csKwhMes,
      Boolean activo,
      String fechaRegistro,
      String ultimoAcceso) {

    public static ClienteResponse from(Cliente c) {
      return new ClienteResponse(
          c.getId(),
          c.getNombre(),
          c.getNoContrato(),
          c.getEmail(),
          c.getTelefono(),
          c.getCodTipoCliente(),
          c.getEstrato(),
          c.getCodNivel(),
          c.getIdZona(),
          c.getCodMercado(),
          c.getCodComercializadora(),
          c.getCsKwhMes(),
          c.getActivo(),
          c.getFechaRegistro() != null ? c.getFechaRegistro().toString() : null,
          c.getUltimoAcceso() != null ? c.getUltimoAcceso().toString() : null);
    }
  }
}
