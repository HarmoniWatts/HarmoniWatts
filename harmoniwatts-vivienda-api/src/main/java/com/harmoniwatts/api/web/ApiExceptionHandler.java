package com.harmoniwatts.api.web;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {

  /**
   * Ej.: idZona + codMercado que no existen en mercado_zona (vivienda o cliente), nivel de tensión,
   * comercializadora o tipo de cliente inexistentes.
   */
  @ExceptionHandler(DataIntegrityViolationException.class)
  ProblemDetail onDataIntegrity(DataIntegrityViolationException ex) {
    return ProblemDetail.forStatusAndDetail(
        HttpStatus.BAD_REQUEST,
        "Datos no válidos: verifique ciudad/mercado, nivel de tensión, comercializadora y tipo de cliente");
  }
}
