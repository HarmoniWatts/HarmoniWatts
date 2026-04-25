package com.harmoniwatts.electro.repo;

import com.harmoniwatts.electro.domain.MarcaPredefinida;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MarcaPredefinidaRepository extends JpaRepository<MarcaPredefinida, Integer> {

  List<MarcaPredefinida> findByActivoTrueOrderByOrdenAsc();

  Optional<MarcaPredefinida> findByIdAndActivoTrue(Integer id);
}
