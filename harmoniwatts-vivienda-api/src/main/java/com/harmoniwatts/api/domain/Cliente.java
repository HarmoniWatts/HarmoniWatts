package com.harmoniwatts.api.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "cliente")
public class Cliente {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id_cliente")
  private Long id;

  @Column(nullable = false, length = 100)
  private String nombre;

  /** Número de contrato con la comercializadora (único junto con codComercializadora). */
  @Column(name = "no_contrato", nullable = false, length = 50)
  private String noContrato;

  /** Debe coincidir con el claim `email` del JWT de Keycloak; es único. */
  @Column(nullable = false, length = 100, unique = true)
  private String email;

  /** La autenticación la maneja Keycloak; la columna es NOT NULL, por eso lleva un valor fijo. */
  @Column(name = "password_hash", nullable = false, length = 255)
  private String passwordHash = "{keycloak}";

  @Column(length = 20)
  private String telefono;

  @Column(name = "cod_tipo_cliente", nullable = false, length = 1)
  private String codTipoCliente;

  /** Solo aplica (y es obligatorio) para clientes residenciales 'R'. */
  @Column private Short estrato;

  @Column(name = "cod_nivel", nullable = false, length = 15)
  private String codNivel;

  @Column(name = "id_zona", nullable = false)
  private Short idZona;

  @Column(name = "cod_mercado", nullable = false, length = 30)
  private String codMercado;

  @Column(name = "cod_comercializadora", nullable = false, length = 20)
  private String codComercializadora;

  /** Calculado por el trigger de la BD: solo lectura desde la API. */
  @Column(name = "cs_kwh_mes", insertable = false, updatable = false)
  private BigDecimal csKwhMes;

  @Column(name = "fecha_registro", nullable = false, updatable = false)
  private Instant fechaRegistro = Instant.now();

  @Column(name = "ultimo_acceso")
  private Instant ultimoAcceso;

  @Column(nullable = false)
  private Boolean activo = true;

  public Long getId() { return id; }
  public void setId(Long id) { this.id = id; }
  public String getNombre() { return nombre; }
  public void setNombre(String nombre) { this.nombre = nombre; }
  public String getNoContrato() { return noContrato; }
  public void setNoContrato(String noContrato) { this.noContrato = noContrato; }
  public String getEmail() { return email; }
  public void setEmail(String email) { this.email = email; }
  public String getPasswordHash() { return passwordHash; }
  public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }
  public String getTelefono() { return telefono; }
  public void setTelefono(String telefono) { this.telefono = telefono; }
  public String getCodTipoCliente() { return codTipoCliente; }
  public void setCodTipoCliente(String codTipoCliente) { this.codTipoCliente = codTipoCliente; }
  public Short getEstrato() { return estrato; }
  public void setEstrato(Short estrato) { this.estrato = estrato; }
  public String getCodNivel() { return codNivel; }
  public void setCodNivel(String codNivel) { this.codNivel = codNivel; }
  public Short getIdZona() { return idZona; }
  public void setIdZona(Short idZona) { this.idZona = idZona; }
  public String getCodMercado() { return codMercado; }
  public void setCodMercado(String codMercado) { this.codMercado = codMercado; }
  public String getCodComercializadora() { return codComercializadora; }
  public void setCodComercializadora(String c) { this.codComercializadora = c; }
  public BigDecimal getCsKwhMes() { return csKwhMes; }
  public Instant getFechaRegistro() { return fechaRegistro; }
  public void setFechaRegistro(Instant fechaRegistro) { this.fechaRegistro = fechaRegistro; }
  public Instant getUltimoAcceso() { return ultimoAcceso; }
  public void setUltimoAcceso(Instant ultimoAcceso) { this.ultimoAcceso = ultimoAcceso; }
  public Boolean getActivo() { return activo; }
  public void setActivo(Boolean activo) { this.activo = activo; }
}
