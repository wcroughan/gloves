#include "ICM_20948_WDC.h"

#define OUTPUT_FORMAT 1

ICM_20948_I2C myICM;
double quats[4];
double ypr[3];

int16_t offsets[6];

const int pin_PALM = 3;
const int pin_THUMB = 4;
const int pin_INDEX = 5;
const int pin_MIDDLE = 6;
const int pin_RING = 7;
const int pin_PINKY = 8;

const int CONNECTION_ROUTE_NONE = 0;
const int CONNECTION_ROUTE_THUMB = 1;
const int CONNECTION_ROUTE_PALM = 2;
const int CONNECTION_ROUTE_BOTH = 3;
const int CONNECTION_ROUTE_UNKNOWN = 4;
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

    Wire.begin();
    Wire.setClock(400000); // 400kHz I2C clock. Comment this line if having compilation difficulties
    Wire.setWireTimeout(1000, true);

    bool initialized = false;
    while (!initialized) {
        // myICM.begin(Wire, 1);
        myICM.begin(Wire, 0); // for other address

#if OUTPUT_FORMAT == 1
        Serial.println(myICM.statusString());
#endif
        if (myICM.status != ICM_20948_Stat_Ok) {
#if OUTPUT_FORMAT == 1
            Serial.println("Trying again...");
#endif
            delay(500);
        } else {
#if OUTPUT_FORMAT == 1
            Serial.println("Connected!");
#endif
            initialized = true;
        }
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


  bool success = true; // Use success to show if the DMP configuration was successful

  // Initialize the DMP. initializeDMP is a weak function. You can overwrite it if you want to e.g. to change the sample rate
  success &= (myICM.initializeDMP() == ICM_20948_Stat_Ok);

  // DMP sensor options are defined in ICM_20948_DMP.h
  //    INV_ICM20948_SENSOR_ACCELEROMETER               (16-bit accel)
  //    INV_ICM20948_SENSOR_GYROSCOPE                   (16-bit gyro + 32-bit calibrated gyro)
  //    INV_ICM20948_SENSOR_RAW_ACCELEROMETER           (16-bit accel)
  //    INV_ICM20948_SENSOR_RAW_GYROSCOPE               (16-bit gyro + 32-bit calibrated gyro)
  //    INV_ICM20948_SENSOR_MAGNETIC_FIELD_UNCALIBRATED (16-bit compass)
  //    INV_ICM20948_SENSOR_GYROSCOPE_UNCALIBRATED      (16-bit gyro)
  //    INV_ICM20948_SENSOR_STEP_DETECTOR               (Pedometer Step Detector)
  //    INV_ICM20948_SENSOR_STEP_COUNTER                (Pedometer Step Detector)
  //    INV_ICM20948_SENSOR_GAME_ROTATION_VECTOR        (32-bit 6-axis quaternion)
  //    INV_ICM20948_SENSOR_ROTATION_VECTOR             (32-bit 9-axis quaternion + heading accuracy)
  //    INV_ICM20948_SENSOR_GEOMAGNETIC_ROTATION_VECTOR (32-bit Geomag RV + heading accuracy)
  //    INV_ICM20948_SENSOR_GEOMAGNETIC_FIELD           (32-bit calibrated compass)
  //    INV_ICM20948_SENSOR_GRAVITY                     (32-bit 6-axis quaternion)
  //    INV_ICM20948_SENSOR_LINEAR_ACCELERATION         (16-bit accel + 32-bit 6-axis quaternion)
  //    INV_ICM20948_SENSOR_ORIENTATION                 (32-bit 9-axis quaternion + heading accuracy)

  // Enable the DMP orientation sensor
  success &= (myICM.enableDMPSensor(INV_ICM20948_SENSOR_ORIENTATION) == ICM_20948_Stat_Ok);

  // Enable any additional sensors / features
  //success &= (myICM.enableDMPSensor(INV_ICM20948_SENSOR_RAW_GYROSCOPE) == ICM_20948_Stat_Ok);
  //success &= (myICM.enableDMPSensor(INV_ICM20948_SENSOR_RAW_ACCELEROMETER) == ICM_20948_Stat_Ok);
  //success &= (myICM.enableDMPSensor(INV_ICM20948_SENSOR_MAGNETIC_FIELD_UNCALIBRATED) == ICM_20948_Stat_Ok);

  // Configuring DMP to output data at multiple ODRs:
  // DMP is capable of outputting multiple sensor data at different rates to FIFO.
  // Setting value can be calculated as follows:
  // Value = (DMP running rate / ODR ) - 1
  // E.g. For a 5Hz ODR rate when DMP is running at 55Hz, value = (55/5) - 1 = 10.
  success &= (myICM.setDMPODRrate(DMP_ODR_Reg_Quat9, 0) == ICM_20948_Stat_Ok); // Set to the maximum
  //success &= (myICM.setDMPODRrate(DMP_ODR_Reg_Accel, 0) == ICM_20948_Stat_Ok); // Set to the maximum
  //success &= (myICM.setDMPODRrate(DMP_ODR_Reg_Gyro, 0) == ICM_20948_Stat_Ok); // Set to the maximum
  //success &= (myICM.setDMPODRrate(DMP_ODR_Reg_Gyro_Calibr, 0) == ICM_20948_Stat_Ok); // Set to the maximum
  //success &= (myICM.setDMPODRrate(DMP_ODR_Reg_Cpass, 0) == ICM_20948_Stat_Ok); // Set to the maximum
  //success &= (myICM.setDMPODRrate(DMP_ODR_Reg_Cpass_Calibr, 0) == ICM_20948_Stat_Ok); // Set to the maximum

  // Enable the FIFO
  success &= (myICM.enableFIFO() == ICM_20948_Stat_Ok);

  // Enable the DMP
  success &= (myICM.enableDMP() == ICM_20948_Stat_Ok);

  // Reset DMP
  success &= (myICM.resetDMP() == ICM_20948_Stat_Ok);

  // Reset FIFO
  success &= (myICM.resetFIFO() == ICM_20948_Stat_Ok);

  // Check success
  if (success) {
#if OUTPUT_FORMAT == 1
    Serial.println("DMP enabled!");
    Serial.println("Running Calibration");
    // Serial.println("Board ID:");
    // int16_t bid;
    // myICM.readWord(0, 0x00, &bid);
    // Serial.println(bid, HEX);
    // myICM.readWord(1, 0x00, &bid);
    // Serial.println(bid, HEX);
    // myICM.readWord(0, 0x00, &bid);
    // Serial.println(bid, HEX);
#endif
    // myICM.setXGyroOffset(220);
    // myICM.setYGyroOffset(76);
    // myICM.setZGyroOffset(-85);
    // myICM.setZAccelOffset(1788); // 1688 factory default for my test chip
    // myICM.calibrateAccel(15);
    // myICM.calibrateGyro(15);
    myICM.calibrateAccel(6);
    myICM.calibrateGyro(6);
  } else {
    Serial.println("Enable DMP failed!");
    Serial.println("Please check that you have uncommented line 29 (#define ICM_20948_USE_DMP) in ICM_20948_C.h...");
    while (1)
      ; // Do nothing more
  }
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
                f->connection_route = palm ? (thumb ? CONNECTION_ROUTE_BOTH : CONNECTION_ROUTE_PALM) : (thumb ? CONNECTION_ROUTE_THUMB : CONNECTION_ROUTE_NONE);
            } else {
                f->connection_route = CONNECTION_ROUTE_UNKNOWN;
            }
        }
    }

}

