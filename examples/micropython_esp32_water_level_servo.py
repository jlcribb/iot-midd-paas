"""
Control de nivel de agua en recipiente — ESP32 + MicroPython
============================================================

Lógica:
  - Si el nivel está por debajo del umbral mínimo → activa el servo (válvula/llenado).
  - Si el nivel alcanza el umbral máximo → detiene el servo (cierra / posición de reposo).

Sensor por defecto: **HC-SR04** (ultrasonido) mirando hacia la superficie del agua.
  - Tanque vacío: la superficie está lejos → **distancia medida grande**.
  - Tanque lleno: la superficie cerca del sensor → **distancia medida pequeña**.

Por tanto:
  - **Iniciar llenado** cuando la distancia sea **mayor o igual** que DIST_INICIO_LLENADO_CM
    (agua baja; superficie lejos).
  - **Detener llenado** cuando la distancia sea **menor o igual** que DIST_DETENER_LLENADO_CM
    (agua alta; superficie cerca).

Histéresis obligatoria: DIST_INICIO_LLENADO_CM > DIST_DETENER_LLENADO_CM para evitar
encendidos/apagados continuos en el borde.

Conexiones típicas HC-SR04 (alimentar a 5 V si el módulo lo requiere; lógica Echo a 3.3 V
con divisor o módulo con salida 3.3 V):
  - VCC, GND
  - Trig -> GPIO TRIG_PIN
  - Echo -> GPIO ECHO_PIN (con protección 3.3 V en ESP32)

Servo SG90 (o similar), señal PWM:
  - Rojo -> 5 V externo (recomendado) o 5 V placa
  - Marrón -> GND común con ESP32
  - Naranja (señal) -> GPIO SERVO_PIN

Si usas **flotadores** (contacto en min/max), sustituye leer_distancia_cm() por lectura de
pines digitales y aplica la misma máquina de estados en el bucle principal.

Requisitos: MicroPython en ESP32 (módulos machine, time).
"""

import time
from machine import Pin, PWM

# ============================================
# CONFIGURACIÓN — calibrar con tu recipiente
# ============================================

# Pines HC-SR04
TRIG_PIN = 5
ECHO_PIN = 18

# Pin señal servo (PWM)
SERVO_PIN = 13

# PWM servo 50 Hz (período 20 ms)
SERVO_FREQ_HZ = 50

# Calibración distancia (cm) — mide vacío y lleno y ajusta
# Ejemplo: sensor arriba del tanque; vacío lee ~45 cm, lleno lee ~8 cm
DIST_INICIO_LLENADO_CM = 35.0   # >= esto: agua baja → encender llenado
DIST_DETENER_LLENADO_CM = 12.0  # <= esto: agua alta → apagar llenado

# Debe cumplirse: DIST_INICIO_LLENADO_CM > DIST_DETENER_LLENADO_CM

# Rango físico plausible (descarta ecos erróneos)
DIST_MIN_VALIDA_CM = 2.0
DIST_MAX_VALIDA_CM = 400.0

# Duty PWM para posiciones del servo (calibrar: SG90 en ESP32 ~26–128 en escala 10-bit típica)
# Sustituye por los valores que dejen tu válvula cerrada / abierta
SERVO_DUTY_CERRADO = 77   # ~90° o posición “cerrado”
SERVO_DUTY_ABIERTO = 110  # posición “llenado / abierto”

# Tiempo entre lecturas (s)
LOOP_INTERVAL_S = 0.25

# Timeout eco ultrasonido (microsegundos)
ECHO_TIMEOUT_US = 30000

# ============================================
# HC-SR04
# ============================================

_trig = Pin(TRIG_PIN, Pin.OUT)
_echo = Pin(ECHO_PIN, Pin.IN)


def leer_distancia_cm():
    """
    Devuelve distancia aproximada en cm o None si la lectura no es válida.
    """
    _trig.value(0)
    time.sleep_us(2)
    _trig.value(1)
    time.sleep_us(10)
    _trig.value(0)

    t0 = time.ticks_us()
    while _echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), t0) > ECHO_TIMEOUT_US:
            return None
    t1 = time.ticks_us()
    while _echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), t1) > ECHO_TIMEOUT_US:
            return None
    t2 = time.ticks_us()

    pulse_us = time.ticks_diff(t2, t1)
    # Velocidad del sonido ~343 m/s → cm/us ≈ 1/58.8 ida y vuelta
    dist_cm = (pulse_us / 2) / 29.1
    if dist_cm < DIST_MIN_VALIDA_CM or dist_cm > DIST_MAX_VALIDA_CM:
        return None
    return dist_cm


# ============================================
# Servo
# ============================================

_servo_pwm = None


def servo_init():
    global _servo_pwm
    _servo_pwm = PWM(Pin(SERVO_PIN), freq=SERVO_FREQ_HZ)
    _servo_pwm.duty(SERVO_DUTY_CERRADO)


def servo_llenado_on():
    if _servo_pwm:
        _servo_pwm.duty(SERVO_DUTY_ABIERTO)


def servo_llenado_off():
    if _servo_pwm:
        _servo_pwm.duty(SERVO_DUTY_CERRADO)


def servo_deinit():
    global _servo_pwm
    if _servo_pwm:
        try:
            _servo_pwm.deinit()
        except Exception:
            pass
        _servo_pwm = None


# ============================================
# Máquina de estados con histéresis
# ============================================

def actualizar_llenado(dist_cm, llenando):
    """
    dist_cm: float o None
    llenando: bool — si ahora estamos en modo llenado

    Devuelve (nuevo_llenando, mensaje)
    """
    if dist_cm is None:
        return llenando, "lectura inválida — manteniendo estado"

    if not llenando:
        if dist_cm >= DIST_INICIO_LLENADO_CM:
            return True, f"nivel bajo ({dist_cm:.1f} cm) → INICIO llenado"
        return False, f"OK ({dist_cm:.1f} cm) — sin llenado"
    else:
        if dist_cm <= DIST_DETENER_LLENADO_CM:
            return False, f"nivel alto ({dist_cm:.1f} cm) → DETENER llenado"
        return True, f"llenando… ({dist_cm:.1f} cm)"


def main():
    print("Control nivel agua + servo — ESP32")
    print(
        f"Umbrales: iniciar llenado si dist >= {DIST_INICIO_LLENADO_CM} cm, "
        f"detener si dist <= {DIST_DETENER_LLENADO_CM} cm"
    )

    servo_init()
    llenando = False
    servo_llenado_off()

    try:
        while True:
            d = leer_distancia_cm()
            llenando, msg = actualizar_llenado(d, llenando)

            if llenando:
                servo_llenado_on()
            else:
                servo_llenado_off()

            ds = f"{d:.1f}" if d is not None else "?"
            print(f"[{ds} cm] {msg} | servo={'LLENADO' if llenando else 'OFF'}")

            time.sleep(LOOP_INTERVAL_S)
    except KeyboardInterrupt:
        print("Interrupción — cerrando servo")
    finally:
        servo_llenado_off()
        servo_deinit()


if __name__ == "__main__":
    main()
