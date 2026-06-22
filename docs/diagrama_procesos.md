# Diagrama de Procesos - SecureSab

## 1. Proceso Principal: Registro de Asistencia Biométrica

```
                    [INICIO]
                       |
                       v
            +---------------------+
            | Aprendiz coloca     |
            | huella dactilar     |
            +---------------------+
                       |
                       v
            +---------------------+
            | Hikvision valida    |
            | huella biométrica   |
            +---------------------+
                       |
                       v
                < ¿Coincide ?>  ---- NO --> [Registrar fallo en HistorialFallos]
                       |
                      SI
                       |
                       v
            +---------------------+
            | Webhook recibe      |
            | evento HTTP POST    |
            +---------------------+
                       |
                       v
                < ¿Usuario existe ?>  ---- NO --> [Registrar evento desconocido]
                       |
                      SI
                       |
                       v
            +---------------------+
            | Registrar asistencia|
            | en AsistenciaSede   |
            +---------------------+
                       |
                       v
            +---------------------+
            | Actualizar cache    |
            | monitoreo tiempo    |
            | real                |
            +---------------------+
                       |
                       v
                      [FIN]
```

## 2. Proceso: Registro de Asistencia en Ambiente (Instructor)

```
                    [INICIO]
                       |
                       v
            +---------------------+
            | Instructor selecciona|
            | ficha y competencia |
            +---------------------+
                       |
                       v
            +---------------------+
            | Sistema muestra     |
            | lista de aprendices |
            | con estado actual   |
            +---------------------+
                       |
                       v
            +---------------------+
            | Instructor marca    |
            | asistencia por      |
            | aprendiz:           |
            | Asistió/Inasistió/  |
            | Retardo             |
            +---------------------+
                       |
                       v
                < ¿Alumno sin    ---- SI --> [Auto-seleccionar Inasistencia]
                asistencia sede ?>
                       |
                      NO
                       |
                       v
            +---------------------+
            | Instructor envía    |
            | formulario POST     |
            +---------------------+
                       |
                       v
            +---------------------+
            | Servicio            |
            | registrar_asistencia|
            | guarda registros    |
            +---------------------+
                       |
                       v
            +---------------------+
            | Sistema verifica    |
            | alertas:            |
            | - 3 inasistencias   |
            |   consecutivas      |
            | - 5+ inasistencias  |
            | - 3+ retardos       |
            |   consecutivos      |
            +---------------------+
                       |
                < ¿Hay alertas ?>  ---- NO --> [Redirigir a gestión]
                       |
                      SI
                       |
                       v
            +---------------------+
            | Mostrar alertas en  |
            | interfaz            |
            +---------------------+
                       |
                       v
                < ¿Instructor desea  ---- NO --> [Redirigir a gestión]
                enviar correos ?>
                       |
                      SI
                       |
                       v
            +---------------------+
            | Seleccionar aprendices|
            | con inasistencia    |
            +---------------------+
                       |
                       v
            +---------------------+
            | Servicio            |
            | enviar_correos_     |
            | inasistencia envía  |
            | correos masivos     |
            +---------------------+
                       |
                       v
            +---------------------+
            | Mostrar resultado:  |
            | enviados/fallidos/  |
            | sin_correo          |
            +---------------------+
                       |
                       v
                      [FIN]
```

## 3. Proceso: Gestión de Justificaciones (Instructor)

