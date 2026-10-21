# TeloConnect ERP

Módulo académico de gestión de órdenes de Back Office y despachos de Almacén, desarrollado para Odoo 18. El proyecto permite registrar y dar seguimiento a órdenes, validar datos básicos, preparar equipos para el técnico y documentar el resultado de la visita de instalación.

> **Datos de prueba:** los archivos CSV del repositorio son datos sintéticos generados por `generate_data.py`. Los nombres, DNI, teléfonos, direcciones y eventos son simulados; no representan clientes ni operaciones reales. El dataset no se sincroniza con las órdenes de Odoo.

## Alcance funcional

### Back Office

- Registro de órdenes con información de cliente, ubicación, coordenadas y equipos solicitados.
- Flujo de revisión: borrador, validación, devolución para corrección, aprobación o rechazo por Back Office.
- Generación de un despacho de Almacén al aprobar una orden.
- Registro del resultado de la visita: instalación realizada, visita reprogramada o instalación no realizada.
- Para una visita no completada, captura de categoría y observación. La reprogramación requiere la fecha informada por el técnico.
- Catálogo administrable de categorías de resultado. Las categorías inactivas dejan de estar disponibles para nuevas selecciones.
- Registro de la fecha real cuando la orden se marca como instalada.

### Almacén y trazabilidad

- Despacho relacionado con la orden de Back Office.
- Asignación de técnico o cuadrilla y entrega de equipos al técnico.
- Registro de identificadores o series para ONT, decodificadores y repetidores.
- Validación de formato y cantidad de identificadores al entregar los equipos, y prevención de series duplicadas en otros despachos.
- Historial analítico de cambios y estados de la orden y del despacho.

### Límites explícitos

Este proyecto **no es un CRM ni un sistema de ventas de call center**. No incluye captura de llamadas, campañas, leads, oportunidades, seguimiento de asesores, cotizaciones ni un proceso comercial para originar ventas. Las órdenes se ingresan directamente en el módulo de Back Office.

Tampoco incluye integración con Claro u otro sistema externo. En particular, las fechas de reprogramación deben ingresarse en TeloConnect según la información que comunique el técnico; no se importan automáticamente. El registro logístico de series y entrega no reemplaza una implementación completa de Inventario, compras, valoración de existencias o control de almacenes de Odoo.

Crear órdenes en Odoo **no agrega filas** a los CSV. Estos son archivos separados, estáticos y sintéticos para ejercicios de análisis; no constituyen una exportación de la base de datos operativa.

## Tecnología

- Odoo 18.0 (imagen oficial `odoo:18.0`)
- PostgreSQL 15 (imagen oficial `postgres:15`)
- Docker Compose
- Addon `teloconnect_erp`, con dependencias de Odoo `base`, `mail` y `stock`

El módulo se encuentra en `addons/teloconnect_erp/`. El manifest declara la versión `18.0.1.0.4`.

## Requisitos para ejecutar localmente

- Git para clonar el repositorio.
- Docker Desktop con WSL 2 en Windows, o Docker Engine en Linux/macOS.
- Docker Compose V2 (`docker compose`, con espacio).
- Conexión a Internet la primera vez para descargar las imágenes.
- Puerto local `8069` disponible.
- Como referencia para las imágenes de Odoo y PostgreSQL y los volúmenes locales, disponer de al menos 4 GB de memoria y 5 GB de espacio libre.
- Un navegador web actualizado.

No es necesario instalar Odoo, PostgreSQL ni paquetes Python en el sistema anfitrión. Python 3 solo es necesario si se desea ejecutar el generador CSV; el módulo Python de Odoo se ejecuta dentro del contenedor.

## Preparar la configuración

Desde una terminal, clona el repositorio y entra en la carpeta del proyecto:

```powershell
git clone https://github.com/ingAntonioValladares/teloconnect-erp-odoo18.git
Set-Location teloconnect-erp-odoo18
```

Crea los archivos locales de configuración copiando las plantillas.

En Windows PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item odoo.conf.example odoo.conf
```

En Linux o macOS:

```sh
cp .env.example .env
cp odoo.conf.example odoo.conf
```

Edita `.env` y reemplaza `POSTGRES_PASSWORD` por una clave propia. Luego edita `odoo.conf`: reemplaza `admin_passwd` por una contraseña maestra propia y configura `db_password` con el mismo valor de `POSTGRES_PASSWORD` de `.env`. El usuario de base de datos de `odoo.conf` (`db_user`) debe coincidir con `POSTGRES_USER`.

Tanto `.env` como `odoo.conf` son archivos locales excluidos de Git: **no los publiques ni compartas sus valores**. Las plantillas versionadas solo contienen valores de ejemplo. La contraseña `admin_passwd` es la contraseña maestra que Odoo solicita para crear o administrar bases de datos; no es la contraseña del usuario de inicio de sesión de Odoo.

Compose usa `.env` para configurar PostgreSQL y entrega esos mismos datos al contenedor de Odoo. `odoo.conf` configura la conexión de Odoo y su contraseña maestra.

## Iniciar el proyecto

En la carpeta que contiene `docker-compose.yml`:

```powershell
docker compose up -d
docker compose ps
```

La primera ejecución descarga las imágenes y puede tardar unos minutos. Cuando ambos servicios estén activos, abre [http://localhost:8069](http://localhost:8069).

### Crear la base de datos e instalar la aplicación

En una instalación nueva:

1. En la pantalla de Odoo, crea una base de datos. Usa un nombre como `teloconnect_erp_2026`.
2. Cuando Odoo solicite la contraseña maestra, ingresa el valor de `admin_passwd` que configuraste en `odoo.conf`.
3. Define el correo y contraseña del usuario administrador de esa base de datos; son credenciales propias de Odoo y distintas de las de PostgreSQL y de la contraseña maestra.
4. Abre **Aplicaciones**. Si TeloConnect no aparece, activa el modo desarrollador y selecciona **Actualizar lista de aplicaciones**.
5. Busca **TeloConnect ERP** e instala el módulo.

El addon se monta dentro del contenedor desde `./addons`, y sus dependencias de Odoo se cargan junto con la instalación.

## Comandos de operación

Ejecuta todos los comandos desde la carpeta del proyecto.

```powershell
# Iniciar o crear los contenedores en segundo plano
docker compose up -d

