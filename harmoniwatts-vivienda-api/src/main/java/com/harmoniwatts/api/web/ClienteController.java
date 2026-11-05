package com.harmoniwatts.api.web;

import com.harmoniwatts.api.service.ClienteService;
import com.harmoniwatts.api.web.dto.ClienteDtos.ClienteCreateRequest;
import com.harmoniwatts.api.web.dto.ClienteDtos.ClienteResponse;
import com.harmoniwatts.api.web.dto.ClienteDtos.ClienteUpdateRequest;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/clientes")
public class ClienteController {

  private final ClienteService clienteService;

  public ClienteController(ClienteService clienteService) {
    this.clienteService = clienteService;
  }

  @GetMapping
  public List<ClienteResponse> list(@AuthenticationPrincipal Jwt jwt) {
    return clienteService.listForUser(requireEmail(jwt));
  }

  @GetMapping("/{id}")
  public ClienteResponse get(@AuthenticationPrincipal Jwt jwt, @PathVariable long id) {
    return clienteService.get(requireEmail(jwt), id);
  }

  @PostMapping
  @ResponseStatus(HttpStatus.CREATED)
  public ClienteResponse create(
      @AuthenticationPrincipal Jwt jwt, @Valid @RequestBody ClienteCreateRequest body) {
    return clienteService.create(requireEmail(jwt), body);
  }

  @PutMapping("/{id}")
  public ClienteResponse update(
      @AuthenticationPrincipal Jwt jwt,
      @PathVariable long id,
      @Valid @RequestBody ClienteUpdateRequest body) {
    return clienteService.update(requireEmail(jwt), id, body);
  }

  private static String requireEmail(Jwt jwt) {
    String email = jwt == null ? null : jwt.getClaimAsString("email");
    if (email == null || email.isBlank()) {
      throw new IllegalStateException("Token sin claim email");
    }
    return email;
  }
}
