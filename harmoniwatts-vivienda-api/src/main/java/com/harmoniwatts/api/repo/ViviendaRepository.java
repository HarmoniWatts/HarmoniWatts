package com.harmoniwatts.api.repo;

import com.harmoniwatts.api.domain.Vivienda;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ViviendaRepository extends JpaRepository<Vivienda, Long> {

  List<Vivienda> findByKeycloakUserIdOrderByIdAsc(String keycloakUserId);

  Optional<Vivienda> findByIdAndKeycloakUserId(Long id, String keycloakUserId);
}
