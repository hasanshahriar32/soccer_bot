//========================================
// Working standalone test code provided by user
// Arduino UNO + L298N + 2 DC Motors
//========================================

// Left Motor
const int ENA = 5;
const int IN1 = 9;
const int IN2 = 10;

// Right Motor
const int ENB = 6;
const int IN3 = 11;
const int IN4 = 12;

// Speed (0 - 255)
int motorSpeed = 180;

void setup()
{
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
}

void loop()
{
  // Forward
  forward();
  delay(3000);

  stopMotor();
  delay(1000);

  // Backward
  backward();
  delay(3000);

  stopMotor();
  delay(1000);

  // Left Turn
  left();
  delay(2000);

  stopMotor();
  delay(1000);

  // Right Turn
  right();
  delay(2000);

  stopMotor();
  delay(2000);

  // Slow Forward
  motorSpeed = 100;
  forward();
  delay(3000);

  stopMotor();
  delay(1000);

  // Fast Forward
  motorSpeed = 255;
  forward();
  delay(3000);

  stopMotor();
  while (1);   // End program
}

//========================
// Forward
//========================
void forward()
{
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  // Right motor reversed
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

//========================
// Backward
//========================
void backward()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  // Right motor reversed
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

//========================
// Turn Left
//========================
void left()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

//========================
// Turn Right
//========================
void right()
{
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, motorSpeed);
  analogWrite(ENB, motorSpeed);
}

//========================
// Stop
//========================
void stopMotor()
{
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}
