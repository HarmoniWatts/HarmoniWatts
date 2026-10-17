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

@Entity
@Table(name = "electrodomestico")
public class Electrodomestico {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id_electro")
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY, optional = false)
  @JoinColumn(name = "id_vivienda", nullable = false)
  private Vivienda vivienda;

  @ManyToOne(fetch = FetchType.EAGER, optional = false)
  @JoinColumn(name = "id_tipo_predefinido", nullable = false)
  private ElectrodomesticoTipoPredefinido tipoPredefinido;

  @ManyToOne(fetch = FetchType.EAGER)
  @JoinColumn(name = "id_marca_predefinida")
  private MarcaPredefinida marcaPredefinida;

  @Column(name = "marca_otro", length = 100)
  private String marcaOtro;

  @Column(nullable = false, length = 100)
  private String nombre;

  @Column(nullable = false, length = 50)
  private String tipo;

  @Column(name = "consumo_kwh_dia", nullable = false, precision = 10, scale = 4)
  private java.math.BigDecimal consumoKwhDia;

  @Column(name = "es_desplazable", nullable = false)
  private Boolean desplazable = Boolean.FALSE;

  @Column(name = "uso_semanal")
  private Integer usoSemanal;

  /** Preferencia u horario típico de uso (columna BD: horario_habitual, tipo TIME). */
  @Column(name = "horario_habitual")
  private LocalTime horarioHabitual;

  @Column private Boolean activo = Boolean.TRUE;

  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }

  public Vivienda getVivienda() {
    return vivienda;
  }

  public void setVivienda(Vivienda vivienda) {
    this.vivienda = vivienda;
  }

  public ElectrodomesticoTipoPredefinido getTipoPredefinido() {
    return tipoPredefinido;
  }

  public void setTipoPredefinido(ElectrodomesticoTipoPredefinido tipoPredefinido) {
    this.tipoPredefinido = tipoPredefinido;
  }

  public MarcaPredefinida getMarcaPredefinida() {
    return marcaPredefinida;
  }

  public void setMarcaPredefinida(MarcaPredefinida marcaPredefinida) {
    this.marcaPredefinida = marcaPredefinida;
  }

  public String getMarcaOtro() {
    return marcaOtro;
  }

  public void setMarcaOtro(String marcaOtro) {
    this.marcaOtro = marcaOtro;
  }

  public String getNombre() {
    return nombre;
  }

  public void setNombre(String nombre) {
    this.nombre = nombre;
  }

  public String getTipo() {
    return tipo;
  }

  public void setTipo(String tipo) {
    this.tipo = tipo;
  }

  public Double getConsumoKwhDia() {
    return consumoKwhDia == null ? null : consumoKwhDia.doubleValue();
  }

  public void setConsumoKwhDia(Double consumoKwhDia) {
    this.consumoKwhDia =
        consumoKwhDia == null ? null : java.math.BigDecimal.valueOf(consumoKwhDia);
  }

  public void setConsumoKwhDia(java.math.BigDecimal consumoKwhDia) {
    this.consumoKwhDia = consumoKwhDia;
  }

  public Boolean getDesplazable() {
    return desplazable;
  }

  public void setDesplazable(Boolean desplazable) {
    this.desplazable = desplazable;
  }

  public Integer getUsoSemanal() {
    return usoSemanal;
  }

  public void setUsoSemanal(Integer usoSemanal) {
    this.usoSemanal = usoSemanal;
  }

  public LocalTime getHorarioHabitual() {
    return horarioHabitual;
  }

  public void setHorarioHabitual(LocalTime horarioHabitual) {
    this.horarioHabitual = horarioHabitual;
  }

  public Boolean getActivo() {
    return activo;
  }

  public void setActivo(Boolean activo) {
    this.activo = activo;
  }
}
