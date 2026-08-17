// ============================================================
// soccer_bot_motor_driver.ino
// Complete Dual Motor Driver for Arduino UNO + L298N
// Tuned directions: corrected Forward/Backward/Left/Right directions
// ============================================================

const int ENA = 5;   // Left PWM / Enable
const int IN1 = 9;   // Left Dir A
const int IN2 = 10;  // Left Dir B

const int ENB = 6;   // Right PWM / Enable
const int IN3 = 11;  // Right Dir A
const int IN4 = 12;  // Right Dir B

// Tuned default speeds for smooth, controlled control
const int DEFAULT_FORWARD_SPEED = 235;
const int DEFAULT_TURN_SPEED = 210;

unsigned long lastCommandTime = 0;
const unsigned long WATCHDOG_TIMEOUT_MS = 3000;

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
  Serial.println("Soccer Bot Motor Driver Active (Corrected Directions)");
  lastCommandTime = millis();
}

void loop()
{
  if (millis() - lastCommandTime > WATCHDOG_TIMEOUT_MS) {
    stopMotors();
  }

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

  // Single Character Protocol
  if (cmd.length() == 1) {
    char c = cmd.charAt(0);
    switch (c) {
      case 'F':
      case 'f':
        setMotors(DEFAULT_FORWARD_SPEED, DEFAULT_FORWARD_SPEED);
        break;
      case 'B':
      case 'b':
        setMotors(-DEFAULT_FORWARD_SPEED, -DEFAULT_FORWARD_SPEED);
        break;
      case 'L':
      case 'l':
        setMotors(-DEFAULT_TURN_SPEED, DEFAULT_TURN_SPEED);
        break;
      case 'R':
      case 'r':
        setMotors(DEFAULT_TURN_SPEED, -DEFAULT_TURN_SPEED);
        break;
      case 'S':
      case 's':
        stopMotors();
        break;
    }
    return;
  }

  // PWM Format: "L:215 R:215"
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
  // Left Motor (OUT1 / OUT2) - INVERTED to correct physical direction
  if (leftSpeed > 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    analogWrite(ENA, leftSpeed);
  } else if (leftSpeed < 0) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    analogWrite(ENA, abs(leftSpeed));
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    analogWrite(ENA, 0);
  }

  // Right Motor (OUT3 / OUT4) - INVERTED to correct physical direction
  if (rightSpeed > 0) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    analogWrite(ENB, rightSpeed);
  } else if (rightSpeed < 0) {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
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
