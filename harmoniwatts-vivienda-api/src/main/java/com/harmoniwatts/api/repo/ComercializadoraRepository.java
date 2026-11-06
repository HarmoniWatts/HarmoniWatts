package com.harmoniwatts.api.repo;

import com.harmoniwatts.api.domain.Comercializadora;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ComercializadoraRepository extends JpaRepository<Comercializadora, String> {

  List<Comercializadora> findByActivoTrueOrderByNombreAsc();
}
