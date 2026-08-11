// ============================================================
// soccer_bot_motor_driver.ino
// Arduino UNO + L298N Motor Driver Firmware for Soccer Bot
//
// HARDWARE PINOUT:
//   Left Motor:  ENA = Pin 5 (PWM), IN1 = Pin 9, IN2 = Pin 10
//   Right Motor: ENB = Pin 6 (PWM), IN3 = Pin 11, IN4 = Pin 12
//
// SERIAL PROTOCOL (9600 Baud on /dev/ttyACM0):
//   'F' -> Forward
//   'B' -> Backward
//   'L' -> Turn Left
//   'R' -> Turn Right
//   'S' -> Stop Motors
// ============================================================

// --- Pin Definitions ---
const int ENA = 5;   // Left Motor PWM Speed
const int IN1 = 9;   // Left Motor Dir A
const int IN2 = 10;  // Left Motor Dir B

const int ENB = 6;   // Right Motor PWM Speed
const int IN3 = 11;  // Right Motor Dir A
const int IN4 = 12;  // Right Motor Dir B

// Default Speed (0 - 255)
int motorSpeed = 180;

void setup() {
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopMotor(); // Safe initial state

  Serial.begin(9600);
  Serial.println("Soccer Bot Motor Driver Ready.");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    switch (cmd) {
      case 'F':
        forward();
        Serial.println("CMD: Forward");
        break;
      case 'B':
        backward();
        Serial.println("CMD: Backward");
        break;
      case 'L':
        left();
        Serial.println("CMD: Left");
        break;
      case 'R':
        right();
        Serial.println("CMD: Right");
        break;
      case 'S':
        stopMotor();
        Serial.println("CMD: Stop");
        break;
      default:
        break;
    }
  }
}

// Forward Motion
void forward() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

// Backward Motion
void backward() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

// Turn Left
void left() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

// Turn Right
void right() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

// Stop Motors
void stopMotor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}
