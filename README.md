# Actividad 6 - Brazo robótico dibujando números

Sistema de interacción entre un **ESP32, un teclado matricial 4x4, una pantalla LCD 16x2 mediante I2C y una simulación robótica en PyBullet**.

El usuario introduce un número utilizando el teclado conectado al ESP32. El número aparece en la pantalla LCD y, al presionar `#`, es enviado al computador mediante comunicación USB.

Python recibe la información, genera digitalmente el número mediante OpenCV, obtiene sus contornos y transforma dichos puntos en una trayectoria para que el brazo robótico, definido mediante un archivo URDF, reproduzca el número sobre una pizarra virtual en PyBullet.

## ¿Qué hace el proyecto?

El sistema integra hardware, comunicación serial, procesamiento de imágenes y simulación robótica.

El funcionamiento puede resumirse de la siguiente manera:

```text
┌──────────────────────┐
│   Teclado matricial  │
│         4x4          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│       ESP32          │
│   MicroPython        │
└──────────┬───────────┘
           │
           ├──────────────► LCD 16x2 I2C
           │
           │ USB / UART
           ▼
┌──────────────────────┐
│        Python        │
│       PySerial       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│       OpenCV         │
│  Generación del      │
│      número          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Cinemática inversa   │
│      del brazo       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│       PyBullet       │
│  Brazo robótico +    │
│      pizarra         │
└──────────────────────┘
```

## Secuencia de operación

El proceso completo se desarrolla en varias etapas:

1. El ESP32 inicia el teclado matricial y el LCD.
2. El usuario introduce un número de hasta cuatro cifras.
3. Cada cifra aparece en la pantalla LCD.
4. La tecla `*` permite eliminar la última cifra.
5. Al presionar `#`, el ESP32 transmite el número al computador.
6. Python recibe el mensaje mediante el puerto serial.
7. OpenCV genera una representación gráfica del número.
8. Se obtienen los contornos de los caracteres.
9. Los puntos del contorno se convierten en coordenadas físicas.
10. La cinemática inversa determina los movimientos necesarios de las articulaciones.
11. PyBullet ejecuta la trayectoria.
12. La pinza del brazo recorre la superficie de la pizarra.
13. El trazo se representa tanto en PyBullet como en una ventana de OpenCV.
14. Al terminar, el dibujo se guarda como una imagen PNG.
15. Python puede enviar nuevamente información al ESP32 para actualizar el LCD.

## Teclado matricial

Se utiliza un teclado matricial de cuatro filas por cuatro columnas.

La distribución implementada en MicroPython es:

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

Cada tecla tiene una función determinada:

| Tecla | Función |
|---|---|
| `0` a `9` | Agregar una cifra |
| `*` | Eliminar la última cifra |
| `#` | Enviar el número para dibujarlo |
| `A` | Repetir el último número |
| `B` | Limpiar la pizarra |
| `C` | Llevar el brazo a posición HOME |
| `D` | Limpiar el número mostrado en el LCD |

El programa permite introducir como máximo cuatro cifras. Esta restricción se encuentra definida mediante:

```python
MAX_CIFRAS = 4
```

La lógica de las teclas y sus funciones está implementada en `main.py`. :contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3}

## Conexiones del ESP32

### LCD 16x2 mediante I2C

| LCD | ESP32 |
|---|---|
| SDA | GPIO 21 |
| SCL | GPIO 22 |
| VCC | 5 V / VIN |
| GND | GND |

La comunicación I2C se configura a:

```python
I2C(
    0,
    sda=Pin(21),
    scl=Pin(22),
    freq=100000
)
```

El programa realiza un escaneo del bus I2C para detectar el dispositivo conectado. :contentReference[oaicite:4]{index=4}

El controlador del LCD contempla las direcciones habituales:

```text
0x27
0x3F
```

y también puede utilizar otra dirección detectada en el bus. :contentReference[oaicite:5]{index=5}

### Teclado 4x4

Las filas utilizan:

