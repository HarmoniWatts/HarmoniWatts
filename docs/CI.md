# Integración continua (GitHub Actions)

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

## Cuándo corre

- En cada **Pull Request** hacia `qa`, `main` o `release` (antes de poder mergear).
- En cada **push** a `qa`, `main` o `release` (después del merge).
- Manualmente desde la pestaña *Actions* (`workflow_dispatch`).

Solo se ejecutan los jobs de los servicios que tienen cambios. Si se modifica algo en `.github/workflows/`, se validan todos.

## Qué revisa

| Servicio | Revisión de código | Pruebas unitarias | Build |
|----------|--------------------|-------------------|-------|
| `frontend` (Angular) | TypeScript estricto + `strictTemplates` + budgets en `ng build` | Vitest (`*.spec.ts`) | `ng build` + imagen Docker |
| `backend/insights-service` (Node) | `node --check` | `node --test` (`test/*.test.js`) | imagen Docker |
| `harmoni-register` (Node) | `node --check` | `node --test` (`test/*.test.js`) | imagen Docker |
| `backend/consumption-service` (Python) | `ruff` | `pytest` (`tests/`) | imagen Docker |
| `harmoniwatts-vivienda-api` (Java) | compilación `javac` | JUnit 5 + Mockito (`mvn verify`) | imagen Docker |
| `harmoniwatts-electrodomesticos-api` (Java) | compilación `javac` | JUnit 5 (`mvn verify`) | imagen Docker |
| Todo el repo | **gitleaks**: secretos en los commits nuevos | — | — |

Las imágenes Docker se construyen para validar el `Dockerfile`, **no se publican**.

El job **`CI OK`** resume todo: queda en verde si cada job pasó o se omitió por no tener cambios. Es el único check que hay que marcar como obligatorio.

Además, **Dependabot** ([`.github/dependabot.yml`](../.github/dependabot.yml)) abre cada lunes PRs hacia `qa` con actualizaciones de dependencias.

## Correr lo mismo en local

```bash
# Frontend
cd frontend && npm ci && npm run test:ci && npm run build

# Node (insights-service o harmoni-register)
cd backend/insights-service && npm ci && npm test

# Python
cd backend/consumption-service && pip install -r requirements-dev.txt && ruff check . && pytest

# Java
cd harmoniwatts-vivienda-api && mvn verify
```

## Protección de ramas (configurar una vez en GitHub)

*Settings → Branches → Add branch ruleset* (o *Add rule*) para `qa`, `main` y `release`:

1. **Require a pull request before merging**, con al menos **1 aprobación** (revisión humana).
2. **Require status checks to pass** → agregar el check **`CI OK`**.
3. **Require branches to be up to date before merging** (recomendado).
4. Bloquear *force push* y borrado de la rama.

Con esto ningún PR se puede mergear si las pruebas o la revisión automática fallan.
