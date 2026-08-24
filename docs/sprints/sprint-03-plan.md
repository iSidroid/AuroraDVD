# AuroraDVD

## Sprint 03 — DVD-Video: detección, análisis y preparación de reproducción

**Estado:** Planificado
**Rama:** `dev`

---

## 1. Objetivo

Construir la primera capa funcional de soporte para DVD-Video en AuroraDVD.

Al finalizar este sprint, la aplicación deberá ser capaz de detectar un DVD-Video insertado, validar su estructura `VIDEO_TS`, analizar su contenido básico e identificar los títulos disponibles, dejando preparada una representación de datos que pueda ser utilizada posteriormente por la capa de reproducción.

El objetivo de este sprint no es implementar todavía la reproducción completa del DVD, sino establecer una base sólida y desacoplada para ella.

---

## 2. Contexto

Durante el Sprint 02 se implementó la primera capa de gestión de unidades ópticas, incluyendo:

* Detección de unidades ópticas.
* Detección de medios insertados.
* Consulta del estado de la unidad.
* Control de la bandeja.
* Identificación inicial de DVD-Video mediante la estructura `VIDEO_TS`.
* Obtención de información básica del medio.
* Integración de estas capacidades con la interfaz de usuario.

La arquitectura establecida durante el Sprint 02 seguirá siendo utilizada:

```text
UI
 ↓
ApplicationActions
 ↓
Service
 ↓
Operating System / Filesystem
```

Sprint 03 ampliará esta arquitectura incorporando una capa especializada para el análisis de DVD-Video.

---

## 3. Alcance

### 3.1 Servicio DVD-Video

Crear un nuevo servicio:

```text
src/
└── auroradvd/
    └── services/
        ├── optical_drive_service.py
        └── dvd_video_service.py
```

`DvdVideoService` será responsable de las operaciones relacionadas específicamente con la estructura y contenido de un DVD-Video.

La lógica de análisis no deberá implementarse directamente en la interfaz de usuario.

---

### 3.2 Validación de DVD-Video

El servicio deberá validar que el medio corresponda realmente a una estructura DVD-Video.

Como mínimo deberá considerar:

* Existencia del directorio `VIDEO_TS`.
* Existencia de `VIDEO_TS.IFO`.
* Existencia y coherencia básica de los archivos de títulos.
* Presencia de archivos `.IFO` y `.VOB` correspondientes cuando corresponda.

La validación deberá ser suficientemente robusta para diferenciar un DVD-Video válido de una unidad que simplemente contenga una carpeta denominada `VIDEO_TS`.

---

### 3.3 Análisis del contenido

El servicio deberá obtener información básica del contenido del DVD.

La información podrá incluir:

* Unidad utilizada.
* Etiqueta del medio.
* Tipo de medio.
* Cantidad de títulos detectados.
* Identificación de los conjuntos `VTS`.
* Información básica de los títulos.
* Información disponible sobre capítulos y duración cuando pueda obtenerse de forma fiable.

El análisis deberá diseñarse de manera extensible para permitir incorporar información adicional en futuros sprints.

---

### 3.4 Modelo de datos

Se establecerán modelos de datos específicos para representar la información de un DVD-Video.

Conceptualmente:

```text
DvdVideo
 ├── drive
 ├── label
 ├── titles
 └── metadata

DvdTitle
 ├── number
 ├── vts
 ├── duration
 └── chapters
```

La utilización de modelos permitirá evitar una dependencia excesiva de diccionarios genéricos y facilitará la evolución futura del reproductor.

---

### 3.5 Integración con la aplicación

La información obtenida por `DvdVideoService` deberá poder ser utilizada desde `ApplicationActions`.

Se mantendrá la separación de responsabilidades:

```text
UI
 ↓
ApplicationActions
 ↓
DvdVideoService
 ↓
Filesystem / DVD
```

La interfaz no deberá contener lógica específica para interpretar directamente la estructura `VIDEO_TS`.

---

### 3.6 Integración inicial con la UI

La interfaz podrá mostrar información básica cuando se detecte un DVD-Video.

Como referencia:

