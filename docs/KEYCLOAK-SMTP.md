# Tutorial: Configuración SMTP en Keycloak para envío de correos

Este documento explica cómo configurar el envío de correos electrónicos en Keycloak (verificación de email, restablecimiento de contraseña, etc.) usando SMTP.

---

## 1. ¿Para qué usa Keycloak el correo?

Keycloak puede enviar correos en estos casos:

| Función | Descripción |
|--------|-------------|
| **Verificación de email** | Tras el registro, el usuario recibe un enlace para verificar su correo. Hasta que no verifique, puede estar bloqueado el login (según configuración del realm). |
| **Restablecimiento de contraseña** | El usuario solicita "¿Olvidaste tu contraseña?" y recibe un enlace para crear una nueva. |
| **Actualización de email** | Si el realm permite cambiar el correo, puede enviarse un correo de confirmación. |
| **Eventos de seguridad** | Avisos de inicio de sesión desde un dispositivo nuevo, etc. (según configuración). |

Sin SMTP configurado, estas funciones no enviarán correos y el usuario no podrá verificar su email ni recuperar la contraseña por correo.

---

## 2. Dónde se configura SMTP en Keycloak

1. Abre la **Admin Console** de Keycloak (ej. `http://localhost:8080`).
2. Inicia sesión con el usuario administrador.
3. Selecciona el **realm** donde quieres configurar el correo (ej. `harmoniwatts`).
4. En el menú lateral: **Realm settings** → pestaña **Email**.

Ahí verás todos los parámetros SMTP.

---

## 3. Parámetros SMTP explicados

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **From** | Dirección que aparece como remitente. Debe ser válida; algunos proveedores exigen un dominio verificado. | `noreply@midominio.com` o `keycloak@localhost` (solo pruebas) |
| **From display name** | Nombre que ve el usuario como remitente. | `HarmoniWatts` |
| **Host** | Servidor SMTP. | `smtp.gmail.com`, `sandbox.smtp.mailtrap.io`, `smtp.office365.com` |
| **Port** | Puerto SMTP. Suele ser **587** (STARTTLS) o **465** (SSL). | `587` |
| **Encryption** | **None** (puerto 25), **SSL** (465) o **StartTLS** (587). | StartTLS para 587 |
| **Authentication** | ON si el servidor exige usuario y contraseña (casi siempre). | ON |
| **Username** | Usuario SMTP (a menudo tu correo completo). | `miemail@gmail.com` |
| **Password** | Contraseña. En Gmail se usa una **contraseña de aplicación**, no la contraseña normal. | (secreta) |

Después de rellenar, usa **Save** y luego **Test connection** para comprobar que Keycloak puede conectar y autenticarse.

---

## 4. Configuración con Gmail

Gmail exige usar **contraseña de aplicación** (App Password) cuando la cuenta tiene 2FA; si no tienes 2FA, puede que tengas que activarla para poder crear la contraseña de aplicación.

### 4.1 Habilitar 2FA y crear contraseña de aplicación (recomendado)

