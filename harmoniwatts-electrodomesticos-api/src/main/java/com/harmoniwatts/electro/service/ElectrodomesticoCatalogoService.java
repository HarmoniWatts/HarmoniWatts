package com.harmoniwatts.electro.service;

import com.harmoniwatts.electro.repo.ElectrodomesticoTipoPredefinidoRepository;
import com.harmoniwatts.electro.repo.MarcaPredefinidaRepository;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.CatalogosResponse;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.MarcaCatalogoItem;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.TipoCatalogoItem;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Catálogos de tipos y marcas (solo lectura). */
@Service
public class ElectrodomesticoCatalogoService {

  private final ElectrodomesticoTipoPredefinidoRepository tipoRepository;
  private final MarcaPredefinidaRepository marcaRepository;

  public ElectrodomesticoCatalogoService(
      ElectrodomesticoTipoPredefinidoRepository tipoRepository,
      MarcaPredefinidaRepository marcaRepository) {
    this.tipoRepository = tipoRepository;
    this.marcaRepository = marcaRepository;
  }

  @Transactional(readOnly = true)
  public CatalogosResponse listarActivos() {
    List<TipoCatalogoItem> tipos =
        tipoRepository.findByActivoTrueOrderByOrdenAsc().stream()
            .map(t -> new TipoCatalogoItem(t.getId(), t.getCodigo(), t.getNombreEs(), t.getOrden(), t.isActivo()))
            .toList();
    List<MarcaCatalogoItem> marcas =
        marcaRepository.findByActivoTrueOrderByOrdenAsc().stream()
            .map(m -> new MarcaCatalogoItem(m.getId(), m.getNombre(), m.getOrden(), m.isActivo()))
            .toList();
    return new CatalogosResponse(tipos, marcas);
  }
}
