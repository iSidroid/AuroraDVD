# Sprint 02 — Gestión de unidad óptica

## 1. Objetivo

Implementar la primera capa de gestión de la unidad óptica en AuroraDVD, permitiendo detectar la unidad disponible, consultar su estado y controlar la bandeja.

Este sprint debe dejar preparada la arquitectura necesaria para que, posteriormente, AuroraDVD pueda detectar y reproducir contenido DVD.

---

## 2. Contexto

Durante el Sprint 01 se construyó y modularizó la interfaz principal de AuroraDVD, incluyendo la barra de menús, acciones de la aplicación y componentes principales de la ventana.

Como parte de las pruebas iniciales se verificó que el sistema operativo permite identificar correctamente la unidad óptica disponible. En el entorno de desarrollo, la unidad fue detectada como:

```text
E:
```

El Sprint 02 toma esta funcionalidad como punto de partida.

---

## 3. Alcance

### 3.1 Detección de unidad óptica

* [ ] Detectar automáticamente las unidades ópticas disponibles.
* [ ] Identificar la letra o ruta de la unidad.
* [ ] Permitir trabajar con más de una unidad óptica en el futuro.
* [ ] Manejar correctamente el caso en que no exista ninguna unidad óptica.

### 3.2 Estado de la unidad

* [ ] Determinar si la unidad está disponible.
* [ ] Determinar si existe un medio insertado.
* [ ] Diferenciar entre unidad disponible y unidad sin medio.
* [ ] Preparar la detección futura del tipo de medio.

### 3.3 Control de bandeja

* [ ] Implementar apertura de la bandeja.
* [ ] Implementar cierre de la bandeja cuando el sistema operativo lo permita.
* [ ] Encapsular el control de la unidad en una capa de servicio.
* [ ] Evitar que la interfaz gráfica contenga lógica específica del sistema operativo.

### 3.4 Integración con la interfaz

* [ ] Crear las acciones correspondientes.
* [ ] Integrar las acciones con la interfaz principal.
* [ ] Agregar la opción "Abrir bandeja unidad óptica".
* [ ] Agregar posteriormente la opción de cerrar bandeja si corresponde.
* [ ] Mostrar información útil al usuario cuando no exista una unidad óptica disponible.
* [ ] Mantener la lógica de acciones separada de los componentes visuales.

---

## 4. Arquitectura

La interacción con la unidad óptica seguirá inicialmente esta dirección:

```text
UI
 │
 ▼
ApplicationActions
 │
 ▼
OpticalDriveService
 │
 ▼
Sistema operativo
```

La interfaz gráfica no deberá encargarse directamente de ejecutar operaciones específicas de Windows.

El objetivo es mantener una separación clara entre:

* **UI:** presentación e interacción con el usuario.
* **Actions:** acciones disponibles en AuroraDVD.
* **Services:** comunicación con el sistema operativo.
* **Core:** constantes, modelos y lógica común.

---

## 5. Estructura prevista

Se evaluará incorporar un servicio específico para la unidad óptica:

```text
src/
└── auroradvd/
    ├── core/
    │   ├── constants.py
    │   └── ...
    │
    ├── services/
    │   ├── optical_drive_service.py
    │   └── ...
    │
    └── ui/
        ├── actions.py
        ├── menu_bar.py
        ├── main_window.py
        └── ...
```

El nombre y responsabilidad definitiva de los módulos se validarán durante la implementación.

---

## 6. Criterios de aceptación

El Sprint 02 se considerará completado cuando:

* [ ] AuroraDVD pueda identificar correctamente la unidad óptica disponible.
* [ ] La unidad pueda ser consultada desde un servicio independiente de la UI.
* [ ] AuroraDVD pueda solicitar la apertura de la bandeja.
* [ ] Las acciones estén correctamente conectadas con la interfaz.
* [ ] El sistema maneje adecuadamente la ausencia de una unidad óptica.
* [ ] El código mantenga la separación entre UI, acciones y servicios.
* [ ] Las funcionalidades principales hayan sido probadas en el entorno real.
* [ ] Los cambios estén documentados mediante commits de Git.

