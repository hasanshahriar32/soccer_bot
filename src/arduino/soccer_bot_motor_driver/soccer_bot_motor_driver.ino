// ============================================================
// soccer_bot_motor_driver.ino
// ROS 2 Serial Motor Driver for Arduino UNO + L298N
//
// VERIFIED HARDWARE PINOUT:
//   Left Motor:  ENA = 5 (PWM), IN1 = 9, IN2 = 10
//   Right Motor: ENB = 6 (PWM), IN3 = 11, IN4 = 12
//
// SERIAL COMMANDS (9600 Baud):
//   'F' -> Forward
//   'B' -> Backward
//   'L' -> Turn Left
//   'R' -> Turn Right
//   'S' -> Stop
// ============================================================

// --- Pin Definitions ---
const int ENA = 5;   // Left Motor PWM Speed
const int IN1 = 9;   // Left Motor Dir A
const int IN2 = 10;  // Left Motor Dir B

const int ENB = 6;   // Right Motor PWM Speed
const int IN3 = 11;  // Right Motor Dir A
const int IN4 = 12;  // Right Motor Dir B

// --- Default Speed (0 - 255) ---
int motorSpeed = 175;

void setup()
{
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopMotor(); // Start safe in stopped state

  Serial.begin(9600);
  Serial.println("Soccer Bot Motor Driver Ready.");
}

void loop()
{
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

//========================
// Forward
//========================
void forward()
{
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  // Right motor physically reversed
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

//========================
// Backward
//========================
void backward()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  // Right motor physically reversed
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

//========================
// Turn Left
//========================
void left()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

//========================
// Turn Right
//========================
void right()
{
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

//========================
// Stop
//========================
void stopMotor()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}
