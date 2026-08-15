# AuroraDVD — Retrospectiva Sprint 1

**Estado:** Completado  
**Rama:** `dev` → `main`  
**PR:** #2  
**Commit principal:** `d0319a8`  
**Fecha:** Agosto 2026

# AuroraDVD — Retrospectiva Sprint 1

## 1. Objetivo del Sprint

El objetivo principal del Sprint 1 fue establecer una base sólida para AuroraDVD, construyendo la ventana principal de la aplicación, su estructura modular de interfaz y las primeras acciones funcionales.

El sprint también buscó establecer un flujo de desarrollo ordenado utilizando Git, ramas de desarrollo y Pull Requests.

## 2. Logros alcanzados

### Arquitectura y estructura

* Se estableció la estructura modular del proyecto utilizando Python y PySide6.
* Se separaron las responsabilidades de la ventana principal, menú, barra de herramientas, barra de estado, widgets y servicios.
* Se estableció `ApplicationActions` como punto central para las acciones globales de la aplicación.
* Se incorporó `OpticalDriveService` para separar la lógica relacionada con las unidades ópticas de la interfaz gráfica.

### Interfaz

* Se implementó la ventana principal de AuroraDVD.
* Se implementó el menú principal.
* Se implementó el menú `Archivo`.
* Se incorporó la barra de herramientas.
* Se incorporó la barra de estado.
* Se implementaron los primeros diálogos de la aplicación.

### Acciones

Actualmente AuroraDVD dispone de las siguientes acciones:

* `Abrir DVD...`
* `Abrir imagen ISO...`
* `Abrir VIDEO_TS`
* `Abrir bandeja unidad óptica`
* `Salir`

### Unidad óptica

Se implementó detección de unidades ópticas en Windows.

Además, se implementó el control real de la bandeja mediante Windows API/MCI.

La funcionalidad fue probada físicamente y se confirmó que AuroraDVD puede detectar la unidad `E:\` y abrir su bandeja desde la interfaz gráfica.

Este fue el primer punto en que AuroraDVD pasó de ser solamente una interfaz a ejecutar una operación real sobre el sistema.

## 3. Git y flujo de desarrollo

Durante el Sprint 1 se estableció el siguiente flujo:

```text
dev
 │
 ├── desarrollo
 ├── pruebas
 ├── commit
 └── push
       │
       ▼
 Pull Request
       │
       ▼
     main
```

Se creó y utilizó la rama `dev` para el desarrollo.

También se realizó el Pull Request:

`feat(optical-drive): add tray eject action`

El PR fue fusionado correctamente a `main`.

Commit principal del cambio:

`d0319a8 — feat(optical-drive): add tray eject action`

Actualmente:

```text
dev  → d0319a8
main → 62ec630
```

El repositorio local quedó sincronizado con GitHub y con:

`nothing to commit, working tree clean`

## 4. Lo que aprendimos

### Separación de responsabilidades

Durante el sprint se comprobó la importancia de mantener separadas las responsabilidades:

```text
UI
 │
 ▼
Action
 │
 ▼
MainWindow
 │
 ▼
Service
 │
 ▼
Sistema operativo
```

Esta estructura permitirá incorporar funcionalidades más complejas sin convertir `MainWindow` en un archivo con toda la lógica de la aplicación.

### Desarrollo incremental

Se comprobó que es conveniente implementar una funcionalidad completa de extremo a extremo antes de continuar.

El ejemplo de la bandeja óptica fue especialmente útil:

```text
Acción
  ↓
Menú
  ↓
MainWindow
  ↓
Servicio
  ↓
Windows
  ↓
Hardware
```

Primero se probó el servicio de manera independiente y posteriormente se conectó a la interfaz.

### Git

También se consolidó el uso de:

* ramas de desarrollo;
* commits descriptivos;
* `git status`;
* revisión del staging;
* Pull Requests;
* integración `dev → main`;
* sincronización entre repositorio local y remoto.

Esto nos permitirá mantener `main` como una versión estable mientras `dev` continúa evolucionando.

## 5. Situación de las ramas

La estructura que utilizaremos a partir de ahora será:

```text
GitHub
│
├── main ⭐
│   └── versión estable
│
└── dev 🔧
    └── desarrollo
```

La antigua rama `master` corresponde a una etapa anterior del proyecto y ya no forma parte de nuestro flujo de desarrollo.

## 6. Pendientes identificados

Aunque el Sprint 1 estableció una buena base, varias acciones todavía son principalmente estructuras iniciales:

* `Abrir DVD...` todavía debe evolucionar hacia la detección y selección real de contenido DVD.
* `Abrir imagen ISO...` todavía necesita implementación funcional.
* `Abrir VIDEO_TS` todavía necesita implementación funcional.
* La reproducción de vídeo todavía no está implementada.
* La detección de discos debe evolucionar desde la simple detección de unidades hacia la identificación del contenido.
* La selección de unidad óptica actualmente utiliza la primera unidad disponible.
* Todavía debemos definir claramente el modelo de reproducción y comunicación con VLC.

Estos puntos pasan a formar parte de la planificación futura y no deben considerarse fallos del Sprint 1.

## 7. Conclusión del Sprint 1

El Sprint 1 cumplió su objetivo principal: establecer una base funcional y mantenible para AuroraDVD.

AuroraDVD ya dispone de:

* una arquitectura modular;
* una interfaz gráfica funcional;
* acciones centralizadas;
* servicios independientes;
* control real de una unidad óptica;
* sistema de desarrollo basado en Git;
* ramas `main` y `dev`;
* integración mediante Pull Requests.

El proyecto deja de ser solamente un prototipo visual y comienza a convertirse en una aplicación funcional.

### Hito del Sprint 1

> **“Todo empezó con una ventana vacía.”**

Al finalizar este sprint, esa ventana ya puede interactuar con el sistema operativo y controlar físicamente una unidad óptica.

## 8. Propuesta para Sprint 2

El objetivo recomendado para el siguiente sprint será:

**“Detectar, identificar y preparar el contenido de un DVD para su reproducción.”**

Esto nos llevará desde:

```text
Unidad óptica
     ↓
DVD insertado
     ↓
Detección del disco
     ↓
Identificación del contenido
     ↓
Estructura DVD
     ↓
Preparación para reproducción
```

Antes de comenzar la implementación de Sprint 2, se deberá definir su alcance, criterios de aceptación y tareas técnicas.
