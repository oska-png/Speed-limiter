#define ENC_CLK 2
#define ENC_DT  3
#define ENC_SW  4
#define GAS_BTN 5
#define LED_PIN 13

int speedLimit = 60;
float currentSpeed = 0;

#define ACCEL_RATE 5.0
#define DECEL_RATE 10.0

unsigned long lastSpeedUpdate = 0;
bool gasPressed = false;
unsigned long lastGasDebounce = 0;

int lastClk, lastDt;
unsigned long lastEncSWDebounce = 0;
bool encSWPressed = false;

void setup() {
  Serial.begin(9600);
  pinMode(ENC_CLK, INPUT_PULLUP);
  pinMode(ENC_DT, INPUT_PULLUP);
  pinMode(ENC_SW, INPUT_PULLUP);
  pinMode(GAS_BTN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);

  lastClk = digitalRead(ENC_CLK);
  lastDt = digitalRead(ENC_DT);

  Serial.println("System ready. Turn encoder to set speed limit (km/h).");
  Serial.print("Current limit: "); Serial.print(speedLimit); Serial.println(" km/h");
  lastSpeedUpdate = millis();
}

void loop() {
  unsigned long now = millis();

  int clk = digitalRead(ENC_CLK);
  int dt = digitalRead(ENC_DT);
  if (clk != lastClk || dt != lastDt) {
    if (clk != lastClk) {
      if (dt != clk) speedLimit++;
      else speedLimit--;
      if (speedLimit < 0) speedLimit = 0;
      if (speedLimit > 200) speedLimit = 200;

      Serial.print("Speed limit changed to: ");
      Serial.print(speedLimit); Serial.println(" km/h");

      if (currentSpeed > speedLimit) {
        currentSpeed = speedLimit;
        Serial.println("!!! Speed limited by new limit !!!");
      }
    }
    lastClk = clk;
    lastDt = dt;
  }

  if (digitalRead(ENC_SW) == LOW && !encSWPressed && (now - lastEncSWDebounce > 200)) {
    encSWPressed = true;
    speedLimit = 60;
    Serial.println("Speed limit reset to 60 km/h");
    if (currentSpeed > speedLimit) {
      currentSpeed = speedLimit;
      Serial.println("!!! Speed limited after reset !!!");
    }
    lastEncSWDebounce = now;
  }
  if (digitalRead(ENC_SW) == HIGH) encSWPressed = false;

  bool gasReading = (digitalRead(GAS_BTN) == LOW);
  if (gasReading && !gasPressed && (now - lastGasDebounce > 50)) {
    gasPressed = true;
    lastGasDebounce = now;
  }
  if (!gasReading) gasPressed = false;

  if (now - lastSpeedUpdate >= 100) {
    float deltaTime = (now - lastSpeedUpdate) / 1000.0;
    lastSpeedUpdate = now;

    if (gasPressed) {
      float increment = ACCEL_RATE * deltaTime;
      if (currentSpeed + increment <= speedLimit) {
        currentSpeed += increment;
      } else {
        currentSpeed = speedLimit;
      }
    } else {
      currentSpeed -= DECEL_RATE * deltaTime;
      if (currentSpeed < 0) currentSpeed = 0;
    }
  }

  if (currentSpeed >= speedLimit) digitalWrite(LED_PIN, HIGH);
  else digitalWrite(LED_PIN, LOW);

  static unsigned long lastPrint = 0;
  if (now - lastPrint >= 200) {
    Serial.print("Speed: ");
    Serial.print(currentSpeed, 1);
    Serial.print(" km/h  |  Limit: ");
    Serial.print(speedLimit);
    if (currentSpeed >= speedLimit) Serial.print("  [LIMIT ACTIVE]");
    Serial.println();
    lastPrint = now;
  }
static unsigned long lastSerialSend = 0;
if (now - lastSerialSend >= 200) {
    Serial.print("SPEED:");
    Serial.print(currentSpeed, 1);
    Serial.print(" LIMIT:");
    Serial.println(speedLimit);
    lastSerialSend = now;
}

  delay(10);
}