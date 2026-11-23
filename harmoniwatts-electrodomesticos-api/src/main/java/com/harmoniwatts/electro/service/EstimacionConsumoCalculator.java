package com.harmoniwatts.electro.service;

import java.time.LocalTime;
import java.util.List;

/**
 * Cálculo programático del consumo de un electrodoméstico (HAR-20).
 *
 * <p>Se construye un perfil de una semana típica: kWh por [día 0–6 (lunes–domingo)][hora 0–23].
 * Prioridad de la fuente:
 *
 * <ol>
 *   <li><b>HORARIO_POTENCIA</b>: hay potencia → kWh = horas de uso × W / 1000. Sin franjas el
 *       electrodoméstico está <i>siempre encendido</i> (168 h/semana).
 *   <li><b>HORARIO_CONSUMO</b>: hay franjas sin potencia → el promedio diario (kWh/día × 7) se
 *       reparte proporcionalmente a los minutos de uso de la semana.
 *   <li><b>PROMEDIO_DIARIO</b>: sin franjas ni potencia (registros antiguos) → kWh/día repartido
 *       uniformemente en las 24 h.
 * </ol>
 *
 * Si el usuario indicó un consumo mensual ajustado (<b>AJUSTE_USUARIO</b>) el perfil se escala para
 * que el total mensual coincida con ese valor, conservando la forma horaria.
 */
public final class EstimacionConsumoCalculator {

  /** Días promedio por mes (365.25 / 12). */
  public static final double DIAS_POR_MES = 30.4375;

  public static final String FUENTE_HORARIO_POTENCIA = "HORARIO_POTENCIA";
  public static final String FUENTE_HORARIO_CONSUMO = "HORARIO_CONSUMO";
  public static final String FUENTE_PROMEDIO_DIARIO = "PROMEDIO_DIARIO";
  public static final String FUENTE_AJUSTE_USUARIO = "AJUSTE_USUARIO";

  private static final int MIN_DIA = 24 * 60;

  private EstimacionConsumoCalculator() {}

  /** Franja de uso: día ISO 1–7 y horas locales. */
  public record Franja(int diaSemana, LocalTime inicio, LocalTime fin) {}

  public record Resultado(
      String fuente,
      double horasSemana,
      double kwhSemana,
      double kwhMesCalculado,
      double kwhMes,
      double[][] perfilSemanal) {

    public double kwhDia() {
      return kwhMes / DIAS_POR_MES;
    }
  }

  public static Resultado calcular(
      List<Franja> franjas, Double potenciaW, Double consumoKwhDia, Double ajusteKwhMes) {
    boolean hayPotencia = potenciaW != null && potenciaW > 0;
    double[][] minutos = minutosPorHora(franjas);
    if (suma(minutos) == 0 && hayPotencia) {
      minutos = siempreEncendido();
    }
    double minutosSemana = suma(minutos);
    double[][] perfil = new double[7][24];
    String fuente;

    if (minutosSemana > 0 && hayPotencia) {
      fuente = FUENTE_HORARIO_POTENCIA;
      double kwPorMinuto = potenciaW / 1000.0 / 60.0;
      for (int d = 0; d < 7; d++) {
        for (int h = 0; h < 24; h++) {
          perfil[d][h] = minutos[d][h] * kwPorMinuto;
        }
      }
    } else if (minutosSemana > 0) {
      fuente = FUENTE_HORARIO_CONSUMO;
      double semana = nz(consumoKwhDia) * 7.0;
      for (int d = 0; d < 7; d++) {
        for (int h = 0; h < 24; h++) {
          perfil[d][h] = semana * minutos[d][h] / minutosSemana;
        }
      }
    } else {
      fuente = FUENTE_PROMEDIO_DIARIO;
      double porHora = nz(consumoKwhDia) / 24.0;
      for (int d = 0; d < 7; d++) {
        for (int h = 0; h < 24; h++) {
          perfil[d][h] = porHora;
        }
      }
    }

    double kwhSemanaCalc = suma(perfil);
    double kwhMesCalc = kwhSemanaCalc * DIAS_POR_MES / 7.0;
    double kwhMes = kwhMesCalc;

    if (ajusteKwhMes != null && ajusteKwhMes >= 0) {
      fuente = FUENTE_AJUSTE_USUARIO;
      kwhMes = ajusteKwhMes;
      double objetivoSemana = ajusteKwhMes * 7.0 / DIAS_POR_MES;
      if (kwhSemanaCalc > 0) {
        escalar(perfil, objetivoSemana / kwhSemanaCalc);
      } else {
        // Sin forma previa: reparto uniforme
        double porHora = objetivoSemana / (7 * 24);
        for (double[] dia : perfil) {
          java.util.Arrays.fill(dia, porHora);
        }
      }
    }

    return new Resultado(
        fuente,
        minutosSemana / 60.0,
        suma(perfil),
        kwhMesCalc,
        kwhMes,
        perfil);
  }

  /**
   * kWh/día equivalente a usar {@code potenciaW} en las franjas dadas; sin franjas, siempre
   * encendido (para sincronizar {@code consumo_kwh_dia}).
   */
  public static double kwhDiaPorHorario(List<Franja> franjas, double potenciaW) {
    double minutos = suma(minutosPorHora(franjas));
    if (minutos == 0) {
      minutos = 7 * MIN_DIA;
    }
    return minutos / 60.0 * potenciaW / 1000.0 / 7.0;
  }

  private static double[][] siempreEncendido() {
    double[][] m = new double[7][24];
    for (double[] dia : m) {
      java.util.Arrays.fill(dia, 60);
    }
    return m;
  }

  /** Minutos de uso en cada [día][hora]; las franjas que cruzan la medianoche siguen al día siguiente. */
  static double[][] minutosPorHora(List<Franja> franjas) {
    double[][] m = new double[7][24];
    if (franjas == null) {
      return m;
    }
    for (Franja f : franjas) {
      int dia = f.diaSemana() - 1;
      int ini = f.inicio().getHour() * 60 + f.inicio().getMinute();
      int fin = f.fin().getHour() * 60 + f.fin().getMinute();
      int dur = fin > ini ? fin - ini : fin - ini + MIN_DIA; // igual → 24 h
      for (int t = ini; t < ini + dur; ) {
        int minDelDia = t % MIN_DIA;
        int d = (dia + t / MIN_DIA) % 7;
        int h = minDelDia / 60;
        int hastaFinHora = 60 - (minDelDia % 60);
        int paso = Math.min(hastaFinHora, ini + dur - t);
        m[d][h] = Math.min(60, m[d][h] + paso); // franjas solapadas no cuentan doble
        t += paso;
      }
    }
    return m;
  }

  private static double suma(double[][] x) {
    double s = 0;
    for (double[] fila : x) {
      for (double v : fila) {
        s += v;
      }
    }
    return s;
  }

  private static void escalar(double[][] x, double factor) {
    for (double[] fila : x) {
      for (int i = 0; i < fila.length; i++) {
        fila[i] *= factor;
      }
    }
  }

  private static double nz(Double v) {
    return v == null || v < 0 ? 0 : v;
  }
}
