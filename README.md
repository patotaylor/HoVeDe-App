# HoVeDe — Horas, Vencimientos y Descanso

Aplicación web desarrollada como trabajo práctico de Ingeniería de Software en ISTEA.

HoVeDe permite registrar vuelos, consultar información de vuelos reales mediante una API externa y realizar cálculos de actividad y descanso de tripulaciones.

**Tecnologías:** Python, Flask, PostgreSQL 17, HTML, CSS, Git y Docker.

## Funcionalidades

### Libro de vuelo
- Registrar vuelos indicando fecha, matrícula, origen, destino y horas de vuelo.
- Consultar los vuelos registrados.
- Editar registros existentes.
- Eliminar vuelos mediante borrado lógico, conservando los datos en PostgreSQL.
- Validar el formato de matrícula argentina `LV-XXX`.

### Calculadora de actividad y descanso
- Ingresar fechas y horarios de presentación, primer despegue y último aterrizaje.
- Calcular los tiempos de actividad y descanso según las reglas implementadas en el prototipo académico.
- Consultar vuelos mediante AeroDataBox para completar información automáticamente.

**Importante:** los cálculos son parte de un proyecto académico y no reemplazan procedimientos operativos ni verificaciones de normativa vigente.

## Arquitectura

HoVeDe utiliza dos servicios:

- **Flask:** aplicación web y lógica de negocio.
- **PostgreSQL:** almacenamiento de vuelos.

Ambos servicios se ejecutan en contenedores Docker separados y se comunican mediante una red privada creada automáticamente por Docker Compose.

Los datos se almacenan en un volumen Docker para conservarlos cuando los contenedores se detienen o recrean.

## Estructura del proyecto

```text
HoVeDe-App/
├── src/
│   ├── app.py
│   ├── calculadora.py
│   ├── api_vuelos.py
│   ├── templates/
│   └── static/
├── database/
│   └── init.sql
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── .dockerignore
├── .env.example
├── .gitignore
└── README.md
```

## Instalación y ejecución con Docker

### Requisitos

- Docker Desktop instalado y en ejecución.
- Conexión a Internet para descargar las imágenes y dependencias durante la primera construcción.
- Puerto `5000` disponible.

**No es necesario instalar Python, Flask ni PostgreSQL en la computadora.**

### 1. Obtener el proyecto

Descargar el repositorio desde:

https://github.com/patotaylor/HoVeDe-App

Se puede utilizar la opción **Code → Download ZIP** de GitHub y descomprimirlo.

También se puede clonar mediante Git, si está instalado:

```powershell
git clone https://github.com/patotaylor/HoVeDe-App.git
```

Abrir una terminal en la carpeta `HoVeDe-App`, donde se encuentra `compose.yaml`.

### 2. Iniciar HoVeDe

Ejecutar:

```powershell
docker compose up -d --build
```

Docker realizará automáticamente las siguientes operaciones:

1. Descargará la imagen de PostgreSQL 17 si es necesario.
2. Construirá la imagen de la aplicación utilizando el `Dockerfile`.
3. Creará una red privada y un volumen para la base de datos.
4. Inicializará PostgreSQL mediante `database/init.sql`.
5. Iniciará Flask cuando PostgreSQL esté preparado.

La primera ejecución puede tardar algunos minutos, según la conexión a Internet.

### 3. Abrir la aplicación

Ingresar desde el navegador a:

**http://localhost:5000**

La aplicación funciona sin configurar una clave de RapidAPI. En ese caso, la búsqueda automática de vuelos no estará disponible, pero el libro de vuelo y la calculadora manual sí.

### 4. Comprobar los contenedores

```powershell
docker compose ps
```

Deberían aparecer los servicios `db` y `web`, ambos en ejecución.

Para consultar registros:

```powershell
docker compose logs --tail 30 web
```

### 5. Detener la aplicación

```powershell
docker compose down
```

Este comando detiene y elimina los contenedores del proyecto, pero **conserva los datos del volumen PostgreSQL**.

Para iniciarla nuevamente:

```powershell
docker compose up -d
```

**Precaución:** `docker compose down -v` también elimina el volumen y puede borrar los vuelos almacenados.

