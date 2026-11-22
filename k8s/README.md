# Despliegue en Azure con Kubernetes (k3s) gestionado desde GitHub

Todo el aplicativo corre en **una VM de Azure con k3s** (Kubernetes ligero), bajo un
solo dominio con HTTPS: `https://<dns-label>.<región>.cloudapp.azure.com`.
GitHub Actions construye las imágenes, las publica en GHCR y despliega.

```
Internet ──443──► Traefik (k3s) ─┬─ /auth ............................ keycloak
                                 ├─ /api/auth ........................ harmoni-register
                                 ├─ /api/v1/viviendas/{id}/electrodomesticos, /api/v1/electrodomesticos ─ electrodomesticos-api
                                 ├─ /api/v1/viviendas ................ vivienda-api
                                 ├─ /api/v1/tariff ................... tariff-service
                                 ├─ /api/v1/dashboard, /recommendations insights-service ─► consumption-service ─► MongoDB
                                 └─ / ................................ frontend (nginx)
                    internos: postgres, mongodb, consumption-service, prediction-service
```

| Archivo | Qué hace |
|---|---|
| `infra/azure/provision.sh` | Crea grupo de recursos, IP + DNS, NSG, VM con k3s, apagado automático e identidad administrada (OIDC) para GitHub |
| `infra/azure/configure-k3s-oidc.sh` | Hace que el API server de k3s acepte los tokens de Keycloak (login de Headlamp) |
| `infra/azure/get-kubeconfig.sh` | Saca el kubeconfig de la VM y lo guarda como secreto `KUBECONFIG` en GitHub |
| `k8s/base/` | Manifiestos (Kustomize) de todos los servicios |
| `k8s/deploy.sh` | Instala cert-manager, crea secretos/ConfigMaps y aplica los manifiestos |
| `k8s/keycloak-headlamp.sh` | Crea en Keycloak el cliente `headlamp` y el grupo `k8s-admins` (lo ejecuta `deploy.sh`) |
| `.github/workflows/deploy-azure.yml` | Build + push a GHCR + despliegue (push a `qa` o manual) |
| `.github/workflows/azure-vm.yml` | Encender / apagar / ver estado de la VM desde GitHub |
| `scripts/k8s/restore-postgres.sh` | Carga los snapshots de PostgreSQL en el clúster |

## Costo (aprox.)

VM `Standard_D2as_v7` (2 vCPU, 8 GB) ≈ 0,091 USD/h encendida + disco 64 GB Standard SSD (~5 USD/mes)
+ IP estática (~3,6 USD/mes). Encendida 24/7 ≈ 75 USD/mes; con el apagado automático
diario y encendiéndola solo cuando se usa, mucho menos. (La serie B no está habilitada
en la prueba gratuita; con Azure for Students se puede usar `VM_SIZE=Standard_B2ms`,
algo más barata.) No hay balanceador de carga ni
registro de contenedores de pago (GHCR es gratis).

## Configuración inicial (una sola vez por suscripción)

