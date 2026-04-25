package com.harmoniwatts.electro.repo;

import com.harmoniwatts.electro.domain.Electrodomestico;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ElectrodomesticoRepository extends JpaRepository<Electrodomestico, Long> {

  @EntityGraph(attributePaths = {"tipoPredefinido", "marcaPredefinida"})
  @Query(
      """
      select e from Electrodomestico e
      join e.vivienda v
      where v.id = :viviendaId and v.keycloakUserId = :sub
      order by e.id asc
      """)
  List<Electrodomestico> findAllForViviendaAndOwner(
      @Param("viviendaId") Long viviendaId, @Param("sub") String sub);

  @EntityGraph(attributePaths = {"tipoPredefinido", "marcaPredefinida", "vivienda"})
  @Query(
      """
      select e from Electrodomestico e
      join e.vivienda v
      where e.id = :electroId and v.id = :viviendaId and v.keycloakUserId = :sub
      """)
  Optional<Electrodomestico> findByIdAndViviendaAndOwner(
      @Param("electroId") Long electroId,
      @Param("viviendaId") Long viviendaId,
      @Param("sub") String sub);
}