1. Entra en tu cuenta de Google → [Seguridad](https://myaccount.google.com/security).
2. En **Inicio de sesión en Google**, activa **Verificación en dos pasos** si no está activa.
3. En la misma sección, busca **Contraseñas de aplicaciones** (o "App passwords").
4. Clic en **Contraseñas de aplicaciones**.
5. Selecciona **Correo** y el dispositivo **Otro**; pon un nombre (ej. "Keycloak HarmoniWatts") y genera.
6. Google te muestra una **contraseña de 16 caracteres** (sin espacios). Cópiala; la usarás como contraseña SMTP.

### 4.2 Configuración en Keycloak (Realm settings → Email)

| Campo | Valor |
|-------|--------|
| **From** | Tu correo Gmail (ej. `miemail@gmail.com`). |
| **From display name** | Opcional, ej. `HarmoniWatts`. |
| **Host** | `smtp.gmail.com` |
| **Port** | `587` |
| **Encryption** | **StartTLS** |
| **Authentication** | **ON** |
| **Username** | Tu correo Gmail completo. |
| **Password** | La contraseña de aplicación de 16 caracteres (sin espacios). |

Guardar y **Test connection**. Si falla, revisa que 2FA y contraseña de aplicación estén bien creadas y que no haya bloqueos en la cuenta de Google.

---

## 5. Configuración con Mailtrap (desarrollo y pruebas)

[Mailtrap](https://mailtrap.io) sirve para capturar los correos en desarrollo sin enviarlos a direcciones reales. Tienes una bandeja de prueba donde ves todos los correos que Keycloak “envía”.

### 5.1 Crear cuenta y obtener credenciales SMTP

1. Regístrate en [mailtrap.io](https://mailtrap.io) (plan gratuito suficiente).
2. Entra en **Email Testing** → **Inboxes** → selecciona tu inbox (o crea uno).
3. Abre la pestaña **SMTP Settings**.
4. Elige **Integrations** → **Keycloak** (si existe) o **SMTP** genérico.
5. Anota:
   - **Host:** suele ser `sandbox.smtp.mailtrap.io`
   - **Port:** `587` (o el que indiquen, a veces 2525)
   - **Username** y **Password:** los que muestra Mailtrap para ese inbox

### 5.2 Configuración en Keycloak (Realm settings → Email)

| Campo | Valor |
|-------|--------|
| **From** | Cualquier dirección (ej. `noreply@harmoniwatts.local`). Mailtrap acepta cualquier remitente en pruebas. |
| **From display name** | Opcional. |
| **Host** | `sandbox.smtp.mailtrap.io` |
| **Port** | `587` (o 2525 si Mailtrap lo indica). |
| **Encryption** | **StartTLS** (para 587). |
| **Authentication** | **ON** |
| **Username** | El de Mailtrap. |
| **Password** | La de Mailtrap. |

Guardar y **Test connection**. Luego, al registrar un usuario o pedir “olvidé contraseña”, el correo aparecerá en la bandeja de Mailtrap, no en un buzón real.

---

## 6. Otros proveedores habituales

### Outlook / Microsoft 365

- **Host:** `smtp.office365.com`
- **Port:** `587`
- **Encryption:** StartTLS
- **Username:** tu correo completo (`usuario@dominio.com`)
- **Password:** contraseña de la cuenta (o contraseña de aplicación si está habilitada).

### SendGrid, Mailgun, Amazon SES

Cada uno da en su panel un **host SMTP**, **puerto**, **usuario** y **contraseña** (o API key como contraseña). Rellena en Keycloak los mismos campos (From, Host, Port, Encryption, Username, Password) según su documentación.

---

## 7. Activar el envío de correos en el realm

Solo con SMTP configurado no basta: hay que activar las funciones que usan correo.

### 7.1 Verificación de email (recomendado tras registro)

1. **Realm settings** → pestaña **Login**.
2. Activa **Verify email** (Verify email address).
3. **Save**.

Así, tras registrarse, Keycloak enviará el correo de verificación. Si además quieres **bloquear el login hasta que el usuario verifique**, en **Realm settings** → **Login** (o en los **Authentication** flows) puedes exigir que el usuario haya verificado el email antes de poder iniciar sesión (depende de la versión de Keycloak; suele estar en Required actions o en el flujo de registro).

### 7.2 Restablecimiento de contraseña

La opción "¿Olvidaste tu contraseña?" suele estar habilitada por defecto en la página de login de Keycloak. Al usarla, Keycloak enviará el correo usando la configuración SMTP que definiste.

### 7.3 Comprobar flujos de autenticación (opcional)

En **Authentication** → **Flows** (o **Required actions**) puedes revisar que las acciones **Verify Email** y **Reset Password** estén habilitadas para los flujos que usas (Browser, Direct grant, etc.).

---

## 8. Probar que todo funciona

### 8.1 Test connection en Keycloak

En **Realm settings** → **Email**, tras guardar, pulsa **Test connection**. Keycloak intentará conectar al SMTP y autenticarse. Si hay error, revisa host, puerto, cifrado, usuario y contraseña.

### 8.2 Probar correo de verificación

1. Activa **Verify email** en el realm (ver apartado 7).
2. Desde tu aplicación (o desde la pantalla de registro de Keycloak), registra un usuario con un correo que puedas revisar (o que esté en Mailtrap).
3. Revisa la bandeja: debe llegar un correo de Keycloak con el enlace de verificación.
4. Abre el enlace y comprueba que el usuario queda verificado.

### 8.3 Probar “Olvidé mi contraseña”

1. En la pantalla de login de Keycloak (o la de tu app que redirija a Keycloak), usa “Forgot password?” / “¿Olvidaste tu contraseña?”.
2. Introduce un correo de usuario existente.
3. Revisa que llegue el correo de restablecimiento y que el enlace funcione.

---

## 9. Personalizar plantillas de correo (opcional)

Keycloak permite cambiar los textos y el aspecto de los correos:

1. **Realm settings** → pestaña **Themes**.
2. En **Email theme** elige un tema (ej. `keycloak` por defecto) o crea uno personalizado.
3. Para personalizar textos o HTML, en el servidor Keycloak se editan los archivos del tema de email (directorio del tema dentro de Keycloak). Esto implica crear un tema personalizado y, en Docker, montar los archivos o construir una imagen propia. Para un primer uso no es necesario.

---

## 10. Keycloak en Docker y variables de entorno

Si Keycloak corre en Docker (por ejemplo con el `docker-compose` de HarmoniWatts), la configuración SMTP se hace **dentro de Keycloak** (Realm settings → Email). Es la forma más fiable.

Algunas versiones o imágenes permiten definir parte de la configuración SMTP por variables de entorno (por ejemplo `KC_SPI_EMAIL_SMTP_HOST`, etc.). En el `.env.example` del proyecto aparecen variables opcionales como:

- `KC_SPI_EMAIL_SMTP_HOST`
- `KC_SPI_EMAIL_SMTP_PORT`
- `KC_SPI_EMAIL_SMTP_FROM`
- `KC_SPI_EMAIL_SMTP_USER`
- `KC_SPI_EMAIL_SMTP_PASSWORD`
- `KC_SPI_EMAIL_SMTP_SSL_ENABLED` / `KC_SPI_EMAIL_SMTP_STARTTLS`

No todas las opciones están disponibles por env en todas las versiones. Para un tutorial completo y estable, se recomienda **configurar SMTP desde la consola** (Realm settings → Email) y usar las variables solo si tu versión de Keycloak lo documenta.

---

## 11. Resolución de problemas

| Problema | Posible causa | Qué revisar |
|----------|----------------|-------------|
| **Test connection failed** | Credenciales o red | Host, puerto, usuario, contraseña; firewall; en Gmail, contraseña de aplicación y 2FA. |
| **No llega el correo de verificación** | SMTP o bandeja | Spam/correo no deseado; que **Verify email** esté ON; que el usuario se haya registrado con un correo correcto. |
| **Gmail: "Less secure app"** | Políticas de Google | No uses “menos seguros”; usa **contraseña de aplicación** con 2FA. |
| **Mailtrap: no aparece el correo** | Inbox o credenciales | Que estés en la pestaña correcta del inbox; que Host/User/Password en Keycloak coincidan con los de Mailtrap. |
| **From no válido** | Restricciones del proveedor | Gmail/Outlook suelen exigir From = cuenta autenticada; en Mailtrap en desarrollo puedes usar cualquier From. |

---

## 12. Resumen rápido

1. **Realm settings** → **Email**: rellenar Host, Port, Encryption, From, Username, Password.
2. **Save** y **Test connection**.
3. **Realm settings** → **Login**: activar **Verify email** si quieres verificación tras registro.
4. Probar registrando un usuario y/o usando “Olvidé mi contraseña”.
5. Para desarrollo sin enviar correos reales, usar **Mailtrap**; para producción, **Gmail** (con contraseña de aplicación), **Outlook** o un proveedor SMTP de tu dominio.

Con esto tienes el flujo completo de SMTP en Keycloak para envío de emails (verificación, reset de contraseña, etc.). Para más detalles del realm y del cliente, usa `KEYCLOAK-REALM-CLIENT.md`; para Docker y servicios, `DOCKER-KEYCLOAK.md`.
