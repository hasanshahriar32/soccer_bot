#include <Servo.h>

// =====================================================
// SOCCER BOT - 4 DOF ROBOTIC ARM CONTROLLER
// Controlled via Serial from Raspberry Pi (115200 Baud)
// =====================================================

Servo baseServo;
Servo shoulderServo;
Servo alboServo;
Servo gripperServo;

// =====================================================
// PINS
// =====================================================
const byte BASE_PIN     = 9;
const byte SHOULDER_PIN = 10;
const byte ALBO_PIN     = 11;
const byte GRIPPER_PIN  = 12;

// =====================================================
// SERVO RANGES & PULSE LIMITS
// =====================================================
const int BASE_MIN      = 0;
const int BASE_MAX      = 180;

const int SHOULDER_MIN  = 0;
const int SHOULDER_MAX  = 180;

const int ALBO_MIN      = 0;
const int ALBO_MAX      = 180;

const int GRIPPER_MIN   = 90;
const int GRIPPER_MAX   = 270;
const int GRIPPER_MIN_US = 1000;
const int GRIPPER_MAX_US = 2000;

// Default speed (ms delay per degree)
int moveDelay = 15;

// Current joint positions
int curBase     = 0;
int curShoulder = 0;
int curAlbo     = 0;
int curGripper  = 90;

// =====================================================
// GRIPPER LOW-LEVEL PULSE
// =====================================================
void setGripperPulse(int angle)
{
  angle = constrain(angle, GRIPPER_MIN, GRIPPER_MAX);
  int pulse = map(angle, GRIPPER_MIN, GRIPPER_MAX, GRIPPER_MIN_US, GRIPPER_MAX_US);
  gripperServo.writeMicroseconds(pulse);
  curGripper = angle;
}

// =====================================================
// COORDINATED MULTI-JOINT SMOOTH MOTION
// Updates all active joints concurrently step-by-step
// =====================================================
void moveTo(int tB, int tS, int tA, int tG)
{
  tB = constrain(tB, BASE_MIN, BASE_MAX);
  tS = constrain(tS, SHOULDER_MIN, SHOULDER_MAX);
  tA = constrain(tA, ALBO_MIN, ALBO_MAX);
  tG = constrain(tG, GRIPPER_MIN, GRIPPER_MAX);

  while (curBase != tB || curShoulder != tS || curAlbo != tA || curGripper != tG)
  {
    if (curBase < tB) curBase++;
    else if (curBase > tB) curBase--;

    if (curShoulder < tS) curShoulder++;
    else if (curShoulder > tS) curShoulder--;

    if (curAlbo < tA) curAlbo++;
    else if (curAlbo > tA) curAlbo--;

    if (curGripper < tG) curGripper++;
    else if (curGripper > tG) curGripper--;

    baseServo.write(curBase);
    shoulderServo.write(curShoulder);
    alboServo.write(curAlbo);
    setGripperPulse(curGripper);

    delay(moveDelay);
  }
}

void moveBase(int targetAngle)
{
  moveTo(targetAngle, curShoulder, curAlbo, curGripper);
}

void moveShoulder(int targetAngle)
{
  moveTo(curBase, targetAngle, curAlbo, curGripper);
}

void moveAlbo(int targetAngle)
{
  moveTo(curBase, curShoulder, targetAngle, curGripper);
}

void moveGripper(int targetAngle)
{
  moveTo(curBase, curShoulder, curAlbo, targetAngle);
}

// =====================================================
// PRESET ACTIONS
// =====================================================
void goHome()
{
  // Retract arm safely to folded home
  moveTo(0, 0, 0, 90);
  Serial.println(F("OK HOME"));
}

void goReady()
{
  // Ready to grab ball in front: Base centered, arm extended forward, gripper open
  moveTo(90, 70, 80, 240);
  Serial.println(F("OK READY"));
}

void doGrab()
{
  // Close gripper to grip the ball
  moveGripper(90);
  Serial.println(F("OK GRAB"));
}

void doOpen()
{
  // Open gripper
  moveGripper(240);
  Serial.println(F("OK OPEN"));
}

void printStatus()
{
  Serial.print(F("ARM_STATUS B:"));
  Serial.print(curBase);
  Serial.print(F(" S:"));
  Serial.print(curShoulder);
  Serial.print(F(" A:"));
  Serial.print(curAlbo);
  Serial.print(F(" G:"));
  Serial.println(curGripper);
}

