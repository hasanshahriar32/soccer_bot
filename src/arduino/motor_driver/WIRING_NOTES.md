# Motor Driver Wiring Notes (Arduino Uno + L298N)

## Pin Mapping (from user's existing sketch)

| Arduino Pin | L298N Pin | Function |
|-------------|-----------|----------|
| 8           | IN1       | Left Motor Direction A |
| 9           | IN2       | Left Motor Direction B |
| 10          | ENA       | Left Motor Speed (PWM) |
| 11          | IN3       | Right Motor Direction A |
| 12          | IN4       | Right Motor Direction B |
| 5           | ENB       | Right Motor Speed (PWM) |

## Current Behavior
- On power-up, both motors immediately spin **forward** at PWM speed `80` (out of 255, ~31%).
- No loop logic — it's a one-shot `setup()` only.

## Planned Upgrade: ROS 2 Serial Control
The goal is to replace the hardcoded setup with a serial listener so ROS 2 on the Raspberry Pi can send commands to the Arduino via USB.

### Communication Protocol (Serial, 9600 baud)
The Arduino will listen for single-byte commands:
| Byte | Command |
|------|---------|
| `F`  | Forward |
| `B`  | Backward |
| `L`  | Turn Left |
| `R`  | Turn Right |
| `S`  | Stop |

### Motor Logic
| Direction | IN1 | IN2 | IN3 | IN4 |
|-----------|-----|-----|-----|-----|
| Forward   | H   | L   | H   | L   |
| Backward  | L   | H   | L   | H   |
| Left      | L   | H   | H   | L   |
| Right     | H   | L   | L   | H   |
| Stop      | L   | L   | L   | L   |
