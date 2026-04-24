package com.harmoniwatts.electro.repo;

import com.harmoniwatts.electro.domain.Vivienda;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ViviendaRepository extends JpaRepository<Vivienda, Long> {

  Optional<Vivienda> findByIdAndKeycloakUserId(Long id, String keycloakUserId);
}
