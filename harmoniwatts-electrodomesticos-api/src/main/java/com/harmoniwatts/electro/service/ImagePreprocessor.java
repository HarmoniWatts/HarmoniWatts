package com.harmoniwatts.electro.service;

import com.harmoniwatts.electro.config.VisionProperties;
import java.awt.Graphics2D;
import java.awt.Image;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import javax.imageio.ImageIO;
import org.springframework.stereotype.Component;

/** Redimensiona imágenes antes de enviarlas al modelo (reduce tokens visuales). */
@Component
public class ImagePreprocessor {

  private final VisionProperties properties;

  public ImagePreprocessor(VisionProperties properties) {
    this.properties = properties;
  }

  /**
   * Escala la imagen manteniendo proporción; el lado largo no supera {@code maxImageLongSide}.
   * Devuelve JPEG para uniformidad.
   */
  public ProcessedImage preprocess(byte[] input, String mimeType) {
    try {
      var buffered = ImageIO.read(new ByteArrayInputStream(input));
      if (buffered == null) {
        throw new IllegalArgumentException("No se pudo leer la imagen. Usa JPEG o PNG.");
      }
      int maxSide = properties.getMaxImageLongSide();
      int w = buffered.getWidth();
      int h = buffered.getHeight();
      int longSide = Math.max(w, h);
      if (longSide > maxSide) {
        double scale = (double) maxSide / longSide;
        int nw = Math.max(1, (int) Math.round(w * scale));
        int nh = Math.max(1, (int) Math.round(h * scale));
        Image scaled = buffered.getScaledInstance(nw, nh, Image.SCALE_SMOOTH);
        var out = new java.awt.image.BufferedImage(nw, nh, java.awt.image.BufferedImage.TYPE_INT_RGB);
        Graphics2D g = out.createGraphics();
        g.drawImage(scaled, 0, 0, null);
        g.dispose();
        buffered = out;
      }
      ByteArrayOutputStream bos = new ByteArrayOutputStream();
      ImageIO.write(buffered, "jpg", bos);
      return new ProcessedImage(bos.toByteArray(), "image/jpeg");
    } catch (IOException e) {
      throw new IllegalArgumentException("Error al procesar la imagen", e);
    }
  }

  public record ProcessedImage(byte[] bytes, String mimeType) {}
}
