// ============================================================
// HARDWARE PERMANENT LEFT MOTOR SPIN TEST
// Arduino Uno outputs continuous 100% full power to Left Motor
// ============================================================

const int ENA = 5;
const int IN1 = 9;
const int IN2 = 10;

const int ENB = 6;
const int IN3 = 11;
const int IN4 = 12;

void setup() {
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Right Motor 100% OFF
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  digitalWrite(ENB, LOW);
  analogWrite(ENB, 0);

  // Left Motor 100% CONTINUOUS FORWARD
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(ENA, HIGH);
  analogWrite(ENA, 255);
}

void loop() {
  // Continuously reinforce 100% full power on Left Motor
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(ENA, HIGH);
  analogWrite(ENA, 255);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  digitalWrite(ENB, LOW);
  analogWrite(ENB, 0);

  delay(50);
}