Requisitos: [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli), [GitHub CLI](https://cli.github.com/)
y Git Bash. Ser administrador del repositorio en GitHub.

### 1. Elegir la suscripción

```bash
az login
az account list -o table
az account set --subscription "<id de la suscripción>"
gh auth login
```

### 2. Crear la infraestructura

```bash
bash infra/azure/provision.sh
```

Variables opcionales: `LOCATION` (por defecto `eastus2`), `DNS_LABEL` (`harmoniwatts`,
debe ser único en la región), `VM_SIZE`, `SHUTDOWN_UTC` (`0400` = 23:00 en Colombia).
Ejemplo: `DNS_LABEL=harmoniwatts-demo bash infra/azure/provision.sh`.

El script crea el environment **`azure`** en GitHub y guarda `AZURE_CLIENT_ID`,
`AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` y las variables `AZURE_RESOURCE_GROUP`,
`AZURE_VM_NAME`, `AZURE_NSG_NAME`, `APP_HOST`.

### 3. Kubeconfig (esperar 3-5 min a que k3s se instale)

```bash
bash infra/azure/get-kubeconfig.sh
bash infra/azure/configure-k3s-oidc.sh   # login de Headlamp con Keycloak
```

### 4. Secretos y variables de la aplicación

En GitHub → Settings → Environments → `azure` (o con `gh`):

```bash
gh variable set LETSENCRYPT_EMAIL --env azure -b "<tu correo>"
gh secret set POSTGRES_USER     --env azure -b "harmoniwatts"
gh secret set POSTGRES_PASSWORD --env azure      # pide el valor
gh secret set KC_ADMIN_USERNAME --env azure -b "admin"
gh secret set KC_ADMIN_PASSWORD --env azure      # pide el valor
```

Opcionales: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `MISTRAL_API_KEY`, `SMTP_HOST`, `SMTP_PORT`,
`SMTP_FROM`, `SMTP_USER`, `SMTP_PASSWORD` y `GHCR_PULL_TOKEN` (un token con `read:packages`,
solo si los paquetes de GHCR quedan privados; alternativa: hacerlos públicos en
GitHub → Packages → Package settings).

### 5. Primer despliegue

GitHub → Actions → **Deploy Azure** → Run workflow (o un push a `qa`).

En el primer despliegue la base `harmoniwatts` está vacía, así que `vivienda-api`,
`electrodomesticos-api` y `tariff-service` no arrancan hasta cargar los datos. Exporta
los snapshots desde tu Docker local y restáuralos en el clúster:

```bash
bash scripts/export-snapshots.sh                     # genera docker/snapshots/postgres/*.dump
KUBECONFIG=~/.kube/harmoniwatts-azure.yaml bash scripts/k8s/restore-postgres.sh docker/snapshots/postgres
```

Los pods se recuperan solos; vuelve a ejecutar el workflow para verlo en verde.
MongoDB se carga automáticamente con `BD/datos` (Job `mongo-seed`).

> Si restauras `keycloak_db`, los usuarios y el realm vienen del snapshot. Si no, el realm
> se importa desde `keycloak-realm/realm-export.json` con el dominio público agregado.

## Uso diario

- **Encender / apagar:** Actions → **Azure VM** → `start` / `stop` / `status`.
  El despliegue también enciende la VM. Cada noche se apaga sola.
- **Ver el clúster desde tu PC:** `export KUBECONFIG=~/.kube/harmoniwatts-azure.yaml`, luego
  `kubectl -n harmoniwatts get pods`. El puerto 6443 solo está abierto para la IP que tenías
  al ejecutar `provision.sh`; si cambia, vuelve a ejecutarlo.
- **Logs:** `kubectl -n harmoniwatts logs deploy/keycloak --tail=100`
- **Consola de Keycloak:** `https://<APP_HOST>/auth/admin`
- **Headlamp (interfaz gráfica del clúster):** `https://<APP_HOST>/headlamp` → *Sign in* →
  login de Keycloak del realm **master** (el administrador de Keycloak ya es miembro).
  Para dar acceso a otra persona: en la consola de Keycloak, realm **master** → *Users* →
  crear el usuario → *Groups* → unirlo a **k8s-admins** (permiso `cluster-admin`).
  Los usuarios del realm de la aplicación (`harmoniwatts`) no pueden entrar.
- **Modelos de predicción** (no están en git):
  `kubectl -n harmoniwatts cp backend/prediction-service/model/. <pod>:/app/model`,
  donde `<pod>` sale de `kubectl -n harmoniwatts get pods -l app.kubernetes.io/name=prediction-service`.

## Tareas programadas (CronJobs)

Definidas en `k8s/base/cronjobs.yaml`; los scripts están en `k8s/base/cron/`. Horario de Colombia.

| CronJob | Cuándo | Qué hace |
|---|---|---|
| `sincronizar-consumos` | Cada hora (minuto 5) | Toma los contratos de PostgreSQL (viviendas con contrato + comercializadora y clientes con contrato) y pide a consumption-service las lecturas de ayer y hoy. Repetir un rango no duplica lecturas. |
| `actualizar-tarifas` | Lunes 6:00 | Para cada comercializadora activa, tariff-service descarga y procesa los PDFs de tarifas desde el mes anterior. Las tarifas existentes no se duplican. |

- Ver ejecuciones: `kubectl -n harmoniwatts get cronjobs,jobs` (o en Headlamp → Cargas de trabajo).
- Ejecutar ya: `kubectl -n harmoniwatts create job --from=cronjob/sincronizar-consumos sync-manual`
  (o `--from=cronjob/actualizar-tarifas tarifas-manual`).
- Traer más días de consumo: `kubectl -n harmoniwatts set env cronjob/sincronizar-consumos DIAS_ATRAS=10`
  (vuelve a 1 en el siguiente despliegue).
- Con la VM apagada no corren; la siguiente ejecución vuelve a pedir el rango completo.

## Cambiar de suscripción (ej. de la prueba gratuita a Azure for Students)

1. Respalda los datos de la nube (con el kubeconfig de la suscripción anterior):
   ```bash
   mkdir -p backup
   for db in keycloak_db harmoniwatts; do
     kubectl -n harmoniwatts exec postgres-0 -- sh -c "pg_dump -U \"\$POSTGRES_USER\" -d $db -Fc" > backup/$db.dump
   done
   ```
   Luego, en el clúster nuevo: `bash scripts/k8s/restore-postgres.sh backup`.
2. `az account set --subscription "<nueva>"` y repite los pasos 2, 3 y 5.
   Los scripts sobrescriben los secretos `AZURE_*` y `KUBECONFIG` del environment;
   los secretos de la aplicación (paso 4) se conservan.
3. Borra lo de la suscripción anterior: `az group delete -n rg-harmoniwatts` (con la
   suscripción anterior seleccionada) (incluye la identidad `id-github-rg-harmoniwatts`).

## Notas

- La suscripción de prueba gratuita de Azure limita los vCPU por región (normalmente 4);
  la D2as_v7 usa 2.
- El frontend de producción (`frontend/Dockerfile.prod`) usa `src/environments/environment.ts`,
  que apunta todo al mismo dominio. El desarrollo local con docker-compose no cambia.
- `pgAdmin` y `mongo-express` no se despliegan; para inspeccionar usa
  `kubectl -n harmoniwatts port-forward svc/postgres 5432` o `svc/harmoniwatts-mongodb 27017`.
