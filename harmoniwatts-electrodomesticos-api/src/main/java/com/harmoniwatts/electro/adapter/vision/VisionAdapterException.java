package com.harmoniwatts.electro.adapter.vision;

/** Error al invocar o interpretar un adaptador de visión. */
public class VisionAdapterException extends RuntimeException {

  public VisionAdapterException(String message) {
    super(message);
  }

  public VisionAdapterException(String message, Throwable cause) {
    super(message, cause);
  }
}
