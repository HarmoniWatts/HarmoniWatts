package com.harmoniwatts.api.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.JwtValidators;
import org.springframework.security.oauth2.jwt.NimbusJwtDecoder;

/**
 * El {@code iss} del JWT coincide con la URL pública de Keycloak (p. ej. {@code localhost:8080}),
 * pero dentro de Docker la API debe obtener las claves JWK desde el hostname de red ({@code keycloak:8080}).
 */
@Configuration
public class JwtDecoderConfig {

  @Bean
  JwtDecoder jwtDecoder(
      @Value("${harmoniwatts.oauth2.issuer-uri}") String issuerUri,
      @Value("${harmoniwatts.oauth2.jwk-set-uri}") String jwkSetUri) {
    NimbusJwtDecoder decoder = NimbusJwtDecoder.withJwkSetUri(jwkSetUri).build();
    decoder.setJwtValidator(JwtValidators.createDefaultWithIssuer(issuerUri));
    return decoder;
  }
}
