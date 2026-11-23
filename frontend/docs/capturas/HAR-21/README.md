# Capturas HAR-21: alertas visuales

Tomadas en el entorno local (Docker) con datos reales (contrato 475090, ENERTOTAL) y la tarifa de Cali de
noviembre de 2026 (punta de 18:00 a 22:00). Para mostrar las alertas de franja se simuló la hora con
`?simularHora=` (solo en desarrollo). Tema oscuro, 1440 px de ancho.

| Archivo | Qué muestra | Criterio HU |
|---|---|---|
| `01-dashboard-con-aviso-media.png` | Dashboard a las 17:20 con el aviso emergente | 1 |
| `02-aviso-emergente-media-punta-en-40-min.png` | Aviso de severidad media: la punta empieza en 40 min | 1, 3 |
| `03-campana-con-contador.png` | Campana del menú con el contador de no leídas | 1 |
| `04-panel-de-notificaciones.png` | Panel: alertas (franja y consumo) y recomendaciones IA | 1, 2, 3 |
| `05-ultimas-notificaciones-dashboard.png` | Tarjeta «Últimas notificaciones» del dashboard | 1, 2, 3 |
| `06-aviso-emergente-alta-en-punta.png` | Aviso de severidad alta a las 19:00: en franja de punta | 1, 3 |
| `07-panel-en-punta-severidad-alta.png` | Panel con la alerta alta de punta y la de consumo (+55 % a las 13:00) | 1, 2, 3 |

Criterios: 1 notificación al activarse la franja de alto precio · 2 consumo X % sobre el promedio histórico ·
3 severidad baja / media / alta. (El criterio 4, umbrales configurables, se retiró de la HU.)
