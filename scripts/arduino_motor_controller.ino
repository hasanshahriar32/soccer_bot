// Arduino Motor Controller for L298N
// Listens to Serial commands in the format "L:255 R:-255\n"
// Speed is -255 to 255

// Motor A (Left)
int ENA = 9;  // PWM
int IN1 = 8;  // Dir 1
int IN2 = 7;  // Dir 2

// Motor B (Right)
int ENB = 10; // PWM
int IN3 = 11; // Dir 1
int IN4 = 12; // Dir 2

void setup() {
  Serial.begin(115200);
  
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  
  // Stop motors initially
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  Serial.println("Arduino Motor Controller Ready!");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove whitespace
    
    // Parse "L:255 R:-255"
    int l_idx = command.indexOf("L:");
    int r_idx = command.indexOf("R:");
    
    if (l_idx != -1 && r_idx != -1) {
      // Extract numbers
      int left_speed = command.substring(l_idx + 2, command.indexOf(' ', l_idx)).toInt();
      int right_speed = command.substring(r_idx + 2).toInt();
      
      setMotors(left_speed, right_speed);
    }
  }
}

void setMotors(int left, int right) {
  // Constrain speeds
  left = constrain(left, -255, 255);
  right = constrain(right, -255, 255);
  
  // Left Motor Direction
  if (left > 0) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  } else if (left < 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
  }
  
  // Right Motor Direction
  if (right > 0) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  } else if (right < 0) {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
  }
  
  // Set PWM
  analogWrite(ENA, abs(left));
  analogWrite(ENB, abs(right));
}
