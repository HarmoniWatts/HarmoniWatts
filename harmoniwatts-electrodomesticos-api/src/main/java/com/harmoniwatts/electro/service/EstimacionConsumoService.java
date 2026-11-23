package com.harmoniwatts.electro.service;

import com.harmoniwatts.electro.domain.Electrodomestico;
import com.harmoniwatts.electro.domain.ElectrodomesticoHorario;
import com.harmoniwatts.electro.repo.ElectrodomesticoRepository;
import com.harmoniwatts.electro.repo.ViviendaRepository;
import com.harmoniwatts.electro.service.EstimacionConsumoCalculator.Franja;
import com.harmoniwatts.electro.service.EstimacionConsumoCalculator.Resultado;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.EstimacionElectrodomestico;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.EstimacionViviendaResponse;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

/** Estimación de consumo por electrodoméstico y ranking de la vivienda (HAR-20). */
@Service
public class EstimacionConsumoService {

  private final ViviendaRepository viviendaRepository;
  private final ElectrodomesticoRepository electroRepository;

  public EstimacionConsumoService(
      ViviendaRepository viviendaRepository, ElectrodomesticoRepository electroRepository) {
    this.viviendaRepository = viviendaRepository;
    this.electroRepository = electroRepository;
  }

  @Transactional(readOnly = true)
  public EstimacionViviendaResponse estimar(String keycloakSub, long idVivienda) {
    viviendaRepository
        .findByIdAndKeycloakUserId(idVivienda, keycloakSub)
        .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Vivienda no encontrada"));

    List<Electrodomestico> rows = electroRepository.findAllForViviendaAndOwner(idVivienda, keycloakSub);

    record Calc(Electrodomestico e, Resultado r) {}
    List<Calc> calcs = new ArrayList<>();
    for (Electrodomestico e : rows) {
      Resultado r =
          EstimacionConsumoCalculator.calcular(
              e.getHorarios().stream().map(EstimacionConsumoService::toFranja).toList(),
              e.getPotenciaW(),
              e.getConsumoKwhDia(),
              e.getConsumoAjustadoKwhMes());
      calcs.add(new Calc(e, r));
    }

    // Solo los activos cuentan para el total, el ranking y el perfil de la vivienda
    double totalMes =
        calcs.stream().filter(c -> isActivo(c.e())).mapToDouble(c -> c.r().kwhMes()).sum();
    double[][] perfilTotal = new double[7][24];
    calcs.stream()
        .filter(c -> isActivo(c.e()))
        .forEach(
            c -> {
              for (int d = 0; d < 7; d++) {
                for (int h = 0; h < 24; h++) {
                  perfilTotal[d][h] += c.r().perfilSemanal()[d][h];
                }
              }
            });

    List<Calc> ordenados =
        calcs.stream()
            .sorted(
                Comparator.comparing((Calc c) -> !isActivo(c.e()))
                    .thenComparing(c -> -c.r().kwhMes()))
            .toList();

    List<EstimacionElectrodomestico> out = new ArrayList<>();
    int rank = 0;
    for (Calc c : ordenados) {
      Electrodomestico e = c.e();
      Resultado r = c.r();
      boolean activo = isActivo(e);
      out.add(
          new EstimacionElectrodomestico(
              e.getId(),
              e.getNombre(),
              e.getTipoPredefinido() != null ? e.getTipoPredefinido().getCodigo() : e.getTipo(),
              e.getTipoPredefinido() != null ? e.getTipoPredefinido().getNombreEs() : e.getTipo(),
              activo,
              Boolean.TRUE.equals(e.getDesplazable()),
              r.fuente(),
              e.getPotenciaW(),
              round(r.horasSemana(), 2),
              round(r.kwhDia(), 4),
              round(r.kwhSemana(), 4),
              round(r.kwhMes(), 3),
              round(r.kwhMesCalculado(), 3),
              activo && totalMes > 0 ? round(r.kwhMes() * 100.0 / totalMes, 2) : 0,
              activo ? ++rank : 0,
              roundMatrix(r.perfilSemanal())));
    }

    return new EstimacionViviendaResponse(
        idVivienda,
        EstimacionConsumoCalculator.DIAS_POR_MES,
        round(totalMes / EstimacionConsumoCalculator.DIAS_POR_MES, 4),
        round(totalMes, 3),
        roundMatrix(perfilTotal),
        out);
  }

  static Franja toFranja(ElectrodomesticoHorario h) {
    return new Franja(h.getDiaSemana(), h.getHoraInicio(), h.getHoraFin());
  }

  private static boolean isActivo(Electrodomestico e) {
    return e.getActivo() == null || e.getActivo();
  }

  private static double round(double v, int dec) {
    double f = Math.pow(10, dec);
    return Math.round(v * f) / f;
  }

  private static double[][] roundMatrix(double[][] m) {
    double[][] r = new double[m.length][];
    for (int i = 0; i < m.length; i++) {
      r[i] = new double[m[i].length];
      for (int j = 0; j < m[i].length; j++) {
        r[i][j] = round(m[i][j], 5);
      }
    }
    return r;
  }
}