| Fila | GPIO |
|---|---|
| F1 | GPIO 13 |
| F2 | GPIO 14 |
| F3 | GPIO 27 |
| F4 | GPIO 26 |

Las columnas utilizan:

| Columna | GPIO |
|---|---|
| C1 | GPIO 25 |
| C2 | GPIO 33 |
| C3 | GPIO 32 |
| C4 | GPIO 23 |

El teclado utiliza las resistencias `PULL_UP` internas del ESP32. :contentReference[oaicite:6]{index=6}

La configuración utilizada en el programa es:

```python
FILAS = [Pin(n, Pin.OUT, value=1)
         for n in (13, 14, 27, 26)]

COLUMNAS = [Pin(n, Pin.IN, Pin.PULL_UP)
            for n in (25, 33, 32, 23)]
```

## Comunicación ESP32 - computador

La información enviada desde el ESP32 utiliza la comunicación USB/UART proporcionada por MicroPython.

Cuando el usuario presiona `#`, el programa genera un mensaje como:

```text
NUM:123
```

Este mensaje es interpretado por Python como una orden para dibujar el número.

Las órdenes adicionales utilizan el siguiente formato:

```text
CMD:A
CMD:B
CMD:C
```

Por ejemplo:

```text
NUM:2026
```

indica que debe dibujarse el número `2026`.

Mientras que:

```text
CMD:B
```

indica que la pizarra debe limpiarse.

La comunicación desde Python hacia el ESP32 también permite enviar mensajes destinados al LCD utilizando:

```text
LCD:texto
```

El programa de MicroPython recibe estos mensajes y muestra el texto en la segunda línea de la pantalla. :contentReference[oaicite:7]{index=7}

## Prueba individual del teclado y LCD

Antes de ejecutar todo el sistema es posible utilizar:

```text
prueba_teclado.py
```

Este programa permite verificar independientemente el funcionamiento del teclado y del bus I2C.

Al ejecutarlo en Thonny muestra:

- Dispositivos encontrados en el bus I2C.
- Estado de las columnas del teclado.
- Fila correspondiente a cada tecla.
- Columna correspondiente a cada tecla.
- Tecla detectada.

:contentReference[oaicite:8]{index=8}

Para las columnas en reposo se espera:

```text
1 1 1 1
```

Si alguna permanece en `0` sin presionar una tecla, se debe revisar el cableado correspondiente. :contentReference[oaicite:9]{index=9}

## Controlador del LCD

El archivo:

```text
lcd_i2c.py
```

contiene el controlador para el LCD 16x2 basado en el controlador HD44780 y un módulo PCF8574.

El programa trabaja con una comunicación I2C de cuatro bits y permite:

- Inicializar el LCD.
- Limpiar la pantalla.
- Mover el cursor.
- Escribir texto.
- Escribir una línea completa.

:contentReference[oaicite:10]{index=10}

La función utilizada por el programa principal para mostrar información es:

```python
lcd.linea(fila, texto)
```

## Generación del número

Una vez recibido el número en Python, no se utiliza una imagen previamente almacenada.

El programa genera el carácter utilizando OpenCV:

```python
cv2.putText()
```

Posteriormente obtiene sus contornos mediante:

```python
cv2.findContours()
```

El modo utilizado permite obtener tanto contornos externos como huecos internos de los números.

Esto es importante para caracteres como:

```text
0
4
6
8
9
```

ya que algunos contienen zonas internas que también deben formar parte de la representación.

El proceso de generación de los trazos se encuentra implementado en:

```text
dibujar_brazo_teclado.py
```

:contentReference[oaicite:11]{index=11}

## Transformación de imagen a trayectoria

Los puntos obtenidos mediante OpenCV inicialmente se encuentran expresados en coordenadas de imagen.

El programa realiza una transformación para convertirlos en posiciones sobre la pizarra virtual.

La función:

```python
pizarra_a_mundo()
```

convierte las coordenadas de la pizarra en coordenadas tridimensionales:

```text
Imagen
  ↓
Contorno
  ↓
Coordenadas de pizarra
  ↓
Coordenadas X,Y,Z
  ↓
Trayectoria del brazo
```

