#include <Servo.h>

// =====================================================
// ROBOT ARM - USER CONFIGURATION ARCHITECTURE
// =====================================================

Servo baseServo;
Servo shoulderServo;
Servo alboServo;
Servo gripperServo;

// =====================================================
// PINS (Per user configuration)
// =====================================================

const byte BASE_PIN     = 9;
const byte SHOULDER_PIN = 10;
const byte ALBO_PIN     = 11;
const byte GRIPPER_PIN  = 12;

// =====================================================
// BASE / SHOULDER / ALBO RANGE (Per user configuration)
// =====================================================

const int BASE_MIN      = 0;
const int BASE_MAX      = 180;

const int SHOULDER_MIN  = 0;
const int SHOULDER_MAX  = 180;

const int ALBO_MIN      = 0;
const int ALBO_MAX      = 180;

// =====================================================
// GRIPPER RANGE (Per user configuration)
// =====================================================

const int GRIPPER_MIN    = 90;
const int GRIPPER_MAX    = 270;
const int GRIPPER_MIN_US = 1000;
const int GRIPPER_MAX_US = 2000;

// =====================================================
// SPEED (Per user configuration)
// =====================================================

const int MOVE_DELAY = 40;

// Current angles tracking
int curBase     = 0;
int curShoulder = 0;
int curAlbo     = 0;
int curGripper  = 90;

// =====================================================
// GRIPPER FUNCTION (Per user configuration)
// =====================================================

void moveGripper(int toAngle)
{
  toAngle = constrain(toAngle, GRIPPER_MIN, GRIPPER_MAX);

  if (!gripperServo.attached())
  {
    gripperServo.attach(GRIPPER_PIN, GRIPPER_MIN_US, GRIPPER_MAX_US);
    delay(50);
  }

  if (curGripper != toAngle)
  {
    int step = (curGripper < toAngle) ? 1 : -1;
    for (int angle = curGripper; angle != toAngle; angle += step)
    {
      int pulse = map(angle, GRIPPER_MIN, GRIPPER_MAX, GRIPPER_MIN_US, GRIPPER_MAX_US);
      gripperServo.writeMicroseconds(pulse);
      delay(15);
    }
  }

  int pulse = map(
    toAngle,
    GRIPPER_MIN,
    GRIPPER_MAX,
    GRIPPER_MIN_US,
    GRIPPER_MAX_US
  );

  gripperServo.writeMicroseconds(pulse);
  curGripper = toAngle;
  delay(50);

  Serial.print(F("Gripper = "));
  Serial.print(toAngle);
  Serial.print(F(" deg   Pulse = "));
  Serial.println(pulse);
}

// =====================================================
// MOVE BASE (Per user configuration)
// =====================================================

void moveBase(int fromAngle, int toAngle)
{
  toAngle = constrain(toAngle, BASE_MIN, BASE_MAX);

  if (!baseServo.attached())
  {
    baseServo.attach(BASE_PIN);
    delay(50);
  }

  if (fromAngle < toAngle)
  {
    for (int angle = fromAngle; angle <= toAngle; angle++)
    {
      baseServo.write(angle);
      delay(MOVE_DELAY);
    }
  }
  else
  {
    for (int angle = fromAngle; angle >= toAngle; angle--)
    {
      baseServo.write(angle);
      delay(MOVE_DELAY);
    }
  }
  curBase = toAngle;
  delay(50);
  Serial.print(F("Base = "));
  Serial.println(curBase);
}

// =====================================================
// MOVE SHOULDER (Per user configuration)
// =====================================================

void moveShoulder(int fromAngle, int toAngle)
{
  toAngle = constrain(toAngle, SHOULDER_MIN, SHOULDER_MAX);

  if (!shoulderServo.attached())
  {
    shoulderServo.attach(SHOULDER_PIN);
    delay(50);
  }

  if (fromAngle < toAngle)
  {
    for (int angle = fromAngle; angle <= toAngle; angle++)
    {
      shoulderServo.write(angle);
      delay(MOVE_DELAY);
    }
  }
  else
  {
    for (int angle = fromAngle; angle >= toAngle; angle--)
    {
      shoulderServo.write(angle);
      delay(MOVE_DELAY);
    }
  }
  curShoulder = toAngle;
  delay(50);
  Serial.print(F("Shoulder = "));
  Serial.println(curShoulder);
}

// =====================================================
// MOVE ALBO (Per user configuration)
// =====================================================

void moveAlbo(int fromAngle, int toAngle)
{
  toAngle = constrain(toAngle, ALBO_MIN, ALBO_MAX);

  if (!alboServo.attached())
  {
    alboServo.attach(ALBO_PIN);
    delay(50);
  }

  if (fromAngle < toAngle)
  {
    for (int angle = fromAngle; angle <= toAngle; angle++)
    {
      alboServo.write(angle);
      delay(MOVE_DELAY);
    }
  }
  else
  {
    for (int angle = fromAngle; angle >= toAngle; angle--)
    {
      alboServo.write(angle);
      delay(MOVE_DELAY);
    }
  }
  curAlbo = toAngle;
  delay(50);
  Serial.print(F("ALBO = "));
  Serial.println(curAlbo);
}

