package com.harmoniwatts.electro.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "electrodomestico_tipo_predefinido")
public class ElectrodomesticoTipoPredefinido {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Integer id;

  @Column(nullable = false, unique = true, length = 50)
  private String codigo;

  @Column(name = "nombre_es", nullable = false, length = 100)
  private String nombreEs;

  @Column(nullable = false)
  private short orden = 0;

  @Column(nullable = false)
  private boolean activo = true;

  public Integer getId() {
    return id;
  }

  public void setId(Integer id) {
    this.id = id;
  }

  public String getCodigo() {
    return codigo;
  }

  public void setCodigo(String codigo) {
    this.codigo = codigo;
  }

  public String getNombreEs() {
    return nombreEs;
  }

  public void setNombreEs(String nombreEs) {
    this.nombreEs = nombreEs;
  }

  public short getOrden() {
    return orden;
  }

  public void setOrden(short orden) {
    this.orden = orden;
  }

  public boolean isActivo() {
    return activo;
  }

  public void setActivo(boolean activo) {
    this.activo = activo;
  }
}