void quatsToYPR(double *q, double *ypr) {
    double w = q[0];
    double x = q[1];
    double y = q[2];
    double z = q[3];

    double sinr_cosp = 2 * (w * x + y * z);
    double cosr_cosp = 1 - 2 * (x * x + y * y);
    ypr[1] = atan2(sinr_cosp, cosr_cosp);

    // pitch (y-axis rotation)
    double sinp = 2 * (w * y - z * x);
    if (abs(sinp) >= 1)
        ypr[2] = copysign(M_PI / 2, sinp); // use 90 degrees if out of range
    else
        ypr[2] = asin(sinp);

    // yaw (z-axis rotation)
    double siny_cosp = 2 * (w * z + x * y);
    double cosy_cosp = 1 - 2 * (y * y + z * z);
    ypr[0] = atan2(siny_cosp, cosy_cosp);


    //in this version, w == q[0]
        //   threeaxisrot( -2*(q[2]*q[3] - q[0]*q[1]),
        //             q[0]*q[0] - q[1]*q[1] - q[2]*q[2] + q[3]*q[3],
        //             2*(q[1]*q[3] + q[0]*q[2]),
        //            -2*(q[1]*q[2] - q[0]*q[3]),
        //             q[0]*q[0] + q[1]*q[1] - q[2]*q[2] - q[3]*q[3],
        //             ypr);
        //   threeaxisrot( -2*(q[1]*q[2] - q[3]*q[0]),
        //             q[3]*q[3] - q[0]*q[0] - q[1]*q[1] + q[2]*q[2],
        //             2*(q[0]*q[2] + q[3]*q[1]),
        //            -2*(q[0]*q[1] - q[3]*q[2]),
        //             q[3]*q[3] + q[0]*q[0] - q[1]*q[1] - q[2]*q[2],
        //             ypr);
//    ypr[0] = atan2(2.0*(q[2]*q[3] + q[0]*q[1]), q[0]*q[0] - q[1]*q[1] - q[2]*q[2] + q[3]*q[3]);
//    ypr[1] = asin(-2.0*(q[1]*q[3] - q[0]*q[2]));
//    ypr[2] = atan2(2.0*(q[1]*q[2] + q[0]*q[3]), q[0]*q[0] + q[1]*q[1] - q[2]*q[2] - q[3]*q[3]);
//    ypr[0] = atan2(2.0*(q[1]*q[2] + q[3]*q[0]), q[3]*q[3] - q[0]*q[0] - q[1]*q[1] + q[2]*q[2]);
//    ypr[1] = asin(-2.0*(q[0]*q[2] - q[3]*q[1]));
//    ypr[2] = atan2(2.0*(q[0]*q[1] + q[3]*q[2]), q[3]*q[3] + q[0]*q[0] - q[1]*q[1] - q[2]*q[2]);
    // ypr[0] = atan2(2.0*(q.y*q.z + q.w*q.x), q.w*q.w - q.x*q.x - q.y*q.y + q.z*q.z);
    // ypr[1] = asin(-2.0*(q.x*q.z - q.w*q.y));
    // ypr[2] = atan2(2.0*(q.x*q.y + q.w*q.z), q.w*q.w + q.x*q.x - q.y*q.y - q.z*q.z);
        //   threeaxisrot( -2*(q.y*q.z - q.w*q.x),
        //             q.w*q.w - q.x*q.x - q.y*q.y + q.z*q.z,
        //             2*(q.x*q.z + q.w*q.y),
        //            -2*(q.x*q.y - q.w*q.z),
        //             q.w*q.w + q.x*q.x - q.y*q.y - q.z*q.z,
        //             ypr);
}

