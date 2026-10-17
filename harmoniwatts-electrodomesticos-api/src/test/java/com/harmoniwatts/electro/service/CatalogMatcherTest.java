package com.harmoniwatts.electro.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.harmoniwatts.electro.service.CatalogMatcher.MarcaMatch;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.MarcaCatalogoItem;
import com.harmoniwatts.electro.web.dto.ElectrodomesticoDtos.TipoCatalogoItem;
import java.util.List;
import org.junit.jupiter.api.Test;

class CatalogMatcherTest {

  private final CatalogMatcher matcher = new CatalogMatcher();

  private final List<TipoCatalogoItem> tipos =
      List.of(
          new TipoCatalogoItem(1, "NEVERA", "Nevera", (short) 1, true),
          new TipoCatalogoItem(2, "LAVADORA", "Lavadora", (short) 2, true),
          new TipoCatalogoItem(3, "AIRE_ACONDICIONADO", "Aire acondicionado", (short) 3, true));

  private final List<MarcaCatalogoItem> marcas =
      List.of(
          new MarcaCatalogoItem(10, "Samsung", (short) 1, true),
          new MarcaCatalogoItem(11, "LG", (short) 2, true),
          new MarcaCatalogoItem(99, "Otro", (short) 99, true));

  @Test
  void matchTipoUsaAliasEnIngles() {
    assertThat(matcher.matchTipo("Refrigerator", tipos)).get().extracting(TipoCatalogoItem::id).isEqualTo(1);
    assertThat(matcher.matchTipo("air conditioner", tipos)).get().extracting(TipoCatalogoItem::id).isEqualTo(3);
  }

  @Test
  void matchTipoIgnoraMayusculasYTildes() {
    assertThat(matcher.matchTipo("  lavadóra ", tipos)).get().extracting(TipoCatalogoItem::id).isEqualTo(2);
  }

  @Test
  void matchTipoVacioONuloNoCoincide() {
    assertThat(matcher.matchTipo(null, tipos)).isEmpty();
    assertThat(matcher.matchTipo("   ", tipos)).isEmpty();
  }

  @Test
  void matchMarcaExacta() {
    assertThat(matcher.matchMarca("SAMSUNG", marcas)).isEqualTo(new MarcaMatch(10, null, false));
  }

  @Test
  void matchMarcaToleraErroresDeTipeo() {
    assertThat(matcher.matchMarca("Samsumg", marcas)).isEqualTo(new MarcaMatch(10, null, false));
  }

  @Test
  void matchMarcaDesconocidaCaeEnOtroConTextoLibre() {
    assertThat(matcher.matchMarca(" Electrolux ", marcas)).isEqualTo(new MarcaMatch(99, "Electrolux", true));
  }

  @Test
  void matchMarcaSinCatalogoOtroDevuelveSoloTexto() {
    List<MarcaCatalogoItem> sinOtro = marcas.subList(0, 2);
    assertThat(matcher.matchMarca("Electrolux", sinOtro)).isEqualTo(new MarcaMatch(null, "Electrolux", true));
  }
}
