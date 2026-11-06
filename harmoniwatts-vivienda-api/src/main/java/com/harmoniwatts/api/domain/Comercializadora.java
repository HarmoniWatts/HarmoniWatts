package com.harmoniwatts.api.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** Catálogo de comercializadoras de energía (solo lectura desde esta API). */
@Entity
@Table(name = "comercializadora")
public class Comercializadora {

  @Id
  @Column(name = "cod_comercializadora", length = 20)
  private String codigo;

  @Column(nullable = false, length = 100)
  private String nombre;

  @Column private Boolean activo;

  public String getCodigo() {
    return codigo;
  }

  public String getNombre() {
    return nombre;
  }

  public Boolean getActivo() {
    return activo;
  }
}
