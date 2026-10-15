package com.harmoniwatts.electro.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** Vista mínima de la vivienda para comprobar propiedad (id_usuario = sub JWT). */
@Entity
@Table(name = "vivienda")
public class Vivienda {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id_vivienda")
  private Long id;

  @Column(name = "id_usuario", nullable = false, length = 36)
  private String keycloakUserId;

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
}
