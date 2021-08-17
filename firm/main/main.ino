#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"
#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    #include "Wire.h"
#endif

#define OUTPUT_FORMAT 1

// MPU6050 mpu(0x68);
MPU6050 mpu;
#define INTERRUPT_PIN 2

bool dmpReady = false;  // set true if DMP init was successful
uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
uint8_t devStatus;      // return status after each device operation (0 = success, !0 = error)
uint16_t packetSize;    // expected DMP packet size (default is 42 bytes)
// uint16_t fifoCount;     // count of all bytes currently in FIFO
uint8_t fifoBuffer[64]; // FIFO storage buffer

// orientation/motion vars
Quaternion q;           // [w, x, y, z]         quaternion container
VectorFloat gravity;    // [x, y, z]            gravity vector
float ypr[3];           // [yaw, pitch, roll]   yaw/pitch/roll container and gravity vector

volatile bool mpuInterrupt = false;     // indicates whether MPU interrupt pin has gone high
void dmpDataReady() {
    mpuInterrupt = true;
}

const int pin_PALM = 3;
const int pin_THUMB = 4;
const int pin_INDEX = 5;
const int pin_MIDDLE = 6;
const int pin_RING = 7;
const int pin_PINKY = 8;

const int CONNECTION_ROUTE_UNKNOWN = 0;
const int CONNECTION_ROUTE_THUMB = 1;
const int CONNECTION_ROUTE_PALM = 2;
const int FINGER_CONNECTION_DELAY = 20;

typedef struct Finger {
    int pin = 0;
    int state = 0;
    int pending_state = 0;
    unsigned long pending_millis = 0;
    int connection_route = 0;
} Finger;
Finger indexFinger;
Finger middleFinger;
Finger ringFinger;
Finger pinkyFinger;


void setup() {
  Serial.begin(115200);
  
#if OUTPUT_FORMAT == 1
  Serial.println("Hello!");
#endif

    #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
        Wire.begin();
        Wire.setClock(400000); // 400kHz I2C clock. Comment this line if having compilation difficulties
        Wire.setWireTimeout(1000, true);
    #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
        Fastwire::setup(400, true);
    #endif

    mpu.initialize();
    pinMode(INTERRUPT_PIN, INPUT);

    bool tc = mpu.testConnection();
#if OUTPUT_FORMAT == 1
    Serial.println(F("Testing device connections..."));
    Serial.println(tc ? F("MPU6050 connection successful") : F("MPU6050 connection failed"));
#endif

    devStatus = mpu.dmpInitialize();

    // supply your own gyro offsets here, scaled for min sensitivity
    mpu.setXGyroOffset(220);
    mpu.setYGyroOffset(76);
    mpu.setZGyroOffset(-85);
    mpu.setZAccelOffset(1788); // 1688 factory default for my test chip

    // make sure it worked (returns 0 if so)
    if (devStatus == 0) {
        // Calibration Time: generate offsets and calibrate our MPU6050
        mpu.CalibrateAccel(6);
        mpu.CalibrateGyro(6);
        mpu.PrintActiveOffsets();
        // turn on the DMP, now that it's ready
#if OUTPUT_FORMAT == 1
        Serial.println(F("Enabling DMP..."));
#endif
        mpu.setDMPEnabled(true);

        // enable Arduino interrupt detection
#if OUTPUT_FORMAT == 1
        Serial.print(F("Enabling interrupt detection (Arduino external interrupt "));
        Serial.print(digitalPinToInterrupt(INTERRUPT_PIN));
        Serial.println(F(")..."));
#endif
        attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), dmpDataReady, RISING);
        mpuIntStatus = mpu.getIntStatus();

        // set our DMP Ready flag so the main loop() function knows it's okay to use it
#if OUTPUT_FORMAT == 1
        Serial.println(F("DMP ready! Waiting for first interrupt..."));
