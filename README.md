# Actividad 6 — Comunicación entre dispositivos embebidos, visión y robótica

Actividad dividida en dos partes que integran **ESP32 + MicroPython**, comunicación **USB/UART** y **SPI**, visualización en **LCD 16x2** y **OLED SSD1306**, y procesamiento con **Python**.

| Parte | Tema | Comunicación | Video |
|---|---|---|---|
| **Parte 1** | Teclado 4x4 + LCD → brazo robótico dibujando números en PyBullet | USB/UART (ESP32 ↔ PC) | [`ACTIVIDAD 6.mp4`](ACTIVIDAD%206.mp4) |
| **Parte 2** | Dígito reconocido en el PC → ESP maestro → ESP esclavo → OLED | USB (PC → ESP-A) + **SPI** (ESP-A → ESP-B) | [`ACTIVIDAD 6.2.mp4`](ACTIVIDAD%206.2.mp4) |

## Contenido

- [Estructura del repositorio](#estructura-del-repositorio)
- [Dependencias](#dependencias)
- [Parte 1 — Brazo robótico dibujando números](#parte-1--brazo-robótico-dibujando-números)
- [Parte 2 — Maestro/esclavo SPI con pantalla OLED](#parte-2--maestroesclavo-spi-con-pantalla-oled)
- [Solución de problemas](#solución-de-problemas)
- [Autor](#autor)

---

## Estructura del repositorio

Los archivos del repositorio se encuentran en una sola carpeta. Los tres `main.py` están numerados porque cada uno se carga en una placa distinta:

| Archivo en el repositorio | Se guarda como | Placa / destino | Parte |
|---|---|---|---|
| `main (1).py` | `main.py` | ESP32 (teclado + LCD) | 1 |
| `lcd_i2c.py` | `lcd_i2c.py` | ESP32 (teclado + LCD) | 1 |
| `prueba_teclado.py` | — (se ejecuta desde Thonny) | ESP32 | 1 |
| `dibujar_brazo_teclado.py` | — | Computador | 1 |
| `brazo (1).urdf` | `brazo (1).urdf` (misma carpeta que el script) | Computador | 1 |
| `main (3).py` | `main.py` | **ESP-A** (maestro SPI) | 2 |
| `main (2).py` | `main.py` | **ESP-B** (esclavo SPI + OLED) | 2 |
| `ssd1306.py` | `ssd1306.py` | ESP-B | 2 |

Organización recomendada:

```text
.
├── README.md
├── ACTIVIDAD 6.mp4
├── ACTIVIDAD 6.2.mp4
│
├── Parte1/
│   ├── ESP32/
│   │   ├── main.py                  ← main (1).py
│   │   └── lcd_i2c.py
│   ├── prueba_teclado.py
│   ├── dibujar_brazo_teclado.py
│   └── brazo (1).urdf
│
└── Parte2/
    ├── ESP-A_maestro/
    │   └── main.py                  ← main (3).py
    └── ESP-B_esclavo/
        ├── main.py                  ← main (2).py
        └── ssd1306.py
```

## Dependencias

**En el computador:**

```bash
pip install pybullet pyserial opencv-python numpy
```

**En las placas:** MicroPython y el IDE Thonny para cargar los archivos.

---

# Parte 1 — Brazo robótico dibujando números

El usuario escribe un número en un **teclado matricial 4x4** conectado a un ESP32. El número se muestra en un **LCD 16x2 I2C** y, al presionar `#`, se envía por USB al computador. Python genera el número con **OpenCV**, extrae su contorno, lo convierte en una trayectoria mediante **cinemática inversa** y un brazo definido en un **URDF** lo dibuja sobre una pizarra virtual en **PyBullet**.

## Flujo del sistema

```text
┌──────────────────────┐
│  Teclado matricial   │
│         4x4          │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│       ESP32          │───────► LCD 16x2 I2C
│    MicroPython       │
└──────────┬───────────┘
           │  USB / UART   (NUM:2026)
           ▼
┌──────────────────────┐
│  Python + PySerial   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ OpenCV: putText +    │
│ findContours         │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Cinemática inversa   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ PyBullet: brazo +    │──► Lienzo OpenCV ──► dibujo_<numero>.png
│ pizarra              │
└──────────────────────┘
           │
           └──► "LCD:estado" de vuelta al ESP32
```

## Secuencia de operación

1. El ESP32 inicia el teclado y el LCD.
2. El usuario introduce un número de hasta cuatro cifras, que se ve en el LCD.
3. `*` elimina la última cifra.
4. Al presionar `#`, el ESP32 envía `NUM:<número>` por USB.
5. Python recibe el mensaje y OpenCV genera el número y sus contornos.
6. Los puntos del contorno se convierten en coordenadas 3D sobre la pizarra.
7. La cinemática inversa calcula los movimientos de las articulaciones.
8. PyBullet ejecuta la trayectoria: la punta de la pinza recorre la pizarra.
9. El trazo se dibuja en PyBullet y en la ventana de OpenCV `Lienzo`.
10. Al terminar se guarda `dibujo_<numero>.png` y Python envía el estado al LCD.

## Teclado

```text
┌─────┬─────┬─────┬─────┐
│  1  │  2  │  3  │  A  │
├─────┼─────┼─────┼─────┤
│  4  │  5  │  6  │  B  │
├─────┼─────┼─────┼─────┤
│  7  │  8  │  9  │  C  │
├─────┼─────┼─────┼─────┤
│  *  │  0  │  #  │  D  │
└─────┴─────┴─────┴─────┘
```

| Tecla | Función | Mensaje al PC |
|---|---|---|
| `0` a `9` | Agregar una cifra (máx. `MAX_CIFRAS = 4`) | — |
| `*` | Eliminar la última cifra | — |
| `#` | Enviar el número para dibujarlo | `NUM:123` |
| `A` | Repetir el último dibujo | `CMD:A` |
| `B` | Limpiar la pizarra | `CMD:B` |
| `C` | Llevar el brazo a HOME | `CMD:C` |
| `D` | Limpiar el número escrito en el LCD (solo local) | — |

El teclado se lee con antirrebote de 30 ms y cada pulsación hace parpadear el LED de la placa (GPIO 2).

## Conexiones del ESP32

**LCD 16x2 (I2C)**

| LCD | ESP32 |
|---|---|
| SDA | GPIO 21 |
| SCL | GPIO 22 |
| VCC | 5 V (VIN) |
| GND | GND |

El bus I2C trabaja a 100 kHz. El driver `lcd_i2c.py` prueba las direcciones habituales `0x27` y `0x3F`, o usa la que encuentre en el bus.

**Teclado 4x4** (usa las resistencias `PULL_UP` internas, no requiere externas)

| Filas | F1 | F2 | F3 | F4 |
|---|---|---|---|---|
| GPIO | 13 | 14 | 27 | 26 |

| Columnas | C1 | C2 | C3 | C4 |
|---|---|---|---|---|
| GPIO | 25 | 33 | 32 | 23 |

## Protocolo ESP32 ↔ computador

| Dirección | Mensaje | Resultado |
|---|---|---|
| ESP32 → PC | `NUM:1234` | Dibujar el número |
| ESP32 → PC | `CMD:A` | Repetir el último dibujo |
| ESP32 → PC | `CMD:B` | Limpiar la pizarra |
| ESP32 → PC | `CMD:C` | Llevar el brazo a HOME |
| ESP32 → PC | `TECLA:x` | Diagnóstico (el PC lo ignora) |
| PC → ESP32 | `LCD:texto` | Muestra el texto (máx. 16 caracteres) en la 2.ª línea del LCD |

Velocidad: `115200` baudios. Cada mensaje termina en salto de línea.

## Procesamiento del número (OpenCV)

No se usan imágenes almacenadas: el número se genera dinámicamente.

1. `cv2.putText()` escribe el número en una imagen.
2. `cv2.findContours()` con `RETR_CCOMP` obtiene contornos externos **y huecos internos** (importante en `0, 4, 6, 8, 9`).
3. `cv2.approxPolyDP()` suaviza los escalones y se remuestrea cada `PASO = 4 mm`.
4. Los trazos se ordenan empezando por el más a la izquierda y luego por el más cercano.
5. Se escalan para caber en `ANCHO_UTIL × ALTO_UTIL` (0.30 × 0.17 m) dentro de la pizarra.

## Trayectoria y cinemática inversa

`pizarra_a_mundo(u, v)` transforma coordenadas de la pizarra en un punto 3D:

```text
Imagen → Contorno → Coordenadas de pizarra (u, v) → (x, y, z) → Trayectoria
```

Parámetros de la pizarra:

```python
X_PIZARRA = 0.48               # distancia del hombro a la pizarra
PIZ_ANCHO, PIZ_ALTO = 0.40, 0.28
```

El brazo (`brazo (1).urdf`) es de tipo **R-R-P** (esférico):

| Articulación | Tipo | Rango | Función |
|---|---|---|---|
| `joint_1` | Revoluta | ±2.5 rad | Giro de la base |
| `joint_2` | Revoluta | ±2.0 rad | Inclinación del brazo |
| `joint_gripper` | Prismática | 0 – 0.15 m | Extensión de la pinza |
| `joint_dedo_izq` / `joint_dedo_der` | Prismáticas | — | Dedos (cerrados, hacen de “lápiz”) |

La función `cinematica_inversa(punto)` recibe `(x, y, z)` y devuelve `q1`, `q2` y la extensión `d`:

```python
q1 = math.atan2(v[1], v[0])
q2 = math.atan2(math.hypot(v[0], v[1]), v[2])
d  = r - L0
```

Los valores se limitan a los rangos de cada articulación y, si algún punto queda fuera de alcance, el programa lo avisa en consola.

Para **subir y bajar el lápiz**, la punta se aleja `LEVANTE = 3 cm` de la pizarra, desciende en 5 pasos y se levanta al terminar cada trazo. Al llegar y salir, la pinza se recoge (`d = 0`) para que la punta nunca roce la pizarra.

## Simulación y dibujo

- PyBullet carga el URDF con `p.loadURDF(..., useFixedBase=True)` y controla las articulaciones por posición.
- La posición real de la punta se obtiene con la cinemática directa de PyBullet (`punta()`).
- Cuando la punta está a menos de 3 mm de la pizarra, y dentro de la zona blanca, se genera tinta con `p.addUserDebugLine()` y la misma línea se dibuja en la ventana OpenCV `Lienzo`.
- Al terminar el dibujo se guarda `dibujo_<numero>.png`.

Por defecto la pizarra se borra antes de cada número (`BORRAR_ANTES_DE_DIBUJAR = True`). Si se pone en `False`, los números se acumulan hasta pulsar `B`.

## Ejecución

**1. Cargar en el ESP32** (con Thonny): `main (1).py` guardado como `main.py` y `lcd_i2c.py`.

**2. Verificar el hardware** (opcional): abrir `prueba_teclado.py` en Thonny y ejecutarlo con ▶. Muestra los dispositivos I2C encontrados (el LCD debe aparecer como `0x27` o `0x3f`), el estado de las columnas en reposo (deben ser `1 1 1 1`) y la fila, columna y tecla de cada pulsación.

**3. Cerrar Thonny** para liberar el puerto serial y ejecutar en el computador:

```bash
python dibujar_brazo_teclado.py                 # ESP32 en PUERTO_SERIE (COM3 por defecto)
python dibujar_brazo_teclado.py --puerto COM5   # otro puerto
python dibujar_brazo_teclado.py --demo          # sin ESP32, usando el teclado del PC
python dibujar_brazo_teclado.py --numero 2026   # dibuja un número, guarda la imagen y termina
python dibujar_brazo_teclado.py --sin-gui       # PyBullet en modo DIRECT (sin ventana)
```

En **modo demo** se escribe en la ventana `Lienzo`: dígitos, `Enter`/`#` para dibujar, `*`/Retroceso para borrar, `a` repetir, `b` borrar pizarra, `c` home, `q` salir. Si no se puede abrir el puerto serial, el programa entra en modo demo automáticamente.

## Ejemplo: dibujar `2026`

```text
Teclas:   2 → 0 → 2 → 6 → #

LCD:      Numero: 2_ → Numero: 20_ → Numero: 202_ → Numero: 2026
ESP32 →   NUM:2026
Python →  contornos → trayectoria → cinemática inversa → PyBullet
LCD:      Dibujando 2026 → Listo! 2026
Archivo:  dibujo_2026.png
```

---

# Parte 2 — Maestro/esclavo SPI con pantalla OLED

Un computador identifica un dígito (red neuronal **CNN** sobre la imagen de la cámara) y lo envía por USB a una primera placa (**ESP-A, maestro SPI**). Esta lo reenvía por **SPI** a una segunda placa (**ESP-B, esclavo SPI**), que verifica la trama, responde con un **ACK/NAK** y muestra el dígito en grande, con su porcentaje de confianza, en una **pantalla OLED SSD1306 128x64**.

## Flujo del sistema

```text
┌────────────────────┐   USB    ┌────────────────────┐   SPI    ┌────────────────────┐
│    Computador      │  DIG:7,98│  ESP-A (maestro)   │ 5 bytes  │  ESP-B (esclavo)   │
│  cámara + CNN      │ ───────► │  SoftSPI 2 kHz     │ ───────► │  esclavo por       │
│                    │ ◄─────── │  reintentos x3     │ ◄─────── │  software          │
└────────────────────┘ SPI:OK 7 └────────────────────┘ ACK/NAK  └─────────┬──────────┘
                                                                           │ I2C
                                                                           ▼
                                                                  OLED SSD1306 128x64
```

## Protocolo PC → ESP-A (USB)

Líneas de texto terminadas en salto de línea, a 115200 baudios:

| Mensaje | Significado |
|---|---|
| `DIG:7,98` | Dígito `7` con una confianza del 98 % (se limita a 100) |
| `DIG:-` | No hay ningún dígito frente a la cámara |

Respuestas de la ESP-A hacia el PC:

| Respuesta | Significado |
|---|---|
| `SPI:OK 7` | El esclavo confirmó la trama con ACK |
| `SPI:ERROR 7` | Sin ACK tras 3 intentos |
| `SPI:DATO INVALIDO …` | El mensaje recibido era incorrecto (dígito fuera de 0–9, formato erróneo) |

## Trama SPI (5 bytes)

| Byte | Contenido | Valor |
|---|---|---|
| 0 | Inicio | `0xA5` |
| 1 | Dígito | `0`–`9`, o `0xFF` si no hay dígito |
| 2 | Confianza | `0`–`100` (%) |
| 3 | Checksum | `0xA5 ^ dígito ^ confianza` (XOR) |
| 4 | Relleno / **respuesta** | El maestro envía `0x00`; el esclavo contesta por MISO `0x06` (**ACK**) o `0x15` (**NAK**) |

El esclavo calcula el checksum al recibir los primeros cuatro bytes y devuelve el resultado durante el quinto, por lo que el maestro conoce el resultado de la misma transacción (full-duplex).

## Maestro — ESP-A (`main (3).py`)

- Usa **`SoftSPI`** a **2 kHz**, modo 0 (`polarity=0, phase=0`).
- Lee sin bloquear las líneas `DIG:` del USB.
- Baja `CS`, espera 3 ms, envía la trama con `write_readinto()` y libera `CS`.
- Si no recibe `ACK`, **reintenta hasta 3 veces** con 80 ms de espera entre intentos.
- Enciende un LED (GPIO 4) mientras envía.

## Esclavo — ESP-B (`main (2).py`)

MicroPython no incluye modo esclavo SPI por hardware, por lo que el protocolo se implementa **leyendo directamente las líneas del bus** (modo 0). Por esa razón el reloj del maestro es tan lento:

1. Un flanco de bajada en `CS` indica el inicio de una trama.
2. En cada **flanco de subida de SCK** se lee un bit de MOSI (MSB primero).
3. Antes de cada flanco de subida se coloca en MISO el bit correspondiente de la respuesta.
4. Si `CS` sube antes de completar los 5 bytes, la trama se descarta.
5. Al terminar se valida el byte de inicio y el checksum y se actualiza la pantalla.

**Pantalla OLED**

| Situación | Se muestra |
|---|---|
| Al iniciar | “Esperando al maestro…” |
| Trama válida con dígito | Dígito grande (fuente propia 5x7 ampliada ×6), etiqueta `CNN`, confianza en tamaño ×2 y contador `#n` de tramas |
| Trama válida sin dígito (`0xFF`) | “Sin dígito frente a la cámara” |
| Trama con error | No se actualiza la pantalla; la consola muestra los bytes recibidos |

## Conexiones

Pines de una placa **ESP32-S3**:

**Bus SPI entre las placas** (conexión directa, mismo nombre en ambos lados)

| Señal | ESP-A (maestro) | ESP-B (esclavo) |
|---|---|---|
| CS | GPIO 10 | GPIO 10 |
| SCK | GPIO 12 | GPIO 12 |
| MOSI | GPIO 11 | GPIO 11 |
| MISO | GPIO 13 | GPIO 13 |
| GND | GND | GND *(común, obligatorio)* |

**OLED SSD1306 (I2C)** — solo en la ESP-B

| OLED | ESP-B |
|---|---|
| SDA | GPIO 8 |
| SCL | GPIO 9 |
| VCC | 3V3 |
| GND | GND |

## Ejecución

1. **ESP-B:** guardar `main (2).py` como `main.py` y `ssd1306.py`. Al arrancar muestra “Esperando al maestro…”.
2. **ESP-A:** guardar `main (3).py` como `main.py`. La consola indica `ESP-A lista: maestro SPI`.
3. Conectar el bus SPI y GND según la tabla.
4. Desde el computador, enviar los mensajes `DIG:` por el puerto serial de la ESP-A. Para una prueba rápida sin cámara se puede escribir directamente `DIG:5,97` en la consola de Thonny conectada a la ESP-A.
5. Verificar que la OLED de la ESP-B muestre el dígito y la confianza, y que la ESP-A responda `SPI:OK 5`.

---

## Solución de problemas

| Problema | Posible causa / solución |
|---|---|
| Python no puede abrir el puerto | Thonny aún lo tiene abierto: cerrarlo. Indicar el puerto con `--puerto COMx` |
| El LCD no muestra nada | Revisar VCC (5 V), GND, SDA=21 y SCL=22. Ejecutar `prueba_teclado.py` para ver si el bus I2C detecta `0x27`/`0x3f`. El programa sigue funcionando sin LCD |
| Columnas del teclado en `0` en reposo | Corto o pin equivocado en esa columna |
| El brazo no dibuja o falla al cargar | Verificar que el archivo URDF del brazo esté junto al script |
| “Puntos fuera del alcance” | Reducir `ANCHO_UTIL`/`ALTO_UTIL` o acercar `X_PIZARRA` |
| `SPI:ERROR` en la ESP-A | Revisar cableado SPI, GND común y que la ESP-B esté en marcha. Conviene encender primero la ESP-B |
| La OLED no se actualiza | Revisar SDA/SCL (GPIO 8/9) y la dirección I2C `0x3C` |

## Autor

Desarrollado por **Mafe Peñuela** — [@mafer1608-7](https://github.com/mafer1608-7)
