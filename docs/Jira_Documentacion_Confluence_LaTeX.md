# Documentación Confluence — Creación documento LaTeX

Material para copiar a **Jira** (Historia de usuario, Epic o Tarea según el equipo).

---

## Resumen / título

**Documentación Confluence — Creación documento LaTeX (entrega formal del proyecto integrador, versión inicial)**

**Resumen corto (campo breve en Jira):**  
Docs Confluence + informe LaTeX inicial (entrega formal iniciada)

---

## Tipo sugerido

- **Epic** "Documentación técnica y entrega formal" con subtareas, o una **Story** única con subtareas.

---

## Descripción

**Como** equipo del proyecto integrador (HarmoniWatts / proyecto académico),  
**quiero** centralizar la **documentación técnica en Confluence** y disponer de un **documento LaTeX de entrega formal** alineado con los requisitos del integrador,  
**para** asegurar trazabilidad del diseño y la implementación, facilitar revisiones docentes y entregar un borrador oficial del informe final.

### Alcance

1. **Confluence:** estructurar y poblar (en la medida acordada) la documentación técnica del proyecto: arquitectura, stack, despliegue, APIs/contratos relevantes, base de datos, decisiones técnicas y enlaces a repositorio/CI si aplica.
2. **LaTeX:** crear el **esqueleto del documento de entrega formal** (portada, índice, secciones principales según guía del curso), con **contenido inicial** en las secciones prioritarias; **no** se exige documento completo en esta historia, sí **base reutilizable** y coherente con Confluence.

### Fuera de alcance (explícito)

- Cierre de todas las secciones del informe final.
- Redacción exhaustiva de cada capítulo (salvo lo que el equipo marque como mínimo en criterios de aceptación).

---

## Criterios de aceptación

### Confluence

- [ ] Existe un **espacio o árbol de páginas** acordado (por ejemplo: Visión, Arquitectura, Backend, Frontend, Base de datos, Despliegue/DevOps, Seguridad, Glosario).
- [ ] Al menos **las secciones prioritarias** definidas por el equipo tienen **contenido inicial** (no páginas vacías): por ejemplo arquitectura + stack + cómo levantar el proyecto.
- [ ] Las páginas incluyen **enlaces** al repositorio, ramas principales o documentos clave del repo **cuando aplique**.
- [ ] Hay una **página índice** que enlaza al resto de documentación técnica.

### Documento LaTeX

- [ ] Repositorio o carpeta del proyecto contiene el **proyecto LaTeX** (main `.tex`, estructura de capítulos, referencias si se usan).
- [ ] El documento **compila** sin errores (al menos **PDF** generado desde la raíz del proyecto LaTeX).
- [ ] Están creadas las **secciones principales** acordadas con la guía del integrador (portada, resumen/abstract si aplica, introducción, alcance, arquitectura, etc.) aunque parte vaya con **placeholders** breves.
- [ ] **Mínimo contenido redactado** en al menos **N** secciones (definir N en planificación; p. ej. 2–3) para demostrar el hilo narrativo y el estilo de entrega; el resto puede marcarse como "pendiente".
- [ ] Se documenta en **Confluence o comentario de Jira** **dónde** está el LaTeX (ruta) y **cómo** compilarlo.

### Alineación Confluence ↔ LaTeX

- [ ] Las **fuentes de verdad** están claras: lo técnico detallado puede vivir en Confluence; el LaTeX **resume o enlaza** sin duplicar masivamente (criterio del equipo reflejado en una nota corta).

---

## Subtareas sugeridas

1. Definir **jerarquía de páginas** en Confluence y plantilla de página técnica.
2. Redactar **páginas iniciales** (arquitectura, stack, despliegue).
3. Crear **esqueleto LaTeX** (`main.tex`, `\include` / `\input` por capítulo).
4. Rellenar **capítulos iniciales** y placeholders en el resto.
5. Verificar **compilación** y subir **PDF de muestra** (opcional: adjunto en Jira o enlace).
6. Enlazar **Jira → Confluence** (issue link o mención en página de "Estado del proyecto").

---

## Definition of Done (opcional)

- Revisión rápida por **al menos un** miembro del equipo (ortografía básica + que los enlaces funcionen).
- La historia incluye **enlace a la raíz Confluence** y **ruta/cómo compilar** el LaTeX.

---

## Notas

- Si el curso exige **capítulos fijos** (por ejemplo "Marco teórico", "Metodología"), sustituir o ampliar la lista de secciones LaTeX en los criterios de aceptación.
- Ajustar **N** (número mínimo de secciones con contenido redactado) según acuerdo del equipo o del docente.