#endif
        dmpReady = true;

        // get expected DMP packet size for later comparison
        packetSize = mpu.dmpGetFIFOPacketSize();
    } else {
        // ERROR!
        // 1 = initial memory load failed
        // 2 = DMP configuration updates failed
        // (if it's going to break, usually the code will be 1)
        Serial.print(F("DMP Initialization failed (code "));
        Serial.print(devStatus);
        Serial.println(F(")"));
    }

    pinMode(pin_PALM, OUTPUT);
    pinMode(pin_THUMB, OUTPUT);
    digitalWrite(pin_PALM, LOW);
    digitalWrite(pin_THUMB, LOW);
    pinMode(pin_INDEX, INPUT_PULLUP);
    pinMode(pin_MIDDLE, INPUT_PULLUP);
    pinMode(pin_RING, INPUT_PULLUP);
    pinMode(pin_PINKY, INPUT_PULLUP);

    indexFinger.pin = pin_INDEX;
    middleFinger.pin = pin_MIDDLE;
    ringFinger.pin = pin_RING;
    pinkyFinger.pin = pin_PINKY;
}

void updateFinger(struct Finger *f, unsigned long mils) {
    int con = !digitalRead(f->pin);

    if (con == f->state) {
        f->pending_state = con;
    } else {
        if (f->pending_state != con) {
            f->pending_millis = mils;
            f->pending_state = con;
        } else if (mils - f->pending_millis > FINGER_CONNECTION_DELAY) {
            f->state = con;
            if (con) {
                //newly connected, thumb or palm?
                digitalWrite(pin_PALM, HIGH);
                delay(1);
                int palm = digitalRead(f->pin);
                digitalWrite(pin_PALM, LOW);
                digitalWrite(pin_THUMB, HIGH);
                delay(1);
                int thumb = digitalRead(f->pin);
                digitalWrite(pin_THUMB, LOW);
                f->connection_route = palm ? CONNECTION_ROUTE_PALM : (thumb ? CONNECTION_ROUTE_THUMB : CONNECTION_ROUTE_UNKNOWN);
            } else {
                f->connection_route = CONNECTION_ROUTE_UNKNOWN;
            }
        }
    }

}

void loop() {
    unsigned long m = millis();

    updateFinger(&indexFinger, m);
    updateFinger(&middleFinger, m);
    updateFinger(&ringFinger, m);
    updateFinger(&pinkyFinger, m);

    // if programming failed, don't try to do anything
    if (!dmpReady) {
#if OUTPUT_FORMAT == 1
        Serial.println("DMP not ready");
        // delay(1000);
#endif
        // return;
    }
    // read a packet from FIFO
#if OUTPUT_FORMAT == 1
Serial.print(".");
#endif
    if (mpu.dmpGetCurrentFIFOPacket(fifoBuffer)) { // Get the Latest packet 
#if OUTPUT_FORMAT == 1
Serial.print(".");
#endif
            mpu.dmpGetQuaternion(&q, fifoBuffer);
            mpu.dmpGetGravity(&gravity, &q);
            mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);

    } else {
#if OUTPUT_FORMAT == 1
        Serial.println("Didn't get info packet from fifo");
#endif
    }

#if OUTPUT_FORMAT == 0
            Serial.write((uint8_t) indexFinger.connection_route);
            Serial.write((uint8_t) middleFinger.connection_route);
            Serial.write((uint8_t) ringFinger.connection_route);
            Serial.write((uint8_t) pinkyFinger.connection_route);
            Serial.write((byte*)ypr, 12);
            Serial.write(3);
            Serial.write(2);
            Serial.write(1);
            Serial.write(0);
#else
            Serial.print("ypr\t");
            Serial.print(ypr[0] * 180/M_PI);
            Serial.print("\t");
            Serial.print(ypr[1] * 180/M_PI);
            Serial.print("\t");
            Serial.print(ypr[2] * 180/M_PI);
            Serial.print("\t");

            Serial.print("I:");
            Serial.print(indexFinger.state);
            Serial.print(",");
            Serial.print(indexFinger.connection_route);
            Serial.print("\t");
            Serial.print("M:");
            Serial.print(middleFinger.state);
            Serial.print(",");
            Serial.print(middleFinger.connection_route);
            Serial.print("\t");
            Serial.print("R:");
            Serial.print(ringFinger.state);
            Serial.print(",");
            Serial.print(ringFinger.connection_route);
            Serial.print("\t");
            Serial.print("P:");
            Serial.print(pinkyFinger.state);
            Serial.print(",");
            Serial.print(pinkyFinger.connection_route);
            // Serial.print("\t");

            Serial.println();
#endif

    // delay(1000);
    #if OUTPUT_FORMAT == 0
    delay(10);
    #else
    delay(100);
    #endif
}
