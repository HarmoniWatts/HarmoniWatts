package com.harmoniwatts.electro.service;

import com.harmoniwatts.electro.domain.Electrodomestico;
import com.harmoniwatts.electro.domain.ElectrodomesticoTipoPredefinido;
import com.harmoniwatts.electro.domain.MarcaPredefinida;
import com.harmoniwatts.electro.domain.Vivienda;
import com.harmoniwatts.electro.repo.ElectrodomesticoRepository;
import com.harmoniwatts.electro.repo.ElectrodomesticoTipoPredefinidoRepository;
import com.harmoniwatts.electro.repo.MarcaPredefinidaRepository;
import com.harmoniwatts.electro.repo.ViviendaRepository;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.ElectrodomesticoCreateRequest;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.ElectrodomesticoResponse;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.ElectrodomesticoUpdateRequest;
import java.time.LocalTime;
import java.time.format.DateTimeParseException;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class ElectrodomesticoCrudService {

  public static final String CODIGO_TIPO_OTRO = "OTRO";
  private static final String NOMBRE_MARCA_OTRO = "Otro";

  private final ViviendaRepository viviendaRepository;
  private final ElectrodomesticoRepository electroRepository;
  private final ElectrodomesticoTipoPredefinidoRepository tipoRepository;
  private final MarcaPredefinidaRepository marcaRepository;

  public ElectrodomesticoCrudService(
      ViviendaRepository viviendaRepository,
      ElectrodomesticoRepository electroRepository,
      ElectrodomesticoTipoPredefinidoRepository tipoRepository,
      MarcaPredefinidaRepository marcaRepository) {
    this.viviendaRepository = viviendaRepository;
    this.electroRepository = electroRepository;
    this.tipoRepository = tipoRepository;
    this.marcaRepository = marcaRepository;
  }

  @Transactional(readOnly = true)
  public List<ElectrodomesticoResponse> listar(String keycloakSub, long idVivienda) {
    assertViviendaPropia(keycloakSub, idVivienda);
    return electroRepository.findAllForViviendaAndOwner(idVivienda, keycloakSub).stream()
        .map(e -> ElectrodomesticoResponse.from(e, idVivienda))
        .toList();
  }

  @Transactional
  public ElectrodomesticoResponse crear(String keycloakSub, long idVivienda, ElectrodomesticoCreateRequest body) {
    Vivienda vivienda = assertViviendaPropia(keycloakSub, idVivienda);
    ElectrodomesticoTipoPredefinido tipo = loadTipoActivo(body.idTipoPredefinido());
    MarcaPredefinida marca = resolveMarca(body.idMarcaPredefinida());
    validarMarcaOtro(marca, body.marcaOtro());
    String nombre = resolveNombre(body.nombre(), tipo);
    validarTipoOtro(tipo, nombre);

    Electrodomestico e = new Electrodomestico();
    e.setVivienda(vivienda);
    applyCommonFields(e, tipo, marca, body.marcaOtro(), nombre, body);
    Electrodomestico saved = electroRepository.save(e);
    return ElectrodomesticoResponse.from(saved, idVivienda);
  }

  @Transactional
  public ElectrodomesticoResponse actualizar(
      String keycloakSub, long idVivienda, long idElectro, ElectrodomesticoUpdateRequest body) {
    assertViviendaPropia(keycloakSub, idVivienda);
    Electrodomestico e =
        electroRepository
            .findByIdAndViviendaAndOwner(idElectro, idVivienda, keycloakSub)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));

    ElectrodomesticoTipoPredefinido tipo = loadTipoActivo(body.idTipoPredefinido());
    MarcaPredefinida marca = resolveMarca(body.idMarcaPredefinida());
    validarMarcaOtro(marca, body.marcaOtro());
    String nombre = resolveNombre(body.nombre(), tipo);
    validarTipoOtro(tipo, nombre);

    applyCommonFields(e, tipo, marca, body.marcaOtro(), nombre, body);
    if (body.activo() != null) {
      e.setActivo(body.activo());
    }
    Electrodomestico saved = electroRepository.save(e);
    return ElectrodomesticoResponse.from(saved, idVivienda);
  }

  @Transactional
  public void eliminar(String keycloakSub, long idVivienda, long idElectro) {
    assertViviendaPropia(keycloakSub, idVivienda);
    Electrodomestico e =
        electroRepository
            .findByIdAndViviendaAndOwner(idElectro, idVivienda, keycloakSub)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    electroRepository.delete(e);
  }

  private Vivienda assertViviendaPropia(String keycloakSub, long idVivienda) {
    return viviendaRepository
        .findByIdAndKeycloakUserId(idVivienda, keycloakSub)
        .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Vivienda no encontrada"));
  }

  private ElectrodomesticoTipoPredefinido loadTipoActivo(int idTipo) {
    return tipoRepository
        .findByIdAndActivoTrue(idTipo)
        .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "Tipo de electrodoméstico inválido"));
  }

  private MarcaPredefinida resolveMarca(Integer idMarca) {
    if (idMarca == null) {
      return null;
    }
    return marcaRepository
        .findByIdAndActivoTrue(idMarca)
        .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "Marca inválida"));
  }

  private void validarMarcaOtro(MarcaPredefinida marca, String marcaOtro) {
    if (marca == null) {
      return;
    }
    if (NOMBRE_MARCA_OTRO.equalsIgnoreCase(marca.getNombre().trim())) {
      if (marcaOtro == null || marcaOtro.isBlank()) {
        throw new ResponseStatusException(
            HttpStatus.BAD_REQUEST, "Indica la marca en texto cuando eliges «Otro».");
      }
    }
  }

  private void validarTipoOtro(ElectrodomesticoTipoPredefinido tipo, String nombre) {
    if (CODIGO_TIPO_OTRO.equalsIgnoreCase(tipo.getCodigo())) {
      if (nombre == null || nombre.isBlank()) {
        throw new ResponseStatusException(
            HttpStatus.BAD_REQUEST, "El nombre del electrodoméstico es obligatorio para el tipo «Otro».");
      }
    }
  }

  private static String resolveNombre(String nombreSolicitado, ElectrodomesticoTipoPredefinido tipo) {
    if (nombreSolicitado != null && !nombreSolicitado.isBlank()) {
      return nombreSolicitado.trim();
    }
    return tipo.getNombreEs();
  }

  private void applyCommonFields(
      Electrodomestico e,
      ElectrodomesticoTipoPredefinido tipo,
      MarcaPredefinida marca,
      String marcaOtro,
      String nombre,
      ElectrodomesticoCreateRequest body) {
    e.setTipoPredefinido(tipo);
    e.setTipo(tipo.getCodigo());
    e.setNombre(nombre);
    e.setPotenciaW(body.potenciaW());
    e.setUsoSemanal(body.usoSemanal());
    e.setHorarioHabitual(parseHorarioHabitual(body.horarioHabitual()));
    e.setDesplazable(Boolean.TRUE.equals(body.esDesplazable()));
    e.setMarcaPredefinida(marca);
    if (marca != null && NOMBRE_MARCA_OTRO.equalsIgnoreCase(marca.getNombre().trim())) {
      e.setMarcaOtro(marcaOtro != null ? marcaOtro.trim() : null);
    } else {
      e.setMarcaOtro(null);
    }
  }

  private void applyCommonFields(
      Electrodomestico e,
      ElectrodomesticoTipoPredefinido tipo,
      MarcaPredefinida marca,
      String marcaOtro,
      String nombre,
      ElectrodomesticoUpdateRequest body) {
    e.setTipoPredefinido(tipo);
    e.setTipo(tipo.getCodigo());
    e.setNombre(nombre);
    e.setPotenciaW(body.potenciaW());
    e.setUsoSemanal(body.usoSemanal());
    e.setHorarioHabitual(parseHorarioHabitual(body.horarioHabitual()));
    e.setDesplazable(Boolean.TRUE.equals(body.esDesplazable()));
    e.setMarcaPredefinida(marca);
    if (marca != null && NOMBRE_MARCA_OTRO.equalsIgnoreCase(marca.getNombre().trim())) {
      e.setMarcaOtro(marcaOtro != null ? marcaOtro.trim() : null);
    } else {
      e.setMarcaOtro(null);
    }
  }

  private static LocalTime parseHorarioHabitual(String raw) {
    if (raw == null || raw.isBlank()) {
      return null;
    }
    String s = raw.trim();
    try {
      return LocalTime.parse(s);
    } catch (DateTimeParseException ex) {
      throw new ResponseStatusException(
          HttpStatus.BAD_REQUEST, "horarioHabitual inválido; use formato HH:mm o HH:mm:ss.");
    }
  }
}
