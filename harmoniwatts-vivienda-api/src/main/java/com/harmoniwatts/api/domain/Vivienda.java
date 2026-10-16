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

  /** Municipio (zona_geografica); junto con codMercado debe existir en mercado_zona. */
  @Column(name = "id_zona")
  private Short idZona;

  /** Mercado de comercialización: con el estrato define la tarifa de la vivienda. */
  @Column(name = "cod_mercado", length = 30)
  private String codMercado;

  /** Número de contrato / cuenta con la comercializadora. */
  @Column(name = "numero_contrato", length = 30)
  private String numeroContrato;

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

  public Short getIdZona() {
    return idZona;
  }

  public void setIdZona(Short idZona) {
    this.idZona = idZona;
  }

  public String getCodMercado() {
    return codMercado;
  }

  public void setCodMercado(String codMercado) {
    this.codMercado = codMercado;
  }

  public String getNumeroContrato() {
    return numeroContrato;
  }

  public void setNumeroContrato(String numeroContrato) {
    this.numeroContrato = numeroContrato;
  }

  public Instant getFechaRegistro() {
    return fechaRegistro;
  }

  public void setFechaRegistro(Instant fechaRegistro) {
    this.fechaRegistro = fechaRegistro;
  }
}