```
                    [INICIO]
                       |
                       v
            +---------------------+
            | Instructor accede a |
            | gestión de          |
            | justificaciones     |
            +---------------------+
                       |
                       v
            +---------------------+
            | Sistema muestra     |
            | justificaciones con |
            | filtros: ficha,     |
            | jornada, estado,    |
            | fecha, aprendiz     |
            +---------------------+
                       |
                       v
                < ¿Hay justificaciones  ---- NO --> [Mostrar mensaje vacío]
                pendientes ?>
                       |
                      SI
                       |
                       v
            +---------------------+
            | Instructor revisa   |
            | documento soporte   |
            | y motivo            |
            +---------------------+
                       |
                       v
                < ¿Aprueba o  ---- RECHAZAR --> +---------------------+
                rechaza?                        | Servicio procesar_   |
                       |                       | acción_justificación |
                      APROBAR                   | cambia estado a      |
                       |                        | "Rechazado"          |
                       v                        +---------------------+
            +---------------------+                    |
            | Servicio procesar_  |                    v
            | acción_justificación|              [Registrar actividad]
            | cambia estado a     |                    |
            | "Aprobado"          |                    v
            +---------------------+              [Redirigir]
            | Actualiza           |
            | AsistenciaAmbiente  |
            | a "Justificada"     |
            +---------------------+
                       |
                       v
              [Registrar actividad]
                       |
                       v
                 [Redirigir]
```

## 4. Proceso: Envío de Correos de Inasistencia (Coordinador)

```
                    [INICIO]
                       |
                       v
            +---------------------+
            | Coordinador accede  |
            | a asistencia en     |
            | ambiente            |
            +---------------------+
                       |
                       v
            +---------------------+
            | Aplica filtros:     |
            | ficha, fecha,       |
            | estado, instructor  |
            +---------------------+
                       |
                       v
            +---------------------+
            | Sistema muestra     |
            | registros con       |
            | checkboxes para     |
            | inasistentes        |
            +---------------------+
                       |
                       v
            +---------------------+
            | Coordinador         |
            | selecciona          |
            | aprendices          |
            | inasistentes        |
            +---------------------+
                       |
                       v
            +---------------------+
            | Clic "Enviar correos|
            | a inasistentes"     |
            +---------------------+
                       |
                       v
                < ¿Confirma envío ?>  ---- NO --> [No hace nada]
                       |
                      SI
                       |
                       v
            +---------------------+
            | AJAX POST a         |
            | /coordinador/       |
            | enviar-correos/     |
            +---------------------+
                       |
                       v
            +---------------------+
            | Servicio            |
            | enviar_correos_     |
            | inasistencia envía  |
            | correos HTML        |
            | individuales        |
            +---------------------+
                       |
                       v
            +---------------------+
            | Mostrar modal con   |
            | resultado:          |
            | enviados/fallidos/  |
            | sin_correo          |
            +---------------------+
                       |
                       v
                      [FIN]
```

## 5. Proceso: Consulta Detallada por Aprendiz (Coordinador)

```
                    [INICIO]
                       |
                       v
            +---------------------+
            | Coordinador accede  |
            | a asistencia en     |
            | ambiente o sede     |
            +---------------------+
                       |
                       v
            +---------------------+
            | Clic "Ver detalle"  |
            | en un aprendiz      |
            +---------------------+
                       |
                       v
            +---------------------+
            | Sistema carga vista |
            | detallada:          |
            | - Perfil del        |
            |   aprendiz          |
            | - Estadísticas      |
            |   (asistencias,     |
            |   inasistencias,    |
            |   retardos,         |
            |   justificadas)     |
            | - Historial         |
            |   ambiente por      |
            |   competencia/      |
            |   instructor/fecha  |
            | - Historial sede    |
            |   (entrada/salida)  |
            | - Justificaciones   |
            +---------------------+
                       |
                       v
                      [FIN]
```

## 6. Proceso: Recuperación de Contraseña

```
                    [INICIO]
                       |
                       v
            +---------------------+
            | Usuario ingresa    |
            | correo electrónico |
            +---------------------+
                       |
                       v
                < ¿Correo existe ?>  ---- NO --> [Mensaje: correo no encontrado]
                       |
                      SI
                       |
                       v
            +---------------------+
            | Generar código 6    |
            | dígitos aleatorio   |
            +---------------------+
                       |
                       v
            +---------------------+
            | Enviar correo con   |
            | código de           |
            | verificación        |
            +---------------------+
                       |
                       v
            +---------------------+
            | Usuario ingresa    |
            | código recibido    |
            +---------------------+
                       |
                       v
                < ¿Código correcto ?>  ---- NO --> [Mensaje: código incorrecto]
                       |
                      SI
                       |
                       v
            +---------------------+
            | Generar token       |
            | seguro (SHA-256)    |
            +---------------------+
                       |
                       v
            +---------------------+
            | Usuario ingresa    |
            | nueva contraseña    |
            +---------------------+
                       |
                       v
            +---------------------+
            | Actualizar          |
            | contraseña en BD    |
            +---------------------+
                       |
                       v
                      [FIN]
```

