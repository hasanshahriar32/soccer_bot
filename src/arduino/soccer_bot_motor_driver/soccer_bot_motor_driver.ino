// ============================================================
// soccer_bot_motor_driver.ino
// ROS 2 Serial Motor Driver for Arduino UNO + L298N
//
// VERIFIED HARDWARE PINOUT:
//   Left Motor:  ENA = 5 (PWM), IN1 = 9, IN2 = 10
//   Right Motor: ENB = 6 (PWM), IN3 = 11, IN4 = 12
//
// SERIAL PROTOCOL (115200 Baud):
//   PWM Mode:    "L:{-255..255} R:{-255..255}\n"
//   Legacy Mode: 'F','B','L','R','S' single-char commands
//
// SAFETY:
//   Watchdog auto-stop if no command received for 500ms
// ============================================================

// --- Pin Definitions ---
const int ENA = 5;   // Left Motor PWM Speed
const int IN1 = 9;   // Left Motor Dir A
const int IN2 = 10;  // Left Motor Dir B

const int ENB = 6;   // Right Motor PWM Speed
const int IN3 = 11;  // Right Motor Dir A
const int IN4 = 12;  // Right Motor Dir B

// --- Default Speeds for Legacy Single-Char Commands ---
const int LEGACY_FORWARD_SPEED = 175;
const int LEGACY_TURN_SPEED = 165;

// --- Watchdog Timer ---
unsigned long lastCommandTime = 0;
const unsigned long WATCHDOG_TIMEOUT_MS = 500;

// --- Serial Buffer ---
String inputBuffer = "";

void setup()
{
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopMotors();

  Serial.begin(115200);
  Serial.println("Soccer Bot Motor Driver Ready. (PWM + Legacy, 115200 baud)");
  lastCommandTime = millis();
}

void loop()
{
  // --- Watchdog: Auto-stop if no command for 500ms ---
  if (millis() - lastCommandTime > WATCHDOG_TIMEOUT_MS) {
    stopMotors();
  }

  // --- Read Serial Input ---
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      inputBuffer.trim();
      if (inputBuffer.length() > 0) {
        processCommand(inputBuffer);
        lastCommandTime = millis();
      }
      inputBuffer = "";
    } else {
      inputBuffer += c;

      // Safety: prevent buffer overflow
      if (inputBuffer.length() > 32) {
        inputBuffer = "";
      }
    }
  }
}

// ============================================================
// Process Incoming Command
// ============================================================
void processCommand(String cmd)
{
  // --- PWM Mode: "L:{pwm} R:{pwm}" ---
  if (cmd.startsWith("L:")) {
    int spaceIdx = cmd.indexOf(' ');
    if (spaceIdx > 0 && cmd.indexOf("R:") > 0) {
      int leftPWM = cmd.substring(2, spaceIdx).toInt();
      int rightPWM = cmd.substring(cmd.indexOf("R:") + 2).toInt();

      setMotorPWM(leftPWM, rightPWM);
      return;
    }
  }

  // --- Legacy Single-Char Mode ---
  if (cmd.length() == 1) {
    char c = cmd.charAt(0);
    switch (c) {
      case 'F': forward();    break;
      case 'B': backward();   break;
      case 'L': turnLeft();   break;
      case 'R': turnRight();  break;
      case 'S': stopMotors(); break;
    }
  }
}

// ============================================================
// PWM Motor Control (-255 to +255 per wheel)
// ============================================================
void setMotorPWM(int leftPWM, int rightPWM)
{
  // Clamp values
  leftPWM  = constrain(leftPWM, -255, 255);
  rightPWM = constrain(rightPWM, -255, 255);

  // Left Motor
  if (leftPWM >= 0) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  }
  analogWrite(ENA, abs(leftPWM));

  // Right Motor (physically reversed wiring)
  if (rightPWM >= 0) {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  } else {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  }
  analogWrite(ENB, abs(rightPWM));
}

// ============================================================
// Legacy Movement Functions
// ============================================================
void forward()
{
  setMotorPWM(LEGACY_FORWARD_SPEED, LEGACY_FORWARD_SPEED);
}

void backward()
{
  setMotorPWM(-LEGACY_FORWARD_SPEED, -LEGACY_FORWARD_SPEED);
}

void turnLeft()
{
  setMotorPWM(-LEGACY_TURN_SPEED, LEGACY_TURN_SPEED);
}

void turnRight()
{
  setMotorPWM(LEGACY_TURN_SPEED, -LEGACY_TURN_SPEED);
}

void stopMotors()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}
