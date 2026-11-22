package com.harmoniwatts.electro.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.LocalTime;

/**
 * Franja de uso de un electrodoméstico en un día de la semana (HAR-20). Si {@code horaFin} es
 * menor o igual que {@code horaInicio}, la franja cruza la medianoche y continúa al día siguiente.
 */
@Entity
@Table(name = "electrodomestico_horario")
public class ElectrodomesticoHorario {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id_horario")
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY, optional = false)
  @JoinColumn(name = "id_electro", nullable = false)
  private Electrodomestico electrodomestico;

  /** ISO-8601: 1 = lunes … 7 = domingo. */
  @Column(name = "dia_semana", nullable = false)
  private Short diaSemana;

  @Column(name = "hora_inicio", nullable = false)
  private LocalTime horaInicio;

  @Column(name = "hora_fin", nullable = false)
  private LocalTime horaFin;

  public Long getId() {
    return id;
  }

  public Electrodomestico getElectrodomestico() {
    return electrodomestico;
  }

  public void setElectrodomestico(Electrodomestico electrodomestico) {
    this.electrodomestico = electrodomestico;
  }

  public int getDiaSemana() {
    return diaSemana;
  }

  public void setDiaSemana(int diaSemana) {
    this.diaSemana = (short) diaSemana;
  }

  public LocalTime getHoraInicio() {
    return horaInicio;
  }

  public void setHoraInicio(LocalTime horaInicio) {
    this.horaInicio = horaInicio;
  }

  public LocalTime getHoraFin() {
    return horaFin;
  }

  public void setHoraFin(LocalTime horaFin) {
    this.horaFin = horaFin;
  }
}