## 7. Proceso: Creación de Usuario (Gestor)

```
                    [INICIO]
                       |
                       v
            +---------------------+
            | Gestor accede a    |
            | crear usuario      |
            +---------------------+
                       |
                       v
                < Método de creación ?>
                /                      \
           Manual                   CSV Masivo
              |                         |
              v                         v
    +-----------------+      +-----------------+
    | Llenar formulario|    | Subir archivo   |
    | con datos del    |    | CSV con usuarios|
    | nuevo usuario    |    |                 |
    +-----------------+      +-----------------+
              |                         |
              v                         v
    +-----------------+      +-----------------+
    | Servicio        |    | Servicio        |
    | crear_usuario() |    | crear_usuario() |
    | en BD           |    | por cada fila   |
    +-----------------+      +-----------------+
              |                         |
              v                         v
    +-----------------+      +-----------------+
    | Sincronizar con |    | Sincronizar con |
    | Hikvision       |    | Hikvision       |
    | (ISAPI PUT)     |    | (ISAPI PUT)     |
    +-----------------+      +-----------------+
              |                         |
              v                         v
    +-----------------+      +-----------------+
    | Enviar correo   |    | Enviar correos  |
    | con credenciales|    | con credenciales|
    | al usuario      |    | a cada usuario  |
    +-----------------+      +-----------------+
              |                         |
              v                         v
    +-----------------+      +-----------------+
    | Registrar       |    | Registrar       |
    | actividad       |    | actividad       |
    +-----------------+      +-----------------+
              |                         |
              v                         v
              +--------> [FIN] <--------+
```

## 8. Compuertas y Decisiones

| Compuerta | Tipo | Condiciones | Salidas |
|-----------|------|-------------|---------|
| ¿Coincide huella? | Exclusive (XOR) | Sí / No | 2 ramas |
| ¿Usuario existe? | Exclusive (XOR) | Sí / No | 2 ramas |
| ¿Sin asistencia sede? | Exclusive (XOR) | Sí / No | 2 ramas |
| ¿Hay alertas? | Exclusive (XOR) | Sí / No | 2 ramas |
| ¿Enviar correos? | Exclusive (XOR) | Sí / No | 2 ramas |
| ¿Aprueba o rechaza? | Exclusive (XOR) | Aprobar / Rechazar | 2 ramas |
| ¿Correo existe? | Exclusive (XOR) | Sí / No | 2 ramas |
| ¿Código correcto? | Exclusive (XOR) | Sí / No | 2 ramas |
| Método de creación | Exclusive (XOR) | Manual / CSV | 2 ramas |
| ¿Confirma envío? | Exclusive (XOR) | Sí / No | 2 ramas |

## Notas para corrección del diagrama original

1. **Las compuertas (condicionales) SIEMPRE deben llevar a funcionalidades**, no a interfaces. Ejemplo correcto: "¿Usuario existe?" → SI → "Registrar asistencia". Ejemplo incorrecto: "¿Usuario existe?" → SI → "Pantalla de asistencia".

2. **Cada actividad/funcionalidad debe tener un nombre descriptivo** que inicie con verbo en infinitivo o sustantivo: "Registrar asistencia", "Enviar correo", "Validar huella".

3. **Los flujos deben ser completos**: cada compuerta debe tener todas sus ramas definidas, y cada rama debe llegar a un punto final o a una nueva funcionalidad.

4. **No mezclar niveles de abstracción**: el diagrama principal debe mostrar los procesos generales. Los diagramas detallados de cada proceso se muestran por separado.
