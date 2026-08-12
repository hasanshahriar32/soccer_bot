// ============================================================
// soccer_bot_motor_driver.ino
// Complete Dual Motor Driver for Arduino UNO + L298N
// ============================================================

const int ENA = 5;   // Left PWM / Enable
const int IN1 = 9;   // Left Dir A
const int IN2 = 10;  // Left Dir B

const int ENB = 6;   // Right PWM / Enable
const int IN3 = 11;  // Right Dir A
const int IN4 = 12;  // Right Dir B

const int FULL_SPEED = 255;
const int TURN_SPEED = 230;

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
  Serial.println("Soccer Bot Dual Motor Driver Active (115200 Baud)");
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
        setMotors(FULL_SPEED, FULL_SPEED);
        break;
      case 'B':
      case 'b':
        setMotors(-FULL_SPEED, -FULL_SPEED);
        break;
      case 'L':
      case 'l':
        setMotors(-TURN_SPEED, TURN_SPEED);
        break;
      case 'R':
      case 'r':
        setMotors(TURN_SPEED, -TURN_SPEED);
        break;
      case 'S':
      case 's':
        stopMotors();
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
  // Left Motor (OUT1 / OUT2)
  if (leftSpeed > 0) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    digitalWrite(ENA, HIGH);
    analogWrite(ENA, leftSpeed);
  } else if (leftSpeed < 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    digitalWrite(ENA, HIGH);
    analogWrite(ENA, abs(leftSpeed));
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    digitalWrite(ENA, LOW);
    analogWrite(ENA, 0);
  }

  // Right Motor (OUT3 / OUT4)
  if (rightSpeed > 0) {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    digitalWrite(ENB, HIGH);
    analogWrite(ENB, rightSpeed);
  } else if (rightSpeed < 0) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    digitalWrite(ENB, HIGH);
    analogWrite(ENB, abs(rightSpeed));
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
    digitalWrite(ENB, LOW);
    analogWrite(ENB, 0);
  }
}

void stopMotors()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  digitalWrite(ENA, LOW);
  digitalWrite(ENB, LOW);
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}
