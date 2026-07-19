// ============================================================
// soccer_bot_motor_driver.ino
// Listens for serial commands from ROS 2 (via Raspberry Pi USB)
// and drives two DC motors via an L298N motor driver.
//
// WIRING:
//   Pin 8  -> L298N IN1  (Left Motor Dir A)
//   Pin 9  -> L298N IN2  (Left Motor Dir B)
//   Pin 10 -> L298N ENA  (Left Motor PWM Speed)
//   Pin 11 -> L298N IN3  (Right Motor Dir A)
//   Pin 12 -> L298N IN4  (Right Motor Dir B)
//   Pin 5  -> L298N ENB  (Right Motor PWM Speed)
//
// SERIAL COMMANDS (9600 baud, single byte):
//   'F' = Forward
//   'B' = Backward
//   'L' = Turn Left (spin in place)
//   'R' = Turn Right (spin in place)
//   'S' = Stop
// ============================================================

// --- Pin Definitions ---
const int LEFT_IN1  = 8;
const int LEFT_IN2  = 9;
const int LEFT_ENA  = 10;  // PWM pin

const int RIGHT_IN3 = 11;
const int RIGHT_IN4 = 12;
const int RIGHT_ENB = 5;   // PWM pin

// --- Speed Settings (0-255, tune these to match your encoder motors) ---
const int SPEED_FORWARD  = 80;   // forward/backward speed
const int SPEED_TURN     = 70;   // turning speed (usually a bit less)

// -------------------------------------------------------
// Motor Control Functions
// -------------------------------------------------------
void setLeft(int dir, int spd) {
  // dir: 1 = forward, -1 = backward, 0 = stop
  if (dir == 1) {
    digitalWrite(LEFT_IN1, HIGH);
    digitalWrite(LEFT_IN2, LOW);
  } else if (dir == -1) {
    digitalWrite(LEFT_IN1, LOW);
    digitalWrite(LEFT_IN2, HIGH);
  } else {
    digitalWrite(LEFT_IN1, LOW);
    digitalWrite(LEFT_IN2, LOW);
  }
  analogWrite(LEFT_ENA, spd);
}

void setRight(int dir, int spd) {
  if (dir == 1) {
    digitalWrite(RIGHT_IN3, HIGH);
    digitalWrite(RIGHT_IN4, LOW);
  } else if (dir == -1) {
    digitalWrite(RIGHT_IN3, LOW);
    digitalWrite(RIGHT_IN4, HIGH);
  } else {
    digitalWrite(RIGHT_IN3, LOW);
    digitalWrite(RIGHT_IN4, LOW);
  }
  analogWrite(RIGHT_ENB, spd);
}

void moveForward()  { setLeft(1, SPEED_FORWARD);  setRight(1, SPEED_FORWARD);  }
void moveBackward() { setLeft(-1, SPEED_FORWARD); setRight(-1, SPEED_FORWARD); }
void turnLeft()     { setLeft(-1, SPEED_TURN);    setRight(1, SPEED_TURN);     }
void turnRight()    { setLeft(1, SPEED_TURN);     setRight(-1, SPEED_TURN);    }
void stopMotors()   { setLeft(0, 0);              setRight(0, 0);              }

// -------------------------------------------------------
void setup() {
  pinMode(LEFT_IN1,  OUTPUT);
  pinMode(LEFT_IN2,  OUTPUT);
  pinMode(LEFT_ENA,  OUTPUT);
  pinMode(RIGHT_IN3, OUTPUT);
  pinMode(RIGHT_IN4, OUTPUT);
  pinMode(RIGHT_ENB, OUTPUT);

  stopMotors();  // Start safe - don't auto-move!

  Serial.begin(9600);
  Serial.println("Soccer Bot Motor Driver Ready.");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    switch (cmd) {
      case 'F': moveForward();  Serial.println("CMD: Forward");  break;
      case 'B': moveBackward(); Serial.println("CMD: Backward"); break;
      case 'L': turnLeft();     Serial.println("CMD: Left");     break;
      case 'R': turnRight();    Serial.println("CMD: Right");    break;
      case 'S': stopMotors();   Serial.println("CMD: Stop");     break;
      default: break;  // Ignore unknown commands
    }
  }
}
