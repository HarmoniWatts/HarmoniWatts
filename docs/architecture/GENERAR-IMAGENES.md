# 🖼️ Generar Imágenes de Diagramas

**Guía para compilar los diagramas C4 (Structurizr) y de secuencia (Mermaid) como imágenes PNG.**

---

## 📋 Imágenes Requeridas

### C4 Diagramas (Structurizr → PNG)

```
images/
├── c4-context.png                    # Level 1: System Context
├── c4-container.png                  # Level 2: Container Architecture
├── c4-component-consumption.png      # Level 3: Consumption Service
├── c4-component-insights.png         # Level 3: Insights Service
├── c4-component-vivienda.png         # Level 3: Vivienda API
├── c4-component-appliances.png       # Level 3: Electrodomésticos API
└── c4-component-prediction.png       # Level 3: Prediction Service
```

### Diagramas de Secuencia (Mermaid → PNG)

```
images/
├── sequence-ingesta.png              # Flujo 1: Ingesta de datos
├── sequence-dashboard.png            # Flujo 2: Visualización de dashboards
├── sequence-prediccion.png           # Flujo 3: Predicción de electrodomésticos
├── sequence-autenticacion.png        # Flujo 4: Autenticación Keycloak
├── sequence-recomendaciones.png      # Flujo 5: Recomendaciones de ahorro
└── sequence-tariffas.png             # Flujo 6: Integración tarifas
```

---

## 🔧 Generar Imágenes C4 (Structurizr)

### Opción 1: Interfaz Web Structurizr (Recomendado - Manual)

```
1. Ir a https://structurizr.com/dsl
2. Copiar contenido de workspace.dsl
3. Pegar en el editor
4. Para cada vista (Context, Container, Component):
   a. Seleccionar la vista en el dropdown superior
   b. Hacer clic en el icono "Export" (esquina superior derecha)
   c. Seleccionar formato PNG
   d. Descargar imagen
   e. Renombrar y guardar en images/
```

### Opción 2: Docker Structurizr Lite (Automático)

```bash
# Iniciar Structurizr Lite con el DSL
docker run -it --rm -p 8080:8080 -v $(pwd)/docs/architecture:/workspace structurizr/lite:latest

# Luego:
# 1. Abrir http://localhost:8080
# 2. Navegar a cada vista
# 3. Usar la herramienta de exportación interna (screenshot con formato PNG)
```

### Opción 3: Structurizr CLI

```bash
# Descargar CLI desde https://github.com/structurizr/cli/releases

# Exportar a PlantUML y luego convertir
structurizr export -workspace workspace.dsl -format plantuml

# Luego usar PlantUML online para convertir a PNG
# https://www.planttext.com/
```

---

## 🎨 Generar Imágenes de Secuencia (Mermaid)

### Opción 1: Mermaid Live Editor (Manual)

```
1. Ir a https://mermaid.live/
2. Para cada diagrama en sequence-diagrams.mmd:
   a. Copiar el bloque del diagrama
   b. Pegar en Mermaid Live
   c. Exportar como PNG (botón Download)
   d. Guardar en images/sequence-*.png
```

### Opción 2: Mermaid CLI (Automático)

```bash
# Instalar Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Convertir diagramas de secuencia a PNG
mmdc -i sequence-diagrams.mmd -o images/sequences.png

# O generar cada diagrama por separado (requiere editar el .mmd)
mmdc -i sequence-ingesta.mmd -o images/sequence-ingesta.png
mmdc -i sequence-dashboard.mmd -o images/sequence-dashboard.png
# ... etc
```

### Opción 3: GitHub Actions (Automático en CI/CD)

```yaml
# .github/workflows/generate-diagrams.yml
name: Generate Diagrams

on: [push]

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: mermaid-js/mermaid-cli@master
        with:
          files: docs/architecture/sequence-diagrams.mmd
          output: docs/architecture/images/sequences.png
      - uses: actions/upload-artifact@v3
        with:
          name: diagram-artifacts
          path: docs/architecture/images/
```

---

## 📥 Cargar Imágenes en Confluence

Una vez generadas todas las imágenes PNG:

### Opción 1: Carga Manual en cada página

```
1. Ir a Confluence → HarmoniWatts - Documentación Técnica
2. Editar la página correspondiente (ej: "2. Arquitectura de Contenedores")
3. Hacer clic en "Insert" → "Image"
4. Seleccionar "Upload an image"
5. Cargar el PNG desde images/
6. Redimensionar si es necesario
```

### Opción 2: Script de Upload Automático

```python
# Upload images to Confluence via API
import requests
import os

CONFLUENCE_URL = "https://giia.atlassian.net"
SPACE_KEY = "HarmoniWatts"
IMAGES_DIR = "docs/architecture/images"

for image_file in os.listdir(IMAGES_DIR):
    if image_file.endswith(".png"):
        # API call to upload image
        with open(f"{IMAGES_DIR}/{image_file}", "rb") as f:
            files = {"file": f}
            # Requires Confluence API auth
            # requests.post(f"{CONFLUENCE_URL}/rest/api/content/{page_id}/child/attachment",
            #     files=files, auth=(user, token))
```

---

## ✅ Checklist de Imágenes

### C4 - System Context
- [ ] `images/c4-context.png` - Generada y guardada

### C4 - Container Architecture
- [ ] `images/c4-container.png` - Generada y guardada

### C4 - Components (5 servicios)
- [ ] `images/c4-component-consumption.png` - Generada
- [ ] `images/c4-component-insights.png` - Generada
- [ ] `images/c4-component-vivienda.png` - Generada
- [ ] `images/c4-component-appliances.png` - Generada
- [ ] `images/c4-component-prediction.png` - Generada

### Diagramas de Secuencia (6 flujos)
- [ ] `images/sequence-ingesta.png` - Generada
- [ ] `images/sequence-dashboard.png` - Generada
- [ ] `images/sequence-prediccion.png` - Generada
- [ ] `images/sequence-autenticacion.png` - Generada
- [ ] `images/sequence-recomendaciones.png` - Generada
- [ ] `images/sequence-tariffas.png` - Generada

### Documentación Actualizada
- [ ] `docs/architecture/C4-DIAGRAMAS.md` - Referencia imágenes
- [ ] `docs/ARQUITECTURA-MAESTRA.md` - Referencias actualizadas
- [ ] Confluence - Todas las páginas con imágenes

---

## 🚀 Pasos Finales

```bash
# 1. Generar todas las imágenes (ver opciones arriba)

# 2. Guardar en docs/architecture/images/

# 3. Commit cambios
git add docs/architecture/images/
git add docs/architecture/C4-DIAGRAMAS.md
git add docs/ARQUITECTURA-MAESTRA.md
git commit -m "images: agregar diagramas C4 y secuencia compilados"

# 4. Push
git push

# 5. Cargar imágenes en Confluence (manualmente o via API)
```

---

## 📚 Recursos

- **Structurizr DSL:** https://structurizr.com/help/dsl
- **Mermaid Diagrams:** https://mermaid.js.org/
- **Mermaid CLI:** https://github.com/mermaid-js/mermaid-cli
- **Structurizr Export:** https://github.com/structurizr/export

---

**Nota:** Este documento describe el proceso para generar imágenes compiladas.  
Una vez generadas, se guardan en `images/` y se referencian desde los documentos Markdown y Confluence.
