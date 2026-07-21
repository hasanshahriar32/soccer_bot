# Motor Driver Wiring Notes (Arduino Uno + L298N)

## Verified Hardware Pin Mapping

| Arduino Pin | L298N Pin | Function |
|-------------|-----------|----------|
| Pin 5       | ENA       | Left Motor Speed (PWM) |
| Pin 9       | IN1       | Left Motor Direction A |
| Pin 10      | IN2       | Left Motor Direction B |
| Pin 6       | ENB       | Right Motor Speed (PWM) |
| Pin 11      | IN3       | Right Motor Direction A |
| Pin 12      | IN4       | Right Motor Direction B |

## Motor Logic (Verified Physical Polarity)

* **Left Motor**:
  * Forward: `IN1 = HIGH`, `IN2 = LOW`
  * Backward: `IN1 = LOW`, `IN2 = HIGH`

* **Right Motor** (Physically reversed on L298N terminals):
  * Forward: `IN3 = LOW`, `IN4 = HIGH`
  * Backward: `IN3 = HIGH`, `IN4 = LOW`

## Action Table

| Movement | Left Motor (IN1, IN2) | Right Motor (IN3, IN4) | Default PWM |
|----------|------------------------|-------------------------|-------------|
| **Forward** (`F`) | HIGH, LOW | LOW, HIGH | 180 |
| **Backward** (`B`) | LOW, HIGH | HIGH, LOW | 180 |
| **Left Turn** (`L`) | LOW, HIGH (Rev) | LOW, HIGH (Fwd) | 180 |
| **Right Turn** (`R`) | HIGH, LOW (Fwd) | HIGH, LOW (Rev) | 180 |
| **Stop** (`S`) | LOW, LOW | LOW, LOW | 0 |

## Serial Control Protocol
* Baud rate: `9600`
* Single-character commands: `'F'`, `'B'`, `'L'`, `'R'`, `'S'`
