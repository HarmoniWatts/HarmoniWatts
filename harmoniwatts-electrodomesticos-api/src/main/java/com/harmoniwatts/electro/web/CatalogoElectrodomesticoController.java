package com.harmoniwatts.electro.web;

import com.harmoniwatts.electro.service.ElectrodomesticoCatalogoService;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.CatalogosResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/electrodomesticos/catalogos")
public class CatalogoElectrodomesticoController {

  private final ElectrodomesticoCatalogoService catalogoService;

  public CatalogoElectrodomesticoController(ElectrodomesticoCatalogoService catalogoService) {
    this.catalogoService = catalogoService;
  }

  @GetMapping
  public CatalogosResponse listar() {
    return catalogoService.listarActivos();
  }
}
