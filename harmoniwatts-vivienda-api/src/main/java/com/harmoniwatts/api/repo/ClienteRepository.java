package com.harmoniwatts.api.repo;

import com.harmoniwatts.api.domain.Cliente;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ClienteRepository extends JpaRepository<Cliente, Long> {

  Optional<Cliente> findByEmailIgnoreCase(String email);

  Optional<Cliente> findByIdAndEmailIgnoreCase(Long id, String email);

  boolean existsByEmailIgnoreCase(String email);
}
