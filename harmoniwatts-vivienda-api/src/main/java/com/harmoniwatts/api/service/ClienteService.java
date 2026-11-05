package com.harmoniwatts.api.service;

import com.harmoniwatts.api.domain.Cliente;
import com.harmoniwatts.api.repo.ClienteRepository;
import com.harmoniwatts.api.web.dto.ClienteDtos.ClienteCreateRequest;
import com.harmoniwatts.api.web.dto.ClienteDtos.ClienteResponse;
import com.harmoniwatts.api.web.dto.ClienteDtos.ClienteUpdateRequest;
import jakarta.persistence.EntityManager;
import java.time.Instant;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class ClienteService {

  private final ClienteRepository clienteRepository;
  private final EntityManager em;

  public ClienteService(ClienteRepository clienteRepository, EntityManager em) {
    this.clienteRepository = clienteRepository;
    this.em = em;
  }

  @Transactional(readOnly = true)
  public List<ClienteResponse> listForUser(String email) {
    return clienteRepository.findByEmailIgnoreCase(email).map(ClienteResponse::from).stream()
        .toList();
  }

  @Transactional(readOnly = true)
  public ClienteResponse get(String email, long id) {
    return ClienteResponse.from(find(email, id));
  }

  @Transactional
  public ClienteResponse create(String email, ClienteCreateRequest req) {
    if (clienteRepository.existsByEmailIgnoreCase(email)) {
      throw new ResponseStatusException(HttpStatus.CONFLICT, "Ya existe un cliente con ese email");
    }
    Cliente c = new Cliente();
    c.setEmail(email.trim().toLowerCase());
    aplicar(
        c, req.nombre(), req.noContrato(), req.telefono(), req.codTipoCliente(), req.estrato(),
        req.codNivel(), req.idZona(), req.codMercado(), req.codComercializadora());
    return guardar(c);
  }

  @Transactional
  public ClienteResponse update(String email, long id, ClienteUpdateRequest req) {
    Cliente c = find(email, id);
    aplicar(
        c, req.nombre(), req.noContrato(), req.telefono(), req.codTipoCliente(), req.estrato(),
        req.codNivel(), req.idZona(), req.codMercado(), req.codComercializadora());
    if (req.activo() != null) {
      c.setActivo(req.activo());
    }
    return guardar(c);
  }

  private Cliente find(String email, long id) {
    return clienteRepository
        .findByIdAndEmailIgnoreCase(id, email)
        .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
  }

  /** Guarda y recarga la fila para traer cs_kwh_mes, que calcula el trigger de la BD. */
  private ClienteResponse guardar(Cliente c) {
    Cliente saved = clienteRepository.saveAndFlush(c);
    em.refresh(saved);
    return ClienteResponse.from(saved);
  }

  /** Regla de la BD: el estrato es obligatorio para 'R' y debe ser nulo para los demás tipos. */
  private static void aplicar(
      Cliente c,
      String nombre,
      String noContrato,
      String telefono,
      String codTipoCliente,
      Short estrato,
      String codNivel,
      Short idZona,
      String codMercado,
      String codComercializadora) {
    String tipo = codTipoCliente.trim().toUpperCase();
    boolean residencial = "R".equals(tipo);
    if (residencial && estrato == null) {
      throw new ResponseStatusException(
          HttpStatus.BAD_REQUEST, "El estrato es obligatorio para clientes residenciales");
    }
    if (!residencial && estrato != null) {
      throw new ResponseStatusException(
          HttpStatus.BAD_REQUEST, "El estrato solo aplica a clientes residenciales");
    }
    c.setNombre(nombre.trim());
    c.setNoContrato(noContrato.trim());
    c.setTelefono(telefono != null && !telefono.isBlank() ? telefono.trim() : null);
    c.setCodTipoCliente(tipo);
    c.setEstrato(estrato);
    c.setCodNivel(codNivel.trim());
    c.setIdZona(idZona);
    c.setCodMercado(codMercado.trim());
    c.setCodComercializadora(codComercializadora.trim());
  }
}
