package com.harmoniwatts.api.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.harmoniwatts.api.domain.Vivienda;
import com.harmoniwatts.api.repo.ViviendaRepository;
import com.harmoniwatts.api.web.dto.ViviendaDtos.ViviendaCreateRequest;
import com.harmoniwatts.api.web.dto.ViviendaDtos.ViviendaResponse;
import com.harmoniwatts.api.web.dto.ViviendaDtos.ViviendaUpdateRequest;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

@ExtendWith(MockitoExtension.class)
class ViviendaServiceTest {

  private static final String SUB = "user-123";

  @Mock private ViviendaRepository repository;

  @InjectMocks private ViviendaService service;

  @Test
  void createAsignaUsuarioYRecortaCampos() {
    when(repository.save(any(Vivienda.class))).thenAnswer(inv -> inv.getArgument(0));

    ViviendaResponse res =
        service.create(SUB, new ViviendaCreateRequest("  Casa ", 3, 4, " Calle 1 # 2-3 "));

    assertThat(res.tipo()).isEqualTo("Casa");
    assertThat(res.ubicacion()).isEqualTo("Calle 1 # 2-3");
    assertThat(res.habitantes()).isEqualTo(3);
    assertThat(res.estrato()).isEqualTo(4);
  }

  @Test
  void updateLimpiaZonaClimaticaEnBlanco() {
    Vivienda existente = new Vivienda();
    existente.setKeycloakUserId(SUB);
    existente.setZonaClimatica("CALIDA");
    when(repository.findByIdAndKeycloakUserId(5L, SUB)).thenReturn(Optional.of(existente));
    when(repository.save(any(Vivienda.class))).thenAnswer(inv -> inv.getArgument(0));

    ViviendaResponse res =
        service.update(SUB, 5L, new ViviendaUpdateRequest("Apto", 2, 3, "Cra 7", "  "));

    assertThat(res.zonaClimatica()).isNull();
  }

  @Test
  void updateDeViviendaAjenaDevuelve404() {
    when(repository.findByIdAndKeycloakUserId(7L, SUB)).thenReturn(Optional.empty());

    assertThatThrownBy(
            () -> service.update(SUB, 7L, new ViviendaUpdateRequest("Apto", 2, 3, "Cra 7", null)))
        .isInstanceOf(ResponseStatusException.class)
        .extracting(e -> ((ResponseStatusException) e).getStatusCode())
        .isEqualTo(HttpStatus.NOT_FOUND);
    verify(repository, never()).save(any());
  }

  @Test
  void deleteDeViviendaAjenaNoBorraNada() {
    when(repository.findByIdAndKeycloakUserId(8L, SUB)).thenReturn(Optional.empty());

    assertThatThrownBy(() -> service.delete(SUB, 8L)).isInstanceOf(ResponseStatusException.class);
    verify(repository, never()).delete(any());
  }
}