// =====================================================
// FULL TEST SEQUENCE (Per user configuration)
// =====================================================

void runTestSequence()
{
  Serial.println();
  Serial.println(F("******** STEP 1: BASE ********"));
  moveBase(curBase, 180);
  delay(1000);

  Serial.println();
  Serial.println(F("******** STEP 2: SHOULDER ********"));
  moveShoulder(curShoulder, 180);
  delay(1000);

  Serial.println();
  Serial.println(F("******** STEP 3: ALBO ********"));
  moveAlbo(curAlbo, 180);
  delay(1000);

  Serial.println();
  Serial.println(F("******** STEP 4: GRIPPER OPEN ********"));
  for (int angle = 90; angle <= 270; angle++)
  {
    moveGripper(angle);
    delay(MOVE_DELAY);
  }
  delay(1500);

  Serial.println();
  Serial.println(F("******** STEP 5: GRIPPER CLOSE ********"));
  for (int angle = 270; angle >= 90; angle--)
  {
    moveGripper(angle);
    delay(MOVE_DELAY);
  }
  delay(1000);

  Serial.println();
  Serial.println(F("******** STEP 6: ALBO RETURN ********"));
  moveAlbo(curAlbo, 0);
  delay(1000);

  Serial.println();
  Serial.println(F("******** STEP 7: SHOULDER RETURN ********"));
  moveShoulder(curShoulder, 0);
  delay(1000);

  Serial.println();
  Serial.println(F("******** STEP 8: BASE RETURN ********"));
  moveBase(curBase, 0);
  delay(2000);

  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F("       SEQUENCE COMPLETE"));
  Serial.println(F("       ALL SERVOS HOME"));
  Serial.println(F("========================================"));
}

// =====================================================
// SERIAL COMMAND PROCESSOR
// =====================================================

void printStatus()
{
  char buf[48];
  snprintf(buf, sizeof(buf), "ARM_STATUS B:%d S:%d A:%d G:%d", curBase, curShoulder, curAlbo, curGripper);
  Serial.println(buf);
}

void processCommand(char* cmd)
{
  while (*cmd == ' ' || *cmd == '\t') cmd++;
  if (*cmd == '\0') return;

  for (char* p = cmd; *p; p++) *p = toupper((unsigned char)*p);

  if (strncmp(cmd, "B ", 2) == 0)
  {
    int val = atoi(cmd + 2);
    moveBase(curBase, val);
    Serial.print(F("OK B:"));
    Serial.println(curBase);
  }
  else if (strncmp(cmd, "S ", 2) == 0)
  {
    int val = atoi(cmd + 2);
    moveShoulder(curShoulder, val);
    Serial.print(F("OK S:"));
    Serial.println(curShoulder);
  }
  else if (strncmp(cmd, "A ", 2) == 0 || strncmp(cmd, "E ", 2) == 0)
  {
    int val = atoi(cmd + 2);
    moveAlbo(curAlbo, val);
    Serial.print(F("OK A:"));
    Serial.println(curAlbo);
  }
  else if (strncmp(cmd, "G ", 2) == 0)
  {
    int val = atoi(cmd + 2);
    moveGripper(val);
    Serial.print(F("OK G:"));
    Serial.println(curGripper);
  }
  else if (strcmp(cmd, "TEST") == 0)
  {
    runTestSequence();
    Serial.println(F("OK TEST"));
  }
  else if (strcmp(cmd, "HOME") == 0)
  {
    moveGripper(90);
    moveAlbo(curAlbo, 0);
    moveShoulder(curShoulder, 0);
    moveBase(curBase, 0);
    Serial.println(F("OK HOME"));
  }
  else if (strcmp(cmd, "READY") == 0)
  {
    moveBase(curBase, 90);
    moveShoulder(curShoulder, 70);
    moveAlbo(curAlbo, 80);
    moveGripper(240);
    Serial.println(F("OK READY"));
  }
  else if (strcmp(cmd, "STATUS") == 0 || strcmp(cmd, "?") == 0)
  {
    printStatus();
  }
  else
  {
    Serial.print(F("ERR:"));
    Serial.println(cmd);
  }
}

// =====================================================
// SETUP (Safe on-demand attachment)
// =====================================================

void setup()
{
  Serial.begin(115200);
  delay(100);

  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F("        ROBOT ARM READY"));
  Serial.println(F("========================================"));
  Serial.println(F("BASE       : PIN 9   : 0 - 180"));
  Serial.println(F("SHOULDER   : PIN 10  : 0 - 180"));
  Serial.println(F("ALBO       : PIN 11  : 0 - 180"));
  Serial.println(F("GRIPPER    : PIN 12  : 90 - 270"));
  Serial.println(F("========================================"));
  Serial.println(F("ARM_READY"));
  printStatus();
}

char rxBuf[48];
byte rxIdx = 0;

void loop()
{
  while (Serial.available() > 0)
  {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r')
    {
      if (rxIdx > 0)
      {
        rxBuf[rxIdx] = '\0';
        processCommand(rxBuf);
        rxIdx = 0;
      }
    }
    else
    {
      if (rxIdx < sizeof(rxBuf) - 1)
      {
        rxBuf[rxIdx++] = c;
      }
    }
  }
}
