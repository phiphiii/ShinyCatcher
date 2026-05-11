const int pinJoyX = 17; 
const int pinJoyY = 18; 

const int pinLed = 2;   
const int pinBuzzer = 5; 
const int pinButtonA = 15;
const int pinButtonX = 14;
const int pinButtonStart = 13;
const int pinButtonHome = 16;

bool isAlarmActive = false;
unsigned long previousMillis = 0;
const long alarmInterval = 150;
int alarmState = LOW;

void releaseJoystick() {
    pinMode(pinJoyX, INPUT);
    pinMode(pinJoyY, INPUT);
}

void tapRigid(char dir) {
    int holdTime = 50;
    if (dir == 'L') {
        pinMode(pinJoyX, OUTPUT);
        digitalWrite(pinJoyX, HIGH); 
        delay(holdTime);
        releaseJoystick();
    } 
    else if (dir == 'R') {
        pinMode(pinJoyX, OUTPUT);
        digitalWrite(pinJoyX, LOW); 
        delay(holdTime);
        releaseJoystick();
    }
    else if (dir == 'U') {
        pinMode(pinJoyY, OUTPUT);
        digitalWrite(pinJoyY, HIGH); 
        delay(holdTime);
        releaseJoystick();
    }
    else if (dir == 'D') {
        pinMode(pinJoyY, OUTPUT);
        digitalWrite(pinJoyY, LOW); 
        delay(holdTime);
        releaseJoystick();
    }
}

void setup() {
    Serial.begin(115200);
    pinMode(pinLed, OUTPUT);
    pinMode(pinBuzzer, OUTPUT);
    pinMode(pinButtonA, OUTPUT);
    pinMode(pinButtonX, OUTPUT);
    pinMode(pinButtonStart, OUTPUT);
    pinMode(pinButtonHome, OUTPUT);

    releaseJoystick();
}

void loop() {
    if (Serial.available() > 0) {
        char command = Serial.read();
        
        if (command == 'Q') isAlarmActive = true;
        else if (command == 'F') { isAlarmActive = false; digitalWrite(pinLed, 0); digitalWrite(pinBuzzer, 0); } 
        else if (command == 'A') { digitalWrite(pinButtonA, 1); delay(100); digitalWrite(pinButtonA, 0); }
        else if (command == 'X') { digitalWrite(pinButtonX, 1); delay(100); digitalWrite(pinButtonX, 0); }
        else if (command == 'S') { digitalWrite(pinButtonStart, 1); delay(100); digitalWrite(pinButtonStart, 0); }
        else if (command == 'H') { digitalWrite(pinButtonHome, 1); delay(100); digitalWrite(pinButtonHome, 0); }
        
        else if (command == 'L') { pinMode(pinJoyX, OUTPUT); digitalWrite(pinJoyX, HIGH); }
        else if (command == 'R') { pinMode(pinJoyX, OUTPUT); digitalWrite(pinJoyX, LOW); }
        else if (command == 'U') { pinMode(pinJoyY, OUTPUT); digitalWrite(pinJoyY, HIGH); }
        else if (command == 'D') { pinMode(pinJoyY, OUTPUT); digitalWrite(pinJoyY, LOW); }
        
        else if (command == 'C') { releaseJoystick(); }

        else if (command == 'l') tapRigid('L');
        else if (command == 'r') tapRigid('R');
        else if (command == 'u') tapRigid('U');
        else if (command == 'd') tapRigid('D');
    }

    if (isAlarmActive) {
        if (millis() % 300 < 150) {
            digitalWrite(pinLed, HIGH);
            digitalWrite(pinBuzzer, HIGH);
        } else {
            digitalWrite(pinLed, LOW);
            digitalWrite(pinBuzzer, LOW);
        }
    }
}