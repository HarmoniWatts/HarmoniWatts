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
    return ViviendaResponse.from(viviendaRepository.save(v));
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
