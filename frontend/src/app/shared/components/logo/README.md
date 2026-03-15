# Logo HarmoniWatts

Icono oficial del proyecto (rayo en círculo con gradiente cyan–verde y contorno por capas). Reutilizable en toda la app.

## Uso del componente

```html
<!-- Tamaño por defecto (56px), sin animación -->
<app-logo />

<!-- Tamaño personalizado -->
<app-logo [size]="40" />

<!-- Con animación de brillo (ej. página de login) -->
<app-logo [size]="56" [animated]="true" />

<!-- En header o barra lateral -->
<app-logo [size]="32" [animated]="false" />
```

**Inputs:**

| Input     | Tipo    | Por defecto | Descripción                                      |
|----------|---------|-------------|--------------------------------------------------|
| `size`   | number  | 56          | Ancho y alto en píxeles.                         |
| `animated` | boolean | false     | Si es true, aplica la animación de brillo pulsante. |

Importar el componente donde se use:

```ts
import { LogoComponent } from '../shared/components/logo';
// ...
imports: [..., LogoComponent],
```

## Archivo SVG estático

Para favicon, PWA, correos o uso fuera de Angular:

- **Ruta:** `public/images/harmoniwatts-logo.svg`
- **URL en la app:** `/images/harmoniwatts-logo.svg`

Ejemplo en HTML:

```html
<img src="/images/harmoniwatts-logo.svg" alt="HarmoniWatts" width="64" height="64" />
```

Colores del proyecto: cyan `#22d3ee`, verde `#4ade80`, contorno `#0e7490`.