---

## 7. Pruebas

Se realizarán como mínimo las siguientes pruebas:

### Prueba 1 — Detección

**Condición:**
Unidad óptica conectada.

**Resultado esperado:**

```text
Unidad detectada: E:
```

### Prueba 2 — Sin unidad óptica

**Condición:**
No existe una unidad óptica disponible.

**Resultado esperado:**

AuroraDVD informa correctamente que no existe una unidad óptica disponible y no genera un error inesperado.

### Prueba 3 — Apertura de bandeja

**Condición:**
Unidad óptica disponible.

**Acción:**
Ejecutar "Abrir bandeja unidad óptica".

**Resultado esperado:**

La bandeja de la unidad óptica se abre correctamente.

### Prueba 4 — Medio insertado

**Condición:**
DVD insertado.

**Resultado esperado:**

AuroraDVD puede determinar que existe un medio disponible.

La identificación y reproducción del contenido DVD completo quedará para un sprint posterior.

---

## 8. Fuera de alcance

Para evitar ampliar innecesariamente el sprint, las siguientes funcionalidades no forman parte del Sprint 02:

* Reproducción completa de DVD.
* Navegación por menús DVD.
* Decodificación de video.
* Selección de pistas de audio.
* Selección de subtítulos.
* Reproducción de archivos ISO.
* Gestión avanzada de múltiples unidades.
* Interfaz avanzada de selección de dispositivos.

Estas funcionalidades serán abordadas en futuros sprints.

---

## 9. Git

Cada funcionalidad importante deberá validarse antes de realizar el commit.

Convención prevista:

```text
feat(optical): detect optical drive
feat(optical): add tray control
feat(ui): add optical drive actions
test(optical): validate optical drive detection
```

Al finalizar el sprint se realizará un commit que represente el cierre funcional del Sprint 02.

---

## 10. Estado del Sprint

**Estado:** 🟢 Completado

### Progreso

* [x] Sprint 02 creado.
* [x] Detectar automáticamente las unidades ópticas.
* [x] Identificar la unidad óptica `E:`.
* [x] Crear `OpticalDriveService`.
* [x] Implementar apertura de bandeja.
* [x] Implementar cierre de bandeja.
* [x] Integrar la acción "Abrir bandeja unidad óptica" con la UI.
* [x] Integrar la acción "Cerrar bandeja unidad óptica" con la UI.
* [x] Detectar presencia de medio mediante `QStorageInfo`.
* [x] Implementar `is_dvd_video()`.
* [x] Robustecer la validación de estructuras DVD-Video.
* [x] Implementar `get_media_info()`.
* [x] Integrar información del medio en la interfaz.
* [x] Probar unidad óptica sin medio.
* [x] Probar DVD-Video real.
* [x] Probar DVD de datos real.
* [x] Probar ruta/unidad no disponible.
* [x] Verificar etiqueta del medio.
* [x] Verificar capacidad reportada por Windows.
* [x] Realizar pruebas adicionales de inserción y extracción de medios.
* [x] Documentar resultados finales.
* [x] Realizar commits funcionales.
* [x] Realizar push de los cambios a `origin/dev`.
* [x] Cerrar Sprint 02.

### Pruebas realizadas

#### DVD-Video

```text
Unidad:        E:/
Etiqueta:      G3
Medio:         Presente
Tamaño:        4,574,199,808 bytes
DVD-Video:     True
```

Estructura detectada:

```text
E:\
├── AUDIO_TS\
├── JACKET_P\
└── VIDEO_TS\
    ├── VIDEO_TS.BUP
    ├── VIDEO_TS.IFO
    ├── VIDEO_TS.VOB
    ├── VTS_01_0.BUP
    ├── VTS_01_0.IFO
    ├── VTS_01_0.VOB
    ├── VTS_01_1.VOB
    ├── VTS_01_2.VOB
    ├── VTS_01_3.VOB
    └── VTS_01_4.VOB
```

