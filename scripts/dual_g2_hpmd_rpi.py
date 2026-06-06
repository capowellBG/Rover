import lgpio
import time

# Motor speeds: -MAX_SPEED to MAX_SPEED (480 for historical compatibility)
_max_speed = 480
MAX_SPEED = _max_speed

_pin_M1FLT = 5
_pin_M2FLT = 6
_pin_M1PWM = 12
_pin_M2PWM = 13
_pin_M1EN = 22
_pin_M2EN = 23
_pin_M1DIR = 24
_pin_M2DIR = 25

_PWM_FREQ = 2000  # Hz — Pi 5 RP1 chardev caps software PWM well below 20kHz

# Pi 5 RP1 is /dev/gpiochip0 (gpiochip4 is a symlink that Docker can't resolve)
_h = lgpio.gpiochip_open(0)
if _h < 0:
    raise IOError("Can't open gpiochip0 — is /dev/gpiochip0 accessible?")


class Motor(object):
    MAX_SPEED = _max_speed

    def __init__(self, pwm_pin, dir_pin, en_pin, flt_pin):
        self.pwm_pin = pwm_pin
        self.dir_pin = dir_pin
        self.en_pin = en_pin
        self.flt_pin = flt_pin

        lgpio.gpio_claim_input(_h, flt_pin, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_output(_h, dir_pin)
        lgpio.gpio_claim_output(_h, en_pin)
        lgpio.gpio_claim_output(_h, pwm_pin)
        lgpio.gpio_write(_h, en_pin, 1)
        time.sleep(0.05)  # let FLT pull-up settle before first fault read

    def setSpeed(self, speed):
        if speed < 0:
            speed = -speed
            dir_value = 1
        else:
            dir_value = 0

        if speed > MAX_SPEED:
            speed = MAX_SPEED

        duty = speed / MAX_SPEED * 100.0
        lgpio.gpio_write(_h, self.dir_pin, dir_value)
        lgpio.tx_pwm(_h, self.pwm_pin, _PWM_FREQ, duty)

    def enable(self):
        lgpio.gpio_write(_h, self.en_pin, 1)

    def disable(self):
        lgpio.gpio_write(_h, self.en_pin, 0)

    def getFault(self):
        return not lgpio.gpio_read(_h, self.flt_pin)


class Motors(object):
    MAX_SPEED = _max_speed

    def __init__(self):
        self.motor1 = Motor(_pin_M1PWM, _pin_M1DIR, _pin_M1EN, _pin_M1FLT)
        self.motor2 = Motor(_pin_M2PWM, _pin_M2DIR, _pin_M2EN, _pin_M2FLT)

    def setSpeeds(self, m1_speed, m2_speed):
        self.motor1.setSpeed(-m1_speed)
        self.motor2.setSpeed(m2_speed)

    def enable(self):
        self.motor1.enable()
        self.motor2.enable()

    def disable(self):
        self.motor1.disable()
        self.motor2.disable()

    def getFaults(self):
        return self.motor1.getFault() or self.motor2.getFault()

    def forceStop(self):
        self.setSpeeds(0, 0)


motors = Motors()
