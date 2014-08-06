#include "DualVNH5019MotorShield.h"
#include <math.h>

/*
  Cosmic Praise 
  Search Light Motor Controller
  Burning Man 2014
  seph@directionless.org
  
  This is a trivial sketch for driving a polulu shield. We're using as
  a speed controller for the search light
  
  Motor measures:
  15 amp inrush (to full on, no smoothing)
  2-3 amps loaded with my foot
  3-4 amps loaded with the searchlight.

  https://github.com/pololu/dual-vnh5019-motor-shield
  void setM1Speed(int speed)
  void setM2Speed(int speed)
  void setSpeeds(int m1Speed, int m2Speed)
  Speed should be between -400 and 400

  void setM1Brake(int brake)
  void setBrakes(int m1Brake, int m2Brake)
  400 is full break
   
 */

/*
  Motor Speed constants

  The controller is -400 - 400. We may want to limit that more
*/
#define SPEED_MAX 400
#define SPEED_MIN -400
#define MAX_DELTA 10
#define DELAY 100


int pot_pin = 5;

int current_speed = 0;
unsigned long last_speed_adjust = 0;

DualVNH5019MotorShield md;

/*
  Acceleration.
 
  To avoid sudden direction shifts, we implement acceleration.
  This should reduce current draw.
 
  This is done via a simple linedar velocity change. Basically, never
  adjust more than X units every M milliseconds.

  Converting to a nice S-curve is future work
 */
 
int calculateSpeedChange(int req_speed) {
  // If the difference is greater than X, step slowly.
  int delta_v = req_speed - current_speed;
  if( delta_v > 0) {
    // accelerating
    return min(MAX_DELTA, delta_v);
  }
  else {
    // de-accelerating
    return max(-MAX_DELTA, delta_v);
  }
  // WTF
  return 0;
      
}

void set_speed(int req_sp) {
  
  int sp = current_speed + calculateSpeedChange(req_sp);
  md.setSpeeds(sp, sp);

  Serial.print("current: ");
  Serial.print(current_speed);
  Serial.print(" requested: ");
  Serial.print(req_sp);
  Serial.print(" got: ");
  Serial.print(sp);
  Serial.print(" draw: ");
  Serial.print(md.getM1CurrentMilliamps());
  Serial.println();

  
  last_speed_adjust = millis();
  current_speed = sp;
}

void stopIfFault() {
  if (md.getM1Fault()) {
    Serial.println("M1 fault");
    while(1);
  }
  if (md.getM2Fault()) {
    Serial.println("M2 fault");
    while(1);
  }
}


void setup() {
  Serial.begin(115200);
  Serial.println("Dual VNH5019 Motor Shield");
  md.init();
  current_speed = 0;
  stopIfFault();
}


void loop() {
  delay(DELAY);
  stopIfFault();
  // analogread is 0-1023
  // motor is -400 - 400  `
  int new_speed = map(analogRead(pot_pin), 0, 1023, SPEED_MIN, SPEED_MAX);
  set_speed(new_speed);
  stopIfFault();
}