# Ver estado de los servicios
docker compose ps

# Ver logs de Odoo en tiempo real (Ctrl+C cierra la lectura de logs)
docker compose logs -f web

# Detener los contenedores sin borrar la base de datos
docker compose stop

# Volver a iniciarlos
docker compose start

# Detener y eliminar los contenedores; los volúmenes y datos se conservan
docker compose down
```

### Actualizar el addon

Después de cambiar el código del addon, actualiza la lista de aplicaciones en Odoo y actualiza **TeloConnect ERP** desde la interfaz de Aplicaciones. Si necesitas usar la línea de comandos, detén primero el servicio web:

```powershell
docker compose stop web
docker compose run --rm web odoo --config=/etc/odoo/odoo.conf -d teloconnect_erp_2026 -u teloconnect_erp --stop-after-init
docker compose start web
```

Reemplaza `teloconnect_erp_2026` por el nombre que elegiste al crear la base. Si el comando de actualización falla, revisa sus logs y vuelve a iniciar el servicio web antes de continuar.

### Borrar la base de datos local y empezar de nuevo

> **Advertencia:** el siguiente comando elimina los volúmenes de PostgreSQL y Odoo, incluida la base de datos local. No lo uses si necesitas conservar información.

```powershell
docker compose down -v
docker compose up -d
```

Después tendrás que volver a crear la base de datos e instalar el addon. Si cambias los datos de `.env` cuando ya existe un volumen de PostgreSQL, el contenedor no cambia automáticamente las credenciales de ese volumen. Para un entorno local descartable, `down -v` lo vuelve a inicializar con las variables nuevas; para conservar datos, realiza una migración de credenciales y una copia de seguridad antes de cambiar.

## Pruebas

El addon incluye pruebas transaccionales de Odoo para validaciones, flujo de estados, despacho, series de equipos, historial y resultados de instalación. Para ejecutar la suite contra una base de desarrollo existente:

```powershell
docker compose stop web
docker compose run --rm web odoo --config=/etc/odoo/odoo.conf -d teloconnect_erp_2026 -u teloconnect_erp --test-enable --test-tags /teloconnect_erp --stop-after-init
docker compose start web
```

Utiliza el nombre real de tu base de datos. El proceso actualiza el addon en esa base y ejecuta sus pruebas; para evitar modificar una base con información importante, usa una base local de pruebas.

## Dataset sintético

Los archivos analíticos se encuentran en:

- `historial_backoffice_eventos_3years.csv`
- `almacen_despachos_3years.csv`

Contienen datos simulados para pruebas y análisis, no información real de clientes. En la versión actual, el historial cubre del 1 de enero de 2023 al 19 de octubre de 2026 y los despachos del 2 de enero de 2023 al 19 de octubre de 2026. `generate_data.py` es un generador de CSV y no importa información a Odoo. El rango generado está acotado por las fechas configuradas en el propio script; al alcanzar la fecha final, el script termina sin añadir registros.

Para ejecutar el generador (opcional, requiere Python 3):

```powershell
python generate_data.py
```

El generador modifica los CSV del directorio actual. Si quieres conservar los archivos existentes, haz una copia antes de ejecutarlo. Los datos generados no son una fuente oficial ni un respaldo de la base de Odoo.

## Estructura principal

```text
addons/teloconnect_erp/
  data/       Categorías iniciales de resultados de instalación
  models/     Back Office, Almacén, categorías e historial analítico
  security/   Accesos y grupos del módulo
  tests/      Pruebas transaccionales de Odoo
  views/      Formularios, listas y menús
docker-compose.yml
odoo.conf
generate_data.py
*.csv         Dataset sintético de análisis
```

## Seguridad y uso público

- No agregues `.env` al repositorio. Comparte únicamente `.env.example`, que contiene valores de muestra.
- El historial de Git contiene versiones anteriores de la configuración con credenciales de desarrollo. Trátalas como expuestas: no las reutilices y cámbialas en cualquier entorno que aún dependa de ellas. Actualizar los archivos actuales no elimina valores de commits anteriores.
- La configuración de Compose es para desarrollo local, no para producción. Antes de publicar el servicio en una red, configura secretos seguros, TLS, copias de seguridad, control de acceso y endurecimiento del servidor.
- Los puertos del ejemplo se enlazan a `127.0.0.1`, por lo que la aplicación queda limitada al equipo local.

## Licencia

El addon declara licencia LGPL-3 en su manifest. Revisa las licencias de Odoo y de cualquier componente externo antes de redistribuir una instalación o derivados.
