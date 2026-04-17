package com.harmoniwatts.api.web;

import com.harmoniwatts.api.service.ViviendaService;
import com.harmoniwatts.api.web.dto.ViviendaDtos.ViviendaCreateRequest;
import com.harmoniwatts.api.web.dto.ViviendaDtos.ViviendaResponse;
import com.harmoniwatts.api.web.dto.ViviendaDtos.ViviendaUpdateRequest;
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
@RequestMapping("/api/v1/viviendas")
public class ViviendaController {

  private final ViviendaService viviendaService;

  public ViviendaController(ViviendaService viviendaService) {
    this.viviendaService = viviendaService;
  }

  @GetMapping
  public List<ViviendaResponse> list(@AuthenticationPrincipal Jwt jwt) {
    return viviendaService.listForUser(requireSub(jwt));
  }

  @PostMapping
  @ResponseStatus(HttpStatus.CREATED)
  public ViviendaResponse create(
      @AuthenticationPrincipal Jwt jwt, @Valid @RequestBody ViviendaCreateRequest body) {
    return viviendaService.create(requireSub(jwt), body);
  }

  @PutMapping("/{id}")
  public ViviendaResponse update(
      @AuthenticationPrincipal Jwt jwt,
      @PathVariable long id,
      @Valid @RequestBody ViviendaUpdateRequest body) {
    return viviendaService.update(requireSub(jwt), id, body);
  }

  @DeleteMapping("/{id}")
  @ResponseStatus(HttpStatus.NO_CONTENT)
  public void delete(@AuthenticationPrincipal Jwt jwt, @PathVariable long id) {
    viviendaService.delete(requireSub(jwt), id);
  }

  private static String requireSub(Jwt jwt) {
    if (jwt == null || jwt.getSubject() == null || jwt.getSubject().isBlank()) {
      throw new IllegalStateException("Token sin subject (sub)");
    }
    return jwt.getSubject();
  }
}
