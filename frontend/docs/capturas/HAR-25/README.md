# Capturas HAR-25: visualización de la predicción

Tomadas en el entorno local (Docker) con datos reales sincronizados (contrato 475090, ENERTOTAL), el modelo
MLflow de prediction-service y la tarifa de noviembre de 2026. Tema oscuro, 1440 px de ancho.

| Archivo | Qué muestra | Criterio HU |
|---|---|---|
| `01-dashboard-vista-general.png` | Dashboard completo con la tarjeta nueva | — |
| `02-grafico-dia-prediccion-del-modelo.png` | Gráfico del día: la línea punteada ya es la predicción del modelo (antes, consumo real + ruido) | 1 |
| `03-prediccion-por-dia.png` | Real vs predicho (últimos días) y próximos días con rango | 1, 2 |
| `04-prediccion-por-dia-tooltip-real-vs-predicho.png` | Tooltip de un día pasado: real, predicho y diferencia | 1, 4 |
| `05-prediccion-proximos-dias-tooltip-rango.png` | Tooltip de un día futuro: predicción y rango probable | 2, 4 |
| `06-prediccion-por-hora-tooltip.png` | Vista por hora: real vs predicho, banda del rango, «Ahora» y tooltip | 1, 2, 4 |
| `07-prediccion-por-franja-tooltip.png` | Vista por franja (valle/media/punta) con el real como referencia | 5 |
| `08-indicador-de-confianza.png` | Confianza alta/media/baja con el error diario medido | 3 |

Criterios: 1 predicción vs real · 2 próximos días · 3 confianza · 4 tooltip · 5 por franjas horarias.
