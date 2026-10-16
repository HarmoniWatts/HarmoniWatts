package com.harmoniwatts.api.service;

import com.harmoniwatts.api.domain.Vivienda;
import com.harmoniwatts.api.repo.ViviendaRepository;
import com.harmoniwatts.api.web.dto.ViviendaDtos.ViviendaCreateRequest;
import com.harmoniwatts.api.web.dto.ViviendaDtos.ViviendaResponse;
import com.harmoniwatts.api.web.dto.ViviendaDtos.ViviendaUpdateRequest;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class ViviendaService {

  private final ViviendaRepository viviendaRepository;

  public ViviendaService(ViviendaRepository viviendaRepository) {
    this.viviendaRepository = viviendaRepository;
  }

  @Transactional(readOnly = true)
  public List<ViviendaResponse> listForUser(String keycloakSub) {
    return viviendaRepository.findByKeycloakUserIdOrderByIdAsc(keycloakSub).stream()
        .map(ViviendaResponse::from)
        .toList();
  }

  @Transactional
  public ViviendaResponse create(String keycloakSub, ViviendaCreateRequest req) {
    Vivienda v = new Vivienda();
    v.setKeycloakUserId(keycloakSub);
    v.setTipo(req.tipo().trim());
    v.setHabitantes(req.habitantes());
    v.setEstrato(req.estrato());
    v.setDireccion(req.ubicacion().trim());
    aplicarUbicacionTarifaria(v, req.idZona(), req.codMercado(), req.numeroContrato());
    return ViviendaResponse.from(viviendaRepository.save(v));
  }

  @Transactional
  public ViviendaResponse update(String keycloakSub, long id, ViviendaUpdateRequest req) {
    Vivienda v =
        viviendaRepository
            .findByIdAndKeycloakUserId(id, keycloakSub)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    v.setTipo(req.tipo().trim());
    v.setHabitantes(req.habitantes());
    v.setEstrato(req.estrato());
    v.setDireccion(req.ubicacion().trim());
    if (req.zonaClimatica() != null && !req.zonaClimatica().isBlank()) {
      v.setZonaClimatica(req.zonaClimatica().trim());
    } else {
      v.setZonaClimatica(null);
    }
    aplicarUbicacionTarifaria(v, req.idZona(), req.codMercado(), req.numeroContrato());
    return ViviendaResponse.from(viviendaRepository.save(v));
  }

  /**
   * Ciudad (idZona + codMercado, deben existir juntos en mercado_zona) y número de contrato.
   * La ciudad es opcional, pero sin ella no se pueden resolver las tarifas de la vivienda.
   */
  private static void aplicarUbicacionTarifaria(
      Vivienda v, Short idZona, String codMercado, String numeroContrato) {
    String mercado = codMercado != null && !codMercado.isBlank() ? codMercado.trim() : null;
    if ((idZona == null) != (mercado == null)) {
      throw new ResponseStatusException(
          HttpStatus.BAD_REQUEST, "idZona y codMercado deben enviarse juntos");
    }
    v.setIdZona(idZona);
    v.setCodMercado(mercado);
    v.setNumeroContrato(
        numeroContrato != null && !numeroContrato.isBlank() ? numeroContrato.trim() : null);
  }

  @Transactional
  public void delete(String keycloakSub, long id) {
    Vivienda v =
        viviendaRepository
            .findByIdAndKeycloakUserId(id, keycloakSub)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    viviendaRepository.delete(v);
  }
}
