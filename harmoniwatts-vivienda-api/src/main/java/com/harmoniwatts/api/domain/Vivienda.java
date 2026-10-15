package com.harmoniwatts.api.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "vivienda")
public class Vivienda {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id_vivienda")
  private Long id;

  /** Valor = `sub` del JWT de Keycloak; columna física en BD: `id_usuario`. */
  @Column(name = "id_usuario", nullable = false, length = 36)
  private String keycloakUserId;

  @Column(nullable = false, length = 50)
  private String tipo;

  @Column private Integer habitantes;

  @Column(length = 200)
  private String direccion;

  /** Estrato socioeconómico (1–6, Colombia). */
  @Column(nullable = false)
  private Integer estrato = 3;

  @Column(name = "zona_climatica", length = 20)
  private String zonaClimatica;

  @Column(name = "fecha_registro", nullable = false)
  private Instant fechaRegistro = Instant.now();

  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }

  public String getKeycloakUserId() {
    return keycloakUserId;
  }

  public void setKeycloakUserId(String keycloakUserId) {
    this.keycloakUserId = keycloakUserId;
  }

  public String getTipo() {
    return tipo;
  }

  public void setTipo(String tipo) {
    this.tipo = tipo;
  }

  public Integer getHabitantes() {
    return habitantes;
  }

  public void setHabitantes(Integer habitantes) {
    this.habitantes = habitantes;
  }

  public String getDireccion() {
    return direccion;
  }

  public void setDireccion(String direccion) {
    this.direccion = direccion;
  }

  public Integer getEstrato() {
    return estrato;
  }

  public void setEstrato(Integer estrato) {
    this.estrato = estrato;
  }

  public String getZonaClimatica() {
    return zonaClimatica;
  }

  public void setZonaClimatica(String zonaClimatica) {
    this.zonaClimatica = zonaClimatica;
  }

  public Instant getFechaRegistro() {
    return fechaRegistro;
  }

  public void setFechaRegistro(Instant fechaRegistro) {
    this.fechaRegistro = fechaRegistro;
  }
}
