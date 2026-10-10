from machine import Pin, SoftSPI
import sys
import select
import time

# Reloj SPI lento (2 kHz) para que el esclavo en MicroPython alcance
# a leer cada bit: MicroPython no trae modo esclavo por hardware.
spi = SoftSPI(baudrate=2000, polarity=0, phase=0,
              sck=Pin(12), mosi=Pin(11), miso=Pin(13))
cs = Pin(10, Pin.OUT, value=1)       # CS activo en bajo
led = Pin(4, Pin.OUT, value=0)      # LED azul: parpadea al enviar

INICIO, ACK, NAK, SIN_DIGITO = 0xA5, 0x06, 0x15, 0xFF
REINTENTOS = 3

tx = bytearray(5)
rx = bytearray(5)


def enviar_spi(digito, confianza):
    """Envía la trama al esclavo. Devuelve True si el esclavo contestó ACK."""
    tx[0] = INICIO
    tx[1] = digito
    tx[2] = confianza
    tx[3] = (INICIO ^ digito ^ confianza) & 0xFF
    tx[4] = 0x00
    for _ in range(REINTENTOS):
        cs.value(0)                  # seleccionar esclavo
        time.sleep_ms(3)             # darle tiempo de ver el flanco de CS
        spi.write_readinto(tx, rx)   # full-duplex: envía tx y recibe rx por MISO
        time.sleep_ms(1)
        cs.value(1)                  # liberar esclavo
        if rx[4] == ACK:
            return True
        time.sleep_ms(80)            # el esclavo pudo estar ocupado con la OLED
    return False


# ---------------- lectura sin bloqueo del USB ----------------
lector = select.poll()
lector.register(sys.stdin, select.POLLIN)
buffer_pc = ""


def leer_pc():
    global buffer_pc
    while lector.poll(0):
        ch = sys.stdin.read(1)
        if ch in ("\n", "\r"):
            if buffer_pc:
                linea, buffer_pc = buffer_pc, ""
                return linea
        else:
            buffer_pc += ch
    return None


print("ESP-A lista: maestro SPI")

while True:
    linea = leer_pc()
    if linea and linea.startswith("DIG:"):
        dato = linea[4:]
        try:
            if dato == "-":
                digito, confianza, texto = SIN_DIGITO, 0, "-"
            else:
                d, c = dato.split(",")
                digito, confianza, texto = int(d), min(100, int(c)), d
                if not 0 <= digito <= 9:
                    raise ValueError
        except ValueError:
            print("SPI:DATO INVALIDO " + dato)
            continue

        led.value(1)
        ok = enviar_spi(digito, confianza)
        led.value(0)
        print(("SPI:OK " if ok else "SPI:ERROR ") + texto)   # respuesta al PC
    time.sleep_ms(5)
