package com.harmoniwatts.electro.adapter.vision;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import com.harmoniwatts.electro.domain.vision.VisionRawResult;
import java.util.List;
import org.junit.jupiter.api.Test;

class VisionTextFallbackTest {

  @Test
  void leePotenciaEnWattsYkW() {
    assertEquals(1200.0, VisionTextFallback.detectPotenciaW("120V~ 60Hz 1200W"));
    assertEquals(1500.0, VisionTextFallback.detectPotenciaW("Potencia: 1,5 kW"));
    assertEquals(1200.0, VisionTextFallback.detectPotenciaW("Potencia nominal 1.200 vatios"));
    // La mayor cuando hay varias (lavado / secado)
    assertEquals(2000.0, VisionTextFallback.detectPotenciaW("Lavado 500 W  Secado 2000 W"));
  }

  @Test
  void noConfundeKwhConPotencia() {
    assertNull(VisionTextFallback.detectPotenciaW("Consumo 35 kWh/mes"));
  }

  @Test
  void consumoMensualDesdeEtiqueta() {
    assertEquals(35.0, VisionTextFallback.estimateConsumoKwhMes("Consumo de energía 35 kWh/mes"));
    assertEquals(30.0, VisionTextFallback.estimateConsumoKwhMes("360 kWh/año"));
    assertEquals(30.0, VisionTextFallback.estimateConsumoKwhMes("1 kWh/día"));
  }

  @Test
  void lineasEstructuradas() {
    VisionRawResult r =
        VisionTextFallback.parseFreeText(
            "Marca: Haceb\nTipo: Nevera\nPotenciaW: 150 W\nConsumoKwhMes: 32", List.of("NEVERA"));
    assertEquals("Haceb", r.marcaDetectada());
    assertEquals(150.0, r.potenciaW());
    assertEquals(32.0, r.consumoKwhMes());
  }
}