La posición de la pizarra se define mediante parámetros geométricos como:

```python
X_PIZARRA = 0.48
PIZ_ANCHO = 0.40
PIZ_ALTO = 0.28
```

Estos valores corresponden a las dimensiones utilizadas dentro de la simulación. :contentReference[oaicite:12]{index=12}

## Cinemática inversa

El brazo utiliza una configuración de tres grados principales:

```text
joint_1
joint_2
joint_gripper
```

El programa calcula los valores necesarios para llevar la punta de la pinza hasta cada punto de la trayectoria.

La función principal es:

```python
cinematica_inversa(punto)
```

Esta función recibe una posición:

```text
(x, y, z)
```

y obtiene:

```text
q1 → articulación de giro
q2 → articulación del brazo
d  → extensión de la pinza
```

La implementación utiliza:

```python
q1 = math.atan2(v[1], v[0])

q2 = math.atan2(
    math.hypot(v[0], v[1]),
    v[2]
)

d = r - L0
```

Los resultados son limitados de acuerdo con los rangos definidos para las articulaciones. :contentReference[oaicite:13]{index=13}

## Simulación en PyBullet

El archivo URDF contiene el modelo utilizado para representar el brazo robótico.

Python carga el modelo mediante:

```python
p.loadURDF(
    os.path.join(CARPETA, "brazo.urdf"),
    [0, 0, BASE_Z],
    useFixedBase=True
)
```

El programa identifica automáticamente las articulaciones disponibles en el archivo URDF.

Posteriormente utiliza control de posición para llevar cada articulación hacia el objetivo calculado. :contentReference[oaicite:14]{index=14}

La pinza se utiliza como punto de referencia para determinar la posición real de la punta del brazo:

```python
def punta():
    ...
```

De esta manera el programa puede determinar cuándo la punta se encuentra sobre la superficie de la pizarra. :contentReference[oaicite:15]{index=15}

## Dibujo sobre la pizarra

La simulación incorpora una pizarra vertical ubicada frente al brazo.

Cuando la punta entra en contacto con la zona de dibujo, el programa genera segmentos utilizando:

```python
p.addUserDebugLine()
```

Al mismo tiempo, el trazo se reproduce en una ventana de OpenCV denominada:

```text
Lienzo
```

Por tanto, el resultado puede observarse en dos representaciones:

```text
             Trayectoria
                 │
        ┌────────┴────────┐
        ▼                 ▼
   PyBullet             OpenCV
   Pizarra              Lienzo
        │                 │
        └────────┬────────┘
                 ▼
          dibujo_<numero>.png
```

El lienzo se guarda automáticamente al finalizar el dibujo. :contentReference[oaicite:16]{index=16}

## Modos de ejecución

El programa permite diferentes formas de iniciar la actividad.

### Ejecución normal

Conectar la ESP32 y ejecutar:

```bash
python dibujar_brazo_teclado.py
```

### Especificar el puerto

Si la ESP32 se encuentra en otro puerto:

```bash
python dibujar_brazo_teclado.py --puerto COM5
```

### Modo demostración

El programa también dispone de un modo que permite trabajar sin la ESP32:

```bash
python dibujar_brazo_teclado.py --demo
```

En este caso se utiliza el teclado del computador para introducir los comandos.

### Dibujar directamente un número

También es posible indicar directamente el número:

```bash
python dibujar_brazo_teclado.py --numero 2026
```

El programa dibuja el número y finaliza después de completar la operación.

Estas opciones están implementadas mediante argumentos de línea de comandos. :contentReference[oaicite:17]{index=17}

## Puerto de comunicación

El programa tiene configurado inicialmente:

```python
PUERTO_SERIE = "COM3"
BAUDRATE = 115200
```

Si Windows asigna otro puerto al ESP32, puede indicarse desde la terminal:

```bash
python dibujar_brazo_teclado.py --puerto COM6
```

Antes de ejecutar Python se debe cerrar Thonny para liberar el puerto de comunicación.

## Instalación de dependencias

Las bibliotecas necesarias para el programa de Python son:

