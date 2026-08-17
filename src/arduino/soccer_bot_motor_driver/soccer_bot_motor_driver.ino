// ============================================================
// soccer_bot_motor_driver.ino
// Arduino UNO + L298N Dual H-Bridge Motor Driver
// Configured exactly per Desktop/Motor_wheel_configuration.txt
// ============================================================

// --- Pin Definitions ---
const int ENA = 5;   // Left Motor PWM (L298N ENA)
const int ENB = 6;   // Right Motor PWM (L298N ENB)

const int IN1 = 9;   // Left Motor Dir A (L298N IN1)
const int IN2 = 10;  // Left Motor Dir B (L298N IN2)
const int IN3 = 11;  // Right Motor Dir A (L298N IN3)
const int IN4 = 12;  // Right Motor Dir B (L298N IN4)

// Encoder Pins
const int LEFT_ENC_A  = 2;
const int LEFT_ENC_B  = 3;
const int RIGHT_ENC_A = 4;
const int RIGHT_ENC_B = 7;

// Default Full Speed (0 - 255)
int motorSpeed = 255; // Full 100% power for maximum torque

void setup() {
  // Motor Output Pins
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Encoder Input Pins with Pullup
  pinMode(LEFT_ENC_A, INPUT_PULLUP);
  pinMode(LEFT_ENC_B, INPUT_PULLUP);
  pinMode(RIGHT_ENC_A, INPUT_PULLUP);
  pinMode(RIGHT_ENC_B, INPUT_PULLUP);

  stopMotor(); // Safe initial state

  Serial.begin(9600);
  Serial.println("Soccer Bot Motor Driver Configured & Ready.");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    switch (cmd) {
      case 'F':
      case 'f':
        forward();
        Serial.println("CMD: Forward");
        break;
      case 'B':
      case 'b':
        backward();
        Serial.println("CMD: Backward");
        break;
      case 'L':
      case 'l':
        left();
        Serial.println("CMD: Left");
        break;
      case 'R':
      case 'r':
        right();
        Serial.println("CMD: Right");
        break;
      case 'S':
      case 's':
        stopMotor();
        Serial.println("CMD: Stop");
        break;
      case '1':
        motorSpeed = 100; // Super Slow
        break;
      case '2':
        motorSpeed = 135; // Slow
        break;
      case '3':
        motorSpeed = 175; // Medium
        break;
      case '4':
        motorSpeed = 215; // Fast
        break;
      case '5':
        motorSpeed = 255; // Full Speed
        break;
      default:
        break;
    }
  }
}

// 1. FORWARD
void forward() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

// 2. BACKWARD
void backward() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

// 3. LEFT TURN
void left() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

// 4. RIGHT TURN
void right() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

// 5. STOP
void stopMotor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}
