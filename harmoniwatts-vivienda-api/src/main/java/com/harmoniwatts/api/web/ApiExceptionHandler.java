package com.harmoniwatts.api.web;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {

  /** Ej.: idZona + codMercado que no existen en mercado_zona (FK fk_vivienda_mercado_zona). */
  @ExceptionHandler(DataIntegrityViolationException.class)
  ProblemDetail onDataIntegrity(DataIntegrityViolationException ex) {
    return ProblemDetail.forStatusAndDetail(
        HttpStatus.BAD_REQUEST, "Ciudad o mercado no válidos para la vivienda");
  }
}
