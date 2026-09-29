#include <Servo.h>

// =====================================================
// SOCCER BOT - SERVO MOTOR CONTROLLER (PINS 9, 10, 11, 12)
// Safe on-demand attachment to prevent USB brownout reset
// =====================================================

Servo baseServo;
Servo shoulderServo;
Servo alboServo;
Servo gripperServo;

const byte BASE_PIN     = 9;
const byte SHOULDER_PIN = 10;
const byte ALBO_PIN     = 11;
const byte GRIPPER_PIN  = 12;

const int BASE_MIN      = 0;
const int BASE_MAX      = 180;

const int SHOULDER_MIN  = 0;
const int SHOULDER_MAX  = 180;

const int ALBO_MIN      = 0;
const int ALBO_MAX      = 180;

const int GRIPPER_MIN    = 115;
const int GRIPPER_MAX    = 270;
const int GRIPPER_MIN_US = 1150;
const int GRIPPER_MAX_US = 2000;

int moveDelay = 20;

int curBase     = 0;
int curShoulder = 0;
int curAlbo     = 0;
int curGripper  = 180;

void ensureAttached(byte pin)
{
  if (pin == BASE_PIN && !baseServo.attached())
  {
    baseServo.attach(BASE_PIN);
  }
  else if (pin == SHOULDER_PIN && !shoulderServo.attached())
  {
    shoulderServo.attach(SHOULDER_PIN);
  }
  else if (pin == ALBO_PIN && !alboServo.attached())
  {
    alboServo.attach(ALBO_PIN);
  }
  else if (pin == GRIPPER_PIN && !gripperServo.attached())
  {
    gripperServo.attach(GRIPPER_PIN, GRIPPER_MIN_US, GRIPPER_MAX_US);
  }
}

void moveBase(int toAngle)
{
  toAngle = constrain(toAngle, BASE_MIN, BASE_MAX);
  ensureAttached(BASE_PIN);
  
  if (curBase < toAngle)
  {
    for (int a = curBase; a <= toAngle; a++)
    {
      baseServo.write(a);
      delay(moveDelay);
    }
  }
  else
  {
    for (int a = curBase; a >= toAngle; a--)
    {
      baseServo.write(a);
      delay(moveDelay);
    }
  }
  curBase = toAngle;
}

void moveShoulder(int toAngle)
{
  toAngle = constrain(toAngle, SHOULDER_MIN, SHOULDER_MAX);
  ensureAttached(SHOULDER_PIN);
  
  if (curShoulder < toAngle)
  {
    for (int a = curShoulder; a <= toAngle; a++)
    {
      shoulderServo.write(a);
      delay(moveDelay);
    }
  }
  else
  {
    for (int a = curShoulder; a >= toAngle; a--)
    {
      shoulderServo.write(a);
      delay(moveDelay);
    }
  }
  curShoulder = toAngle;
}

void moveAlbo(int toAngle)
{
  toAngle = constrain(toAngle, ALBO_MIN, ALBO_MAX);
  ensureAttached(ALBO_PIN);
  
  if (curAlbo < toAngle)
  {
    for (int a = curAlbo; a <= toAngle; a++)
    {
      alboServo.write(a);
      delay(moveDelay);
    }
  }
  else
  {
    for (int a = curAlbo; a >= toAngle; a--)
    {
      alboServo.write(a);
      delay(moveDelay);
    }
  }
  curAlbo = toAngle;
}

void setGripperPulse(int angle)
{
  angle = constrain(angle, GRIPPER_MIN, GRIPPER_MAX);
  ensureAttached(GRIPPER_PIN);
  int pulse = map(angle, GRIPPER_MIN, GRIPPER_MAX, GRIPPER_MIN_US, GRIPPER_MAX_US);
  gripperServo.writeMicroseconds(pulse);
  curGripper = angle;
}

void moveGripper(int toAngle)
{
  toAngle = constrain(toAngle, GRIPPER_MIN, GRIPPER_MAX);
  ensureAttached(GRIPPER_PIN);
  
  if (curGripper < toAngle)
  {
    for (int a = curGripper; a <= toAngle; a++)
    {
      setGripperPulse(a);
      delay(moveDelay);
    }
  }
  else
  {
    for (int a = curGripper; a >= toAngle; a--)
    {
      setGripperPulse(a);
      delay(moveDelay);
    }
  }
  curGripper = toAngle;
}

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

  char outBuf[32];

  if (strncmp(cmd, "B ", 2) == 0)
  {
    int val = atoi(cmd + 2);
    moveBase(val);
    snprintf(outBuf, sizeof(outBuf), "OK B:%d", curBase);
    Serial.println(outBuf);
  }
  else if (strncmp(cmd, "S ", 2) == 0)
  {
    int val = atoi(cmd + 2);
    moveShoulder(val);
    snprintf(outBuf, sizeof(outBuf), "OK S:%d", curShoulder);
    Serial.println(outBuf);
  }
  else if (strncmp(cmd, "A ", 2) == 0 || strncmp(cmd, "E ", 2) == 0)
  {
    int val = atoi(cmd + 2);
    moveAlbo(val);
    snprintf(outBuf, sizeof(outBuf), "OK A:%d", curAlbo);
    Serial.println(outBuf);
  }
  else if (strncmp(cmd, "G ", 2) == 0)
  {
    int val = atoi(cmd + 2);
    moveGripper(val);
    snprintf(outBuf, sizeof(outBuf), "OK G:%d", curGripper);
    Serial.println(outBuf);
  }
  else if (strcmp(cmd, "HOME") == 0)
  {
    moveBase(0);
    moveShoulder(0);
    moveAlbo(0);
    moveGripper(180);
    Serial.println(F("OK HOME"));
  }
  else if (strcmp(cmd, "READY") == 0)
  {
    moveBase(90);
    moveShoulder(70);
    moveAlbo(80);
    moveGripper(240);
    Serial.println(F("OK READY"));
  }
  else if (strcmp(cmd, "STATUS") == 0 || strcmp(cmd, "?") == 0)
  {
    printStatus();
  }
  else
  {
    Serial.print(F("ERR UNKNOWN_CMD:"));
    Serial.println(cmd);
  }
}

void setup()
{
  Serial.begin(115200);

  // Attach ONLY Base servo at startup to prevent power surge / brownout
  baseServo.attach(BASE_PIN);
  baseServo.write(0);
  curBase = 0;

  Serial.println(F("ARM_READY"));
}

char rxBuf[64];
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
