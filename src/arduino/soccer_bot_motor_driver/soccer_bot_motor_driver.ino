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
//   Robust 2.5-second watchdog auto-stop (prevents random jitter stops)
// ============================================================

// --- Pin Definitions ---
const int ENA = 5;   // Left Motor PWM Speed
const int IN1 = 9;   // Left Motor Dir A
const int IN2 = 10;  // Left Motor Dir B

const int ENB = 6;   // Right Motor PWM Speed
const int IN3 = 11;  // Right Motor Dir A
const int IN4 = 12;  // Right Motor Dir B

// --- Default Speeds for Legacy Single-Char Commands ---
const int LEGACY_FORWARD_SPEED = 240;
const int LEGACY_TURN_SPEED = 200;

// --- Watchdog Timer (2500ms prevents jitter stops) ---
unsigned long lastCommandTime = 0;
const unsigned long WATCHDOG_TIMEOUT_MS = 2500;

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
  // --- Watchdog: Auto-stop if no command for 2.5s ---
  if (millis() - lastCommandTime > WATCHDOG_TIMEOUT_MS) {
    stopMotors();
  }

  // --- Read Serial Input ---
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (inputBuffer.length() > 0) {
        parseCommand(inputBuffer);
        inputBuffer = "";
      }
    } else {
      inputBuffer += c;
    }
  }
}

void parseCommand(String cmd)
{
  cmd.trim();
  if (cmd.length() == 0) return;

  lastCommandTime = millis();

  // Single-character legacy commands
  if (cmd.length() == 1) {
    char c = cmd.charAt(0);
    switch (c) {
      case 'F':
      case 'f':
        setMotors(LEGACY_FORWARD_SPEED, LEGACY_FORWARD_SPEED);
        Serial.println("CMD: Forward");
        break;
      case 'B':
      case 'b':
        setMotors(-LEGACY_FORWARD_SPEED, -LEGACY_FORWARD_SPEED);
        Serial.println("CMD: Backward");
        break;
      case 'L':
      case 'l':
        setMotors(-LEGACY_TURN_SPEED, LEGACY_TURN_SPEED);
        Serial.println("CMD: Spin Left");
        break;
      case 'R':
      case 'r':
        setMotors(LEGACY_TURN_SPEED, -LEGACY_TURN_SPEED);
        Serial.println("CMD: Spin Right");
        break;
      case 'S':
      case 's':
        stopMotors();
        Serial.println("CMD: Stop");
        break;
      default:
        Serial.print("ERR: Unknown char: ");
        Serial.println(c);
        break;
    }
    return;
  }

  // PWM Format: "L:255 R:255"
  if (cmd.startsWith("L:") || cmd.startsWith("l:")) {
    int rIndex = cmd.indexOf('R');
    if (rIndex == -1) rIndex = cmd.indexOf('r');

    if (rIndex != -1) {
      String leftStr = cmd.substring(2, rIndex);
      leftStr.trim();
      String rightStr = cmd.substring(rIndex + 2);
      rightStr.trim();

      int leftPWM = leftStr.toInt();
      int rightPWM = rightStr.toInt();

      leftPWM = constrain(leftPWM, -255, 255);
      rightPWM = constrain(rightPWM, -255, 255);

      setMotors(leftPWM, rightPWM);
      return;
    }
  }
}

void setMotors(int leftSpeed, int rightSpeed)
{
  // Left Motor Direction & Speed
  if (leftSpeed > 0) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    analogWrite(ENA, leftSpeed);
  } else if (leftSpeed < 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    analogWrite(ENA, abs(leftSpeed));
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    analogWrite(ENA, 0);
  }

  // Right Motor Direction & Speed
  if (rightSpeed > 0) {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    analogWrite(ENB, rightSpeed);
  } else if (rightSpeed < 0) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    analogWrite(ENB, abs(rightSpeed));
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
    analogWrite(ENB, 0);
  }
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
