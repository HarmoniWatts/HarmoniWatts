package com.harmoniwatts.electro.adapter.vision;

import com.harmoniwatts.electro.domain.vision.VisionRawResult;
import java.util.List;

/** Un proveedor concreto de visión (Gemini, OpenAI, Mistral, …). */
public interface VisionProviderAdapter {

  /** Identificador estable: gemini | openai | mistral | ollama */
  String providerId();

  /** false si falta API key (o URL) — se omite en la cadena. */
  boolean isConfigured();

  VisionRawResult analyze(
      byte[] imageBytes, String mimeType, List<String> tipoCodigos, List<String> marcaNombres);
}
