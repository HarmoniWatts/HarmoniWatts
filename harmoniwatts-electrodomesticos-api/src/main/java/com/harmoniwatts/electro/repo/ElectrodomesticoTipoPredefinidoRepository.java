package com.harmoniwatts.electro.repo;

import com.harmoniwatts.electro.domain.ElectrodomesticoTipoPredefinido;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ElectrodomesticoTipoPredefinidoRepository
    extends JpaRepository<ElectrodomesticoTipoPredefinido, Integer> {

  List<ElectrodomesticoTipoPredefinido> findByActivoTrueOrderByOrdenAsc();

  Optional<ElectrodomesticoTipoPredefinido> findByIdAndActivoTrue(Integer id);
}