void runSelfTest()
{
  Serial.println(F("START_TEST"));
  moveBase(180);
  delay(500);
  moveShoulder(180);
  delay(500);
  moveAlbo(180);
  delay(500);
  moveGripper(270);
  delay(1000);
  moveGripper(90);
  delay(500);
  moveAlbo(0);
  delay(500);
  moveShoulder(0);
  delay(500);
  moveBase(0);
  delay(500);
  Serial.println(F("OK TEST"));
}

// =====================================================
// COMMAND PROCESSOR
// =====================================================
void processCommand(String cmd)
{
  cmd.trim();
  if (cmd.length() == 0) return;

  cmd.toUpperCase();

  if (cmd.startsWith("B "))
  {
    int val = cmd.substring(2).toInt();
    moveBase(val);
    Serial.print(F("OK B:"));
    Serial.println(curBase);
  }
  else if (cmd.startsWith("S "))
  {
    int val = cmd.substring(2).toInt();
    moveShoulder(val);
    Serial.print(F("OK S:"));
    Serial.println(curShoulder);
  }
  else if (cmd.startsWith("A ") || cmd.startsWith("E "))
  {
    int val = cmd.substring(2).toInt();
    moveAlbo(val);
    Serial.print(F("OK A:"));
    Serial.println(curAlbo);
  }
  else if (cmd.startsWith("G "))
  {
    int val = cmd.substring(2).toInt();
    moveGripper(val);
    Serial.print(F("OK G:"));
    Serial.println(curGripper);
  }
  else if (cmd.startsWith("SET "))
  {
    // Format: SET <base> <shoulder> <albo> <gripper>
    int b = 0, s = 0, a = 0, g = 90;
    int parsed = sscanf(cmd.c_str(), "SET %d %d %d %d", &b, &s, &a, &g);
    if (parsed == 4)
    {
      moveBase(b);
      moveShoulder(s);
      moveAlbo(a);
      moveGripper(g);
      printStatus();
    }
    else
    {
      Serial.println(F("ERR INVALID_SET_SYNTAX"));
    }
  }
  else if (cmd.startsWith("SPEED "))
  {
    int val = cmd.substring(6).toInt();
    if (val >= 5 && val <= 100)
    {
      moveDelay = val;
      Serial.print(F("OK SPEED:"));
      Serial.println(moveDelay);
    }
    else
    {
      Serial.println(F("ERR SPEED_RANGE_5_100"));
    }
  }
  else if (cmd == "HOME")
  {
    goHome();
  }
  else if (cmd == "READY")
  {
    goReady();
  }
  else if (cmd == "GRAB")
  {
    doGrab();
  }
  else if (cmd == "OPEN")
  {
    doOpen();
  }
  else if (cmd == "TEST")
  {
    runSelfTest();
  }
  else if (cmd == "STATUS" || cmd == "?")
  {
    printStatus();
  }
  else
  {
    Serial.print(F("ERR UNKNOWN_CMD:"));
    Serial.println(cmd);
  }
}

// =====================================================
// SETUP
// =====================================================
void setup()
{
  Serial.begin(115200);

  // Attach servos
  baseServo.attach(BASE_PIN);
  shoulderServo.attach(SHOULDER_PIN);
  alboServo.attach(ALBO_PIN);
  gripperServo.attach(GRIPPER_PIN, GRIPPER_MIN_US, GRIPPER_MAX_US);

  // Initial home position
  baseServo.write(0);
  shoulderServo.write(0);
  alboServo.write(0);
  setGripperPulse(90);

  curBase = 0;
  curShoulder = 0;
  curAlbo = 0;
  curGripper = 90;

  Serial.println(F("ARM_READY"));
}

// =====================================================
// MAIN LOOP - NON-BLOCKING SERIAL LISTENER
// =====================================================
String inputBuffer = "";

void loop()
{
  while (Serial.available() > 0)
  {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r')
    {
      if (inputBuffer.length() > 0)
      {
        processCommand(inputBuffer);
        inputBuffer = "";
      }
    }
    else
    {
      if (inputBuffer.length() < 64)
      {
        inputBuffer += c;
      }
    }
  }
}