## Configuración de AeroDataBox

HoVeDe utiliza **AeroDataBox**, a través de RapidAPI, para consultar información real de vuelos.

### Clave de demostración incluida

Durante el período de evaluación, el proyecto incluye una API Key temporal de demostración en el archivo `.env.example`.

Docker Compose carga este archivo automáticamente. Por lo tanto, **no es necesario configurar ninguna clave para probar la búsqueda de vuelos**.

Para iniciar HoVeDe con la integración habilitada:

```powershell
docker compose up -d --build
```

La clave de demostración tiene una disponibilidad limitada y será revocada cuando finalice la evaluación.

### Utilizar una API Key propia

Una vez revocada la clave de demostración, se puede obtener una API Key de AeroDataBox desde RapidAPI.

Para configurarla con la versión actual del proyecto:

1. Abrir el archivo `.env.example`.
2. Reemplazar el valor de `RAPIDAPI_KEY` por la nueva clave.
3. Guardar el archivo.
4. Aplicar el cambio ejecutando:

```powershell
docker compose up -d --force-recreate web
```

**Seguridad:** `.env.example` es un archivo público del repositorio. Si se utiliza una clave personal, el cambio debe permanecer exclusivamente en la computadora local y no debe subirse nuevamente a GitHub.

### Funcionamiento sin API Key

Si no se dispone de una clave válida, la búsqueda automática de vuelos no estará disponible.

Sin embargo, el resto de HoVeDe continuará funcionando normalmente:

- Registro, consulta, edición y eliminación de vuelos.
- Almacenamiento de datos en PostgreSQL.
- Calculadora manual de actividad y descanso.

La disponibilidad de las consultas depende del servicio AeroDataBox y de los límites de la suscripción de RapidAPI.

**Fuente de información aeronáutica:** AeroDataBox — https://www.aerodatabox.com/

## Construcción y ejecución mediante Docker CLI

Además del procedimiento recomendado con Compose, la imagen de Flask puede construirse individualmente:

```powershell
docker build -t hovede-web .
```

Para ejecutar la aplicación con `docker run`, primero debe existir un servicio PostgreSQL accesible. Se puede crear mediante Compose:

```powershell
docker compose up -d db
```

Esto inicia únicamente PostgreSQL y crea la red privada `hovede_default`.

Con el puerto `5000` libre, ejecutar:

```powershell
docker run --rm --name hovede-web-manual --network hovede_default -p 5000:5000 -e DB_HOST=db -e DB_NAME=hovede -e DB_USER=hovede -e DB_PASSWORD=hovede_demo_local hovede-web
```

Luego abrir:

http://localhost:5000

Este ejemplo utiliza la contraseña local de demostración predeterminada en `compose.yaml`. Si se configuró otra contraseña en `.env`, debe utilizarse la misma en `docker run`.

Para detener el contenedor iniciado manualmente, presionar `Ctrl + C`.

## Desinstalación y limpieza

Para eliminar HoVeDe de una computadora después de probarlo, abrir una terminal en la carpeta del proyecto.

### Eliminar contenedores, red, datos e imagen de HoVeDe

Ejecutar:

```powershell
docker compose down --volumes --rmi local --remove-orphans
```

Este comando elimina los contenedores del proyecto, su red, el volumen de PostgreSQL y las imágenes locales del proyecto que Docker Compose pueda eliminar.

**Advertencia: esta operación elimina permanentemente los vuelos guardados en la base de datos de HoVeDe.**

### Eliminar los archivos del proyecto

Cerrar la terminal y eliminar la carpeta `HoVeDe-App` descargada o descomprimida.

Si se clonó con Git, también se puede eliminar esa carpeta. No es necesario desinstalar Git.

### ¿Qué puede permanecer instalado?

Docker Desktop sigue instalado, así como las imágenes base compartidas o descargadas de Docker Hub, como `postgres:17` y `python:3.13-slim`, y algunas capas de caché de construcción.

No se recomienda ejecutar `docker system prune -a --volumes` como parte de la desinstalación de HoVeDe, porque podría eliminar recursos de otros proyectos.

Este procedimiento no desinstala Docker Desktop ni modifica otros proyectos existentes.