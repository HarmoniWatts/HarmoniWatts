package com.harmoniwatts.electro.web;

import com.harmoniwatts.electro.service.ElectrodomesticoCrudService;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.ElectrodomesticoCreateRequest;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.ElectrodomesticoResponse;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.ElectrodomesticoUpdateRequest;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/viviendas/{viviendaId}/electrodomesticos")
public class ViviendaElectrodomesticoController {

  private final ElectrodomesticoCrudService crudService;

  public ViviendaElectrodomesticoController(ElectrodomesticoCrudService crudService) {
    this.crudService = crudService;
  }

  @GetMapping
  public List<ElectrodomesticoResponse> listar(
      @AuthenticationPrincipal Jwt jwt, @PathVariable long viviendaId) {
    return crudService.listar(requireSub(jwt), viviendaId);
  }

  @PostMapping
  @ResponseStatus(HttpStatus.CREATED)
  public ElectrodomesticoResponse crear(
      @AuthenticationPrincipal Jwt jwt,
      @PathVariable long viviendaId,
      @Valid @RequestBody ElectrodomesticoCreateRequest body) {
    return crudService.crear(requireSub(jwt), viviendaId, body);
  }

  @PutMapping("/{electroId}")
  public ElectrodomesticoResponse actualizar(
      @AuthenticationPrincipal Jwt jwt,
      @PathVariable long viviendaId,
      @PathVariable long electroId,
      @Valid @RequestBody ElectrodomesticoUpdateRequest body) {
    return crudService.actualizar(requireSub(jwt), viviendaId, electroId, body);
  }

  @DeleteMapping("/{electroId}")
  @ResponseStatus(HttpStatus.NO_CONTENT)
  public void eliminar(
      @AuthenticationPrincipal Jwt jwt, @PathVariable long viviendaId, @PathVariable long electroId) {
    crudService.eliminar(requireSub(jwt), viviendaId, electroId);
  }

  private static String requireSub(Jwt jwt) {
    if (jwt == null || jwt.getSubject() == null || jwt.getSubject().isBlank()) {
      throw new IllegalStateException("Token sin subject (sub)");
    }
    return jwt.getSubject();
  }
}
