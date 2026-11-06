package com.harmoniwatts.api.web;

import com.harmoniwatts.api.repo.ComercializadoraRepository;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Comercializadoras activas, para elegir con cuál tiene contrato cada vivienda. */
@RestController
@RequestMapping("/api/v1/comercializadoras")
public class ComercializadoraController {

  public record ComercializadoraResponse(String codigo, String nombre) {}

  private final ComercializadoraRepository repository;

  public ComercializadoraController(ComercializadoraRepository repository) {
    this.repository = repository;
  }

  @GetMapping
  public List<ComercializadoraResponse> list() {
    return repository.findByActivoTrueOrderByNombreAsc().stream()
        .map(c -> new ComercializadoraResponse(c.getCodigo(), c.getNombre()))
        .toList();
  }
}