void loop() {
    unsigned long m = millis();

    updateFinger(&indexFinger, m);
    updateFinger(&middleFinger, m);
    updateFinger(&ringFinger, m);
    updateFinger(&pinkyFinger, m);


  // Read any DMP data waiting in the FIFO
  // Note:
  //    readDMPdataFromFIFO will return ICM_20948_Stat_FIFONoDataAvail if no data is available.
  //    If data is available, readDMPdataFromFIFO will attempt to read _one_ frame of DMP data.
  //    readDMPdataFromFIFO will return ICM_20948_Stat_FIFOIncompleteData if a frame was present but was incomplete
  //    readDMPdataFromFIFO will return ICM_20948_Stat_Ok if a valid frame was read.
  //    readDMPdataFromFIFO will return ICM_20948_Stat_FIFOMoreDataAvail if a valid frame was read _and_ the FIFO contains more (unread) data.
  icm_20948_DMP_data_t data;
  myICM.readDMPdataFromFIFO(&data);


  while (myICM.status == ICM_20948_Stat_FIFOMoreDataAvail)
    myICM.readDMPdataFromFIFO(&data);

  if ((myICM.status == ICM_20948_Stat_Ok) ) // Was valid data available?
  {
    //Serial.print(F("Received data! Header: 0x")); // Print the header in HEX so we can see what data is arriving in the FIFO
    //if ( data.header < 0x1000) Serial.print( "0" ); // Pad the zeros
    //if ( data.header < 0x100) Serial.print( "0" );
    //if ( data.header < 0x10) Serial.print( "0" );
    //Serial.println( data.header, HEX );

    if ((data.header & DMP_header_bitmap_Quat9) > 0) // We have asked for orientation data so we should receive Quat9
    {
      // Q0 value is computed from this equation: Q0^2 + Q1^2 + Q2^2 + Q3^2 = 1.
      // In case of drift, the sum will not add to 1, therefore, quaternion data need to be corrected with right bias values.
      // The quaternion data is scaled by 2^30.

      //Serial.printf("Quat9 data is: Q1:%ld Q2:%ld Q3:%ld Accuracy:%d\r\n", data.Quat9.Data.Q1, data.Quat9.Data.Q2, data.Quat9.Data.Q3, data.Quat9.Data.Accuracy);

      // Scale to +/- 1
      quats[1] = ((double)data.Quat9.Data.Q1) / 1073741824.0; // Convert to double. Divide by 2^30
      quats[2] = ((double)data.Quat9.Data.Q2) / 1073741824.0; // Convert to double. Divide by 2^30
      quats[3] = ((double)data.Quat9.Data.Q3) / 1073741824.0; // Convert to double. Divide by 2^30
      quats[0] = sqrt(1.0 - ((quats[1] * quats[1]) + (quats[2] * quats[2]) + (quats[3] * quats[3])));

      quatsToYPR(quats, ypr);
    }


    offsets[0] = myICM.getXAccelReading();
    offsets[1] = myICM.getYAccelReading();
    offsets[2] = myICM.getZAccelReading();
    offsets[3] = myICM.getXGyroReading();
    offsets[4] = myICM.getYGyroReading();
    offsets[5] = myICM.getZGyroReading();
  }
  else {
      #if OUTPUT_FORMAT == 1
      Serial.print("Couldn't read:\t");
      Serial.println(myICM.status);
      #endif
  }

#if OUTPUT_FORMAT == 0
            Serial.write((uint8_t) indexFinger.connection_route);
            Serial.write((uint8_t) middleFinger.connection_route);
            Serial.write((uint8_t) ringFinger.connection_route);
            Serial.write((uint8_t) pinkyFinger.connection_route);
            Serial.write((byte*)ypr, 12);
            Serial.write((byte*)offsets, 12);
            Serial.write(3);
            Serial.write(2);
            Serial.write(1);
            Serial.write(0);
#else
            // Serial.print(F("Q1:"));
            // Serial.print(quats[1], 3);
            // Serial.print(F(" Q2:"));
            // Serial.print(quats[2], 3);
            // Serial.print(F(" Q3:"));
            // Serial.print(quats[3], 3);

            Serial.print(F("Y:"));
            Serial.print(ypr[0], 3);
            Serial.print(F(" P:"));
            Serial.print(ypr[1], 3);
            Serial.print(F(" R:"));
            Serial.print(ypr[2], 3);
            Serial.print("\t");
            Serial.print(F(" Accuracy:"));
            Serial.print(data.Quat9.Data.Accuracy);
            Serial.print("\t");


            // Serial.print("I:");
            // Serial.print(indexFinger.state);
            // Serial.print(",");
            // Serial.print(indexFinger.connection_route);
            // Serial.print("\t");
            // Serial.print("M:");
            // Serial.print(middleFinger.state);
            // Serial.print(",");
            // Serial.print(middleFinger.connection_route);
            // Serial.print("\t");
            // Serial.print("R:");
            // Serial.print(ringFinger.state);
            // Serial.print(",");
            // Serial.print(ringFinger.connection_route);
            // Serial.print("\t");
            // Serial.print("P:");
            // Serial.print(pinkyFinger.state);
            // Serial.print(",");
            // Serial.print(pinkyFinger.connection_route);
            // Serial.print("\t");

            // Serial.println("Offsets:\nXG\tYG\tZG\tXA\tYA\tZA");
            Serial.print(myICM.getXGyroOffset());
            Serial.print("\t");
            Serial.print(myICM.getYGyroOffset());
            Serial.print("\t");
            Serial.print(myICM.getZGyroOffset());
            Serial.print("\t");
            Serial.print(myICM.getXAccelOffset());
            Serial.print("\t");
            Serial.print(myICM.getYAccelOffset());
            Serial.print("\t");
            Serial.print(myICM.getZAccelOffset());

            Serial.println();
#endif

    // delay(1000);
    #if OUTPUT_FORMAT == 0
    delay(10);
    #else
    delay(100);
    #endif
}
