package com.harmoniwatts.electro.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "harmoniwatts.vision")
public class VisionProperties {

  /**
   * {@code chain} = failover Gemini→OpenAI→Mistral (orden en {@link #chainOrder}).
   * También: gemini | openai | mistral | ollama (un solo provider, sin failover).
   */
  private String provider = "chain";

  /** Orden de failover cuando provider=chain (CSV). */
  private String chainOrder = "gemini,openai,mistral";

  private int maxImageLongSide = 1024;

  private double lowConfidenceThreshold = 0.7;

  private Ollama ollama = new Ollama();

  private Mistral mistral = new Mistral();

  private Gemini gemini = new Gemini();

  private Openai openai = new Openai();

  public String getProvider() {
    return provider;
  }

  public void setProvider(String provider) {
    this.provider = provider;
  }

  public String getChainOrder() {
    return chainOrder;
  }

  public void setChainOrder(String chainOrder) {
    this.chainOrder = chainOrder;
  }

  public int getMaxImageLongSide() {
    return maxImageLongSide;
  }

  public void setMaxImageLongSide(int maxImageLongSide) {
    this.maxImageLongSide = maxImageLongSide;
  }

  public double getLowConfidenceThreshold() {
    return lowConfidenceThreshold;
  }

  public void setLowConfidenceThreshold(double lowConfidenceThreshold) {
    this.lowConfidenceThreshold = lowConfidenceThreshold;
  }

  public Ollama getOllama() {
    return ollama;
  }

  public void setOllama(Ollama ollama) {
    this.ollama = ollama;
  }

  public Mistral getMistral() {
    return mistral;
  }

  public void setMistral(Mistral mistral) {
    this.mistral = mistral;
  }

  public Gemini getGemini() {
    return gemini;
  }

  public void setGemini(Gemini gemini) {
    this.gemini = gemini;
  }

  public Openai getOpenai() {
    return openai;
  }

  public void setOpenai(Openai openai) {
    this.openai = openai;
  }

  public static class Ollama {
    private String baseUrl = "http://localhost:11434";
    private String model = "moondream";
    private int timeoutSeconds = 120;

    public String getBaseUrl() {
      return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
      this.baseUrl = baseUrl;
    }

    public String getModel() {
      return model;
    }

    public void setModel(String model) {
      this.model = model;
    }

    public int getTimeoutSeconds() {
      return timeoutSeconds;
    }

    public void setTimeoutSeconds(int timeoutSeconds) {
      this.timeoutSeconds = timeoutSeconds;
    }
  }

  public static class Mistral {
    private String apiKey = "";
    private String model = "pixtral-12b-2409";
    private String baseUrl = "https://api.mistral.ai";
    private int timeoutSeconds = 90;

    public String getApiKey() {
      return apiKey;
    }

    public void setApiKey(String apiKey) {
      this.apiKey = apiKey;
    }

    public String getModel() {
      return model;
    }

    public void setModel(String model) {
      this.model = model;
    }

    public String getBaseUrl() {
      return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
      this.baseUrl = baseUrl;
    }

    public int getTimeoutSeconds() {
      return timeoutSeconds;
    }

    public void setTimeoutSeconds(int timeoutSeconds) {
      this.timeoutSeconds = timeoutSeconds;
    }
  }

  public static class Gemini {
    private String apiKey = "";
    private String model = "gemini-3.6-flash";
    private String baseUrl = "https://generativelanguage.googleapis.com";
    private int timeoutSeconds = 90;

    public String getApiKey() {
      return apiKey;
    }

    public void setApiKey(String apiKey) {
      this.apiKey = apiKey;
    }

    public String getModel() {
      return model;
    }

    public void setModel(String model) {
      this.model = model;
    }

    public String getBaseUrl() {
      return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
      this.baseUrl = baseUrl;
    }

    public int getTimeoutSeconds() {
      return timeoutSeconds;
    }

    public void setTimeoutSeconds(int timeoutSeconds) {
      this.timeoutSeconds = timeoutSeconds;
    }
  }

  public static class Openai {
    private String apiKey = "";
    private String model = "gpt-4o-mini";
    private String baseUrl = "https://api.openai.com";
    private int timeoutSeconds = 90;

    public String getApiKey() {
      return apiKey;
    }

    public void setApiKey(String apiKey) {
      this.apiKey = apiKey;
    }

    public String getModel() {
      return model;
    }

    public void setModel(String model) {
      this.model = model;
    }

    public String getBaseUrl() {
      return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
      this.baseUrl = baseUrl;
    }

    public int getTimeoutSeconds() {
      return timeoutSeconds;
    }

    public void setTimeoutSeconds(int timeoutSeconds) {
      this.timeoutSeconds = timeoutSeconds;
    }
  }
}
