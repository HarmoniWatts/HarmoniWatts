# Visión de electrodomésticos — providers en la nube + failover

El micro `harmoniwatts-electrodomesticos-api` analiza fotos de etiquetas (RETIQ / potencia) con APIs multimodales por Internet. **Ollama no va en Docker Compose.**

Por defecto usa modo **`chain`**: prueba los providers en orden y, si uno falla (cuota 429, error de red, respuesta inválida, etc.), pasa al siguiente que tenga API key.

```text
Gemini ──(falla)──► OpenAI ──(falla)──► Mistral ──(falla)──► error al usuario
   │ ok                 │ ok                │ ok
   ▼                    ▼                   ▼
 resultado           resultado           resultado
```

---

## Qué hago yo (código) vs qué haces tú

### Ya implementado (no tienes que programarlo)

- Adaptadores **Gemini**, **OpenAI** y **Mistral** registrados a la vez.
- Orquestador `ChainVisionAdapter`: failover automático.
- Providers **sin API key se omiten** (no rompen el arranque).
- Default: `HW_VISION_PROVIDER=chain` y orden `gemini,openai,mistral`.
- Ollama solo si activas flag aparte (fuera del stack normal).

### Lo que tienes que hacer tú

1. **Crear las API keys** (al menos una; ideal las tres para el failover):

   | Provider | URL de la key | Coste típico |
   |----------|---------------|--------------|
   | Gemini (recomendado 1.º) | https://aistudio.google.com/apikey | Tier **gratis** generoso |
   | OpenAI (2.º) | https://platform.openai.com/api-keys | Trial / **pago** (`gpt-4o-mini` barato) |
   | Mistral (3.º) | https://console.mistral.ai/ | Créditos / pay-as-you-go |

2. **Pegarlas en tu `.env`** (raíz de HarmoniWatts), por ejemplo:

```env
HW_VISION_PROVIDER=chain
HW_VISION_CHAIN_ORDER=gemini,openai,mistral

GEMINI_API_KEY=pega_aqui
OPENAI_API_KEY=pega_aqui
MISTRAL_API_KEY=pega_aqui
```

   Si solo tienes Gemini, deja las otras vacías: la cadena usará solo Gemini.

3. **Rebuild / reinicio de la API:**

```powershell
docker compose up -d --build harmoniwatts-electrodomesticos-api
```

4. **Probar** subiendo una foto desde el frontend (electrodomésticos → analizar imagen).

5. **Si falla todo**, mira logs:

```powershell
docker logs harmoniwatts-electrodomesticos-api --tail 80
```

   Busca líneas `Visión cadena: intentando provider=` / `falló provider=`.

---

## Configuración rápida

| Variable | Valores | Efecto |
|----------|---------|--------|
| `HW_VISION_PROVIDER` | `chain` (default) | Failover según `HW_VISION_CHAIN_ORDER` |
| `HW_VISION_PROVIDER` | `gemini` / `openai` / `mistral` | **Solo** ese provider (sin failover) |
| `HW_VISION_CHAIN_ORDER` | `gemini,openai,mistral` | Orden del failover |

Ejemplo: priorizar OpenAI y luego Gemini:

```env
HW_VISION_PROVIDER=chain
HW_VISION_CHAIN_ORDER=openai,gemini,mistral
```

---

## Seguridad

- Keys **solo** en `.env` (nunca en git).
- El frontend **no** ve las keys; solo habla con el micro en `:8083`.
- El contenedor necesita salida a Internet hacia:
  - `generativelanguage.googleapis.com`
  - `api.openai.com`
  - `api.mistral.ai`

---

## Ollama (opcional, no recomendado para este proyecto)

```env
# application / env avanzado
HW_VISION_PROVIDER=chain
HW_VISION_CHAIN_ORDER=gemini,openai,mistral,ollama
# y en application: harmoniwatts.vision.ollama.enabled=true + Ollama corriendo aparte
```

No está en Compose; no hace falta para el flujo normal.