```bash
pip install pybullet pyserial opencv-python numpy
```

Las principales herramientas utilizadas son:

```text
PyBullet
PySerial
OpenCV
NumPy
MicroPython
Thonny
```

## Archivos del proyecto

La estructura recomendada es:

```text
.
├── README.md
│
├── ESP32/
│   ├── main.py
│   └── lcd_i2c.py
│
├── Python/
│   ├── dibujar_brazo_teclado.py
│   ├── prueba_teclado.py
│   └── brazo.urdf
│
└── resultados/
    └── dibujo_<numero>.png
```

### `main.py`

Programa principal de MicroPython.

Se encarga del teclado, LCD, lectura de comandos y comunicación con el computador. :contentReference[oaicite:18]{index=18}

### `lcd_i2c.py`

Controlador del LCD 16x2 mediante el expansor PCF8574. :contentReference[oaicite:19]{index=19}

### `prueba_teclado.py`

Programa de diagnóstico para verificar el teclado y la comunicación I2C. :contentReference[oaicite:20]{index=20}

### `dibujar_brazo_teclado.py`

Programa principal del computador. Integra PySerial, OpenCV, NumPy y PyBullet para convertir el número recibido en una trayectoria robótica. :contentReference[oaicite:21]{index=21}

### `brazo.urdf`

Modelo del brazo robótico utilizado por PyBullet.

## Ejemplo de funcionamiento

Supongamos que se desea dibujar:

```text
2026
```

El usuario realiza:

```text
2 → 0 → 2 → 6 → #
```

El LCD muestra progresivamente:

```text
Numero: 2
Numero: 20
Numero: 202
Numero: 2026
```

Al presionar:

```text
#
```

la ESP32 envía:

```text
NUM:2026
```

Python recibe el comando y genera los contornos correspondientes.

Posteriormente:

```text
2026
 ↓
Contornos OpenCV
 ↓
Puntos de trayectoria
 ↓
Cinemática inversa
 ↓
Movimientos de joint_1
joint_2
joint_gripper
 ↓
Dibujo en PyBullet
```

Al terminar se genera:

```text
dibujo_2026.png
```

## Comandos disponibles

| Comando | Resultado |
|---|---|
| `NUM:1234` | Dibujar el número recibido |
| `CMD:A` | Repetir el último dibujo |
| `CMD:B` | Limpiar la pizarra |
| `CMD:C` | Llevar el brazo a HOME |
| `LCD:texto` | Mostrar texto en el LCD |

La lógica correspondiente a las órdenes `A`, `B` y `C` se encuentra en el procesamiento principal de Python. :contentReference[oaicite:22]{index=22}

## Consideraciones

- El archivo `brazo.urdf` debe estar disponible para PyBullet.
- El puerto serial no debe estar siendo utilizado simultáneamente por Thonny y Python.
- El LCD requiere alimentación, GND y las líneas SDA/SCL correctamente conectadas.
- El teclado necesita las ocho líneas correspondientes a sus cuatro filas y cuatro columnas.
- La posición y dimensiones de la pizarra forman parte de la geometría de la simulación.
- El brazo debe tener las articulaciones esperadas por el programa.
- Los números se generan dinámicamente mediante OpenCV, no mediante imágenes previamente almacenadas.

## Resultado esperado

Al finalizar la actividad se obtiene un sistema en el que una entrada realizada físicamente mediante el teclado matricial controla una simulación robótica.

El resultado final integra:

```text
Entrada física
     ↓
Teclado 4x4
     ↓
ESP32 + MicroPython
     ↓
LCD
     ↓
Comunicación USB
     ↓
Python
     ↓
OpenCV
     ↓
Cinemática inversa
     ↓
PyBullet
     ↓
Brazo robótico
     ↓
Dibujo del número
```

El proyecto demuestra la integración entre dispositivos embebidos, comunicación serial, procesamiento de imágenes y simulación de robots.

## Autor

Desarrollado por <Mafe Peñuela> — [@mafer1608-7](https://github.com/mafer1608-7)