```text
DVD detectado

Nombre: Mi película
Tipo: DVD-Video
Títulos: 3
```

La presentación definitiva podrá evolucionar en futuros sprints.

---

## 4. Pruebas

Se incorporarán pruebas automatizadas para validar los principales escenarios.

Como mínimo:

* DVD-Video válido.
* Unidad sin medio.
* Medio que no corresponde a DVD-Video.
* Ausencia del directorio `VIDEO_TS`.
* Ausencia de `VIDEO_TS.IFO`.
* Estructura DVD incompleta.
* DVD con múltiples títulos.
* Presencia de archivos VOB.
* Manejo correcto de rutas de Windows.

Los tests deberán poder ejecutarse sin depender necesariamente de un DVD físico.

Para ello se podrán utilizar estructuras de directorios simuladas, por ejemplo:

```text
test_dvd/
└── VIDEO_TS/
    ├── VIDEO_TS.IFO
    ├── VIDEO_TS.BUP
    ├── VTS_01_0.IFO
    ├── VTS_01_1.VOB
    └── VTS_01_2.VOB
```

---

## 5. Restricciones

Durante este sprint:

* No se implementará todavía la reproducción completa de DVD.
* No se implementará decodificación MPEG-2.
* No se implementará decodificación de audio AC-3/DTS.
* No se implementarán menús interactivos de DVD.
* No se implementará navegación completa por capítulos.
* No se implementará todavía el sistema completo Play/Pause/Stop.
* No se incorporará VLC como dependencia de reproducción.

La arquitectura deberá mantenerse preparada para incorporar posteriormente una capa de reproducción independiente.

---

## 6. Arquitectura objetivo

Al finalizar el sprint, la arquitectura deberá aproximarse a:

```text
                    AuroraDVD
                        │
               ┌────────┴────────┐
               │                 │
              UI             Application
                                 │
                         ApplicationActions
                                 │
                    ┌────────────┴────────────┐
                    │                         │
          OpticalDriveService        DvdVideoService
                    │                         │
                    ▼                         ▼
                Windows                  VIDEO_TS
```

La futura capa de reproducción podrá construirse posteriormente sobre los modelos generados por `DvdVideoService`.

Conceptualmente:

```text
DvdVideoService
       │
       ▼
   DvdVideo
       │
       ▼
   DvdTitle
       │
       ▼
 PlaybackService
       │
       ▼
Decoder / Renderer
```

---

## 7. Definition of Done

El Sprint 03 se considerará completado cuando:

* [ ] Existe `DvdVideoService`.
* [ ] AuroraDVD puede validar una estructura DVD-Video.
* [ ] Puede identificar los títulos disponibles.
* [ ] Existe un modelo de datos para representar el DVD.
* [ ] La información puede ser consultada mediante `ApplicationActions`.
* [ ] La UI puede mostrar información básica del DVD.
* [ ] Existen pruebas automatizadas para los escenarios principales.
* [ ] Las pruebas pueden ejecutarse sin depender de un DVD físico.
* [ ] No se introduce dependencia con VLC.
* [ ] La lógica de DVD-Video permanece fuera de la UI.
* [ ] La documentación del Sprint 03 está actualizada.
* [ ] Todas las pruebas relevantes pasan correctamente.
* [ ] La rama `dev` queda limpia y sincronizada con GitHub.
* [ ] Se realiza el cierre formal del Sprint 03.

---

## 8. Resultado esperado

Al finalizar el Sprint 03, AuroraDVD deberá haber evolucionado desde una aplicación capaz de detectar y gestionar una unidad óptica hacia una aplicación capaz de comprender la estructura básica de un DVD-Video.

El resultado esperado puede resumirse de la siguiente manera:

```text
Sprint 02
"Hay un disco en la unidad."

            ↓

Sprint 03
"El disco contiene un DVD-Video
y podemos identificar su contenido."

            ↓

Futuros sprints
"Podemos reproducirlo."
```

Este sprint establecerá la base técnica necesaria para desarrollar posteriormente el sistema de reproducción de DVD-Video sin acoplar la lógica de análisis del DVD a la interfaz de usuario o a una tecnología específica de reproducción.
