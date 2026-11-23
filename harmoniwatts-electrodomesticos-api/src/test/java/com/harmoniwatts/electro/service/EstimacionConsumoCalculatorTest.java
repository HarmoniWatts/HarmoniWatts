package com.harmoniwatts.electro.service;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.harmoniwatts.electro.service.EstimacionConsumoCalculator.Franja;
import com.harmoniwatts.electro.service.EstimacionConsumoCalculator.Resultado;
import java.time.LocalTime;
import java.util.List;
import org.junit.jupiter.api.Test;

class EstimacionConsumoCalculatorTest {

  private static final double EPS = 1e-6;

  @Test
  void horarioConPotencia() {
    // Lunes 18:00–19:30 a 2000 W → 3 kWh/semana
    Resultado r =
        EstimacionConsumoCalculator.calcular(
            List.of(new Franja(1, LocalTime.of(18, 0), LocalTime.of(19, 30))), 2000.0, 9.0, null);
    assertEquals(EstimacionConsumoCalculator.FUENTE_HORARIO_POTENCIA, r.fuente());
    assertEquals(1.5, r.horasSemana(), EPS);
    assertEquals(3.0, r.kwhSemana(), EPS);
    assertEquals(2.0, r.perfilSemanal()[0][18], EPS);
    assertEquals(1.0, r.perfilSemanal()[0][19], EPS);
    assertEquals(3.0 * EstimacionConsumoCalculator.DIAS_POR_MES / 7, r.kwhMes(), EPS);
  }

  @Test
  void franjaQueCruzaMedianocheContinuaAlDiaSiguiente() {
    // Domingo 23:00–01:00 → 1 h domingo + 1 h lunes
    double[][] m =
        EstimacionConsumoCalculator.minutosPorHora(
            List.of(new Franja(7, LocalTime.of(23, 0), LocalTime.of(1, 0))));
    assertEquals(60, m[6][23], EPS);
    assertEquals(60, m[0][0], EPS);
  }

  @Test
  void horarioSinPotenciaRepartePromedioDiario() {
    Resultado r =
        EstimacionConsumoCalculator.calcular(
            List.of(new Franja(3, LocalTime.of(8, 0), LocalTime.of(10, 0))), null, 1.0, null);
    assertEquals(EstimacionConsumoCalculator.FUENTE_HORARIO_CONSUMO, r.fuente());
    assertEquals(7.0, r.kwhSemana(), EPS);
    assertEquals(3.5, r.perfilSemanal()[2][8], EPS);
  }

  @Test
  void sinHorarioUsaPromedioDiario() {
    Resultado r = EstimacionConsumoCalculator.calcular(List.of(), null, 2.4, null);
    assertEquals(EstimacionConsumoCalculator.FUENTE_PROMEDIO_DIARIO, r.fuente());
    assertEquals(0.1, r.perfilSemanal()[4][13], EPS);
    assertEquals(2.4, r.kwhDia(), EPS);
  }

  @Test
  void ajusteDelUsuarioPrevaleceYConservaForma() {
    Resultado r =
        EstimacionConsumoCalculator.calcular(
            List.of(new Franja(1, LocalTime.of(18, 0), LocalTime.of(20, 0))), 1000.0, null, 50.0);
    assertEquals(EstimacionConsumoCalculator.FUENTE_AJUSTE_USUARIO, r.fuente());
    assertEquals(50.0, r.kwhMes(), EPS);
    assertEquals(r.perfilSemanal()[0][18], r.perfilSemanal()[0][19], EPS);
    assertEquals(50.0 * 7 / EstimacionConsumoCalculator.DIAS_POR_MES, r.kwhSemana(), EPS);
  }

  @Test
  void potenciaSinHorarioEsSiempreEncendido() {
    // 50 W las 24 h → 1,2 kWh/día
    Resultado r = EstimacionConsumoCalculator.calcular(List.of(), 50.0, 9.0, null);
    assertEquals(EstimacionConsumoCalculator.FUENTE_HORARIO_POTENCIA, r.fuente());
    assertEquals(168, r.horasSemana(), EPS);
    assertEquals(1.2, r.kwhDia(), EPS);
    assertEquals(1.2, EstimacionConsumoCalculator.kwhDiaPorHorario(List.of(), 50.0), EPS);
  }
}