Resultado:

```text
has_media()     → True
is_dvd_video()  → True
```

#### DVD de datos

```text
Unidad:        E:/
Etiqueta:      varios
Medio:         Presente
Tamaño:        1,831,108,608 bytes
DVD-Video:     False
```

Resultado:

```text
has_media()     → True
is_dvd_video()  → False
```

#### Unidad sin medio

Resultado:

```text
has_media()      → False
is_dvd_video()   → False

get_media_info()
    ready        → False
    label        → ""
    size         → 0
    is_dvd_video → False
```

#### Ruta/unidad no disponible

Se probó una ruta no existente (`Z:\`) para validar el comportamiento cuando no existe una unidad disponible.

Resultado:

```text
has_media: False
is_dvd_video: False

get_media_info:
    ready        → False
    label        → ""
    size         → 0
    is_dvd_video → False
```

No se generaron excepciones inesperadas.

#### Control de bandeja

Se realizaron pruebas físicas con la unidad `E:`:

```text
Abrir bandeja                  → Correcto
Cerrar bandeja                 → Correcto
Abrir/cerrar repetidamente     → Correcto
Cerrar bandeja sin medio       → Correcto
```

#### Actualización de información del medio

Se verificó la actualización de la barra de estado después de las operaciones de bandeja:

```text
DVD-Video:
DVD-Video | G3 | E:\ | 4.26 GB

DVD de datos:
DVD de datos | varios | E:\ | 1.71 GB

Sin medio:
No hay ningún medio insertado
```

La actualización posterior al cierre de la bandeja utiliza una única ejecución diferida para dar tiempo al sistema operativo a montar el medio. No se utiliza polling permanente.

### Estado técnico final

`OpticalDriveService` dispone actualmente de las siguientes operaciones:

```text
get_optical_drives()
    → Detecta unidades ópticas.

has_media(drive)
    → Determina si existe un medio insertado.

is_dvd_video(drive)
    → Valida una estructura DVD-Video básica.

get_media_info(drive)
    → Obtiene información básica del medio.

eject(drive)
    → Abre la bandeja de la unidad.

close_tray(drive)
    → Cierra la bandeja de la unidad.
```

### Integración con la interfaz

Las siguientes acciones están disponibles en AuroraDVD:

```text
Abrir bandeja unidad óptica
Cerrar bandeja unidad óptica
```

La información del medio se presenta mediante la barra de estado.

La arquitectura mantiene la separación:

```text
UI
 │
 ▼
ApplicationActions
 │
 ▼
OpticalDriveService
 │
 ▼
Sistema operativo
```

### Trabajo futuro

Las siguientes funcionalidades quedan fuera del cierre del Sprint 02:

* Soporte avanzado para múltiples unidades ópticas.
* Selección de unidad óptica desde la interfaz.
* Validación profunda del contenido binario de archivos IFO.
* Detección y análisis completo de títulos DVD.
* Reproducción del contenido DVD.
* Navegación por menús DVD.

Estas funcionalidades serán abordadas en futuros sprints.

### Commits funcionales

Los principales bloques del Sprint 02 quedaron registrados mediante los siguientes commits:

```text
5ee709b  feat(optical): add optical media detection
f2d472b  feat(optical): add tray control
7104b0f  feat(optical): robust dvd video validation
0d2fa38  feat(ui): show optical media information
```

Todos los cambios funcionales fueron enviados a:

```text
origin/dev
```

---

## 11. Resultado esperado

Al finalizar el Sprint 02, AuroraDVD deberá contar con una primera capa funcional de comunicación con la unidad óptica del equipo.

Esta capa será la base sobre la cual se construirá posteriormente la detección de medios DVD y, finalmente, el sistema de reproducción.

> **Principio del proyecto:** primero controlar correctamente el dispositivo; después interpretar su contenido; finalmente reproducirlo.
