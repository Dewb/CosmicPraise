
/*
  Cosmic Praise 
  Search Light Motor Controller with Ethernet!
  Burning Man 2014
  seph@directionless.org

  Very quick and dirty ethernet + motor controller sketch.

  Using UDP for two reasons:
  1. It has a saner arduino parse-packet interface
  2. Because it's packet based, it's inherently non-blocking

  This code is a very quick hack. I'm sure it has bugs

*/


/*
  Big Caveats:
  DO NOT IGNORE

  I was seeing motor2 faults. I'm not sure if it's a pololu board
  error, or a pin incompatbility with the ethernet shield and the
  motor controller. So do NOT use motor2. Motor1 works...

*/

/*
  # General Usage Notes #


  ## Acceleration ##

  This implements smoothing on velocity changes. We do this via
  tracking the requested speed, and the current speed, and every
  ACCEL_PERIOD stepping the lessor of req-current or ACCEL_STEP.  As
  tuned now, we step *at most* 5 every 100ms. Given that we 0-400 for
  speed, this means it takes up a total of 80 cycles, or 8 seconds
  total. This feels pretty smooth.


  ## Network Protocol ##

  This has a simple network protocol, partly designed for ease of
  implementation. It's using UDP, as the packet nature of UDP means
  it's a more natural fit for non-blocking code.

  Connect via udp on whatever the port, (I use netcat, eg: "nc -u
  10.42.19.4 6565" and hit return. You should get a status message,
  and instructions. To set the speed use "s <speed>" for values
  between -400 and 400. Anything else will reprint the status message.


*/

#include "DualVNH5019MotorShield.h"
#include <math.h>
#include <ctype.h>
#include <SPI.h>
#include <Ethernet.h>
#include <EthernetUdp.h>

#define SPEED_MAX 400
#define SPEED_MIN -400
#define ACCEL_PERIOD 100
#define ACCEL_STEP 5

int current_speed = 0;
unsigned long last_speed_adjust = 0;

#define draw_window_size 100
int draw_window_position = 0;
unsigned int draw_window[draw_window_size] = {0};

// Variables for reading/parsing network crap
int req_speed = 20;
char req_string[3] = {0};
int req_direction = 1;
int req_parser = 0;


DualVNH5019MotorShield md;


// Enter a MAC address and IP address for your controller below.
// The IP address will be dependent on your local network/
// Grab something from xen's mac address range.
byte mac[] = { 0x00, 0x16, 0x3E, 0x17, 0xFA, 0x22 };
IPAddress ip(10, 0, 0, 71);

unsigned int localPort = 6565;

// buffers for receiving and sending data
char packetBuffer[UDP_TX_PACKET_MAX_SIZE] = {0}; //buffer to hold incoming packet,
char ReplyBuffer[512] = {0};       // a string to send back
int packetSize = 0;

// An EthernetUDP instance to let us send and receive packets over UDP
EthernetUDP UDP;

void setup() {
  Serial.begin(9600);
  md.init();
  req_speed = 20;
  set_speed(req_speed);
  stopIfFault();

  Ethernet.begin(mac, ip);
  UDP.begin(localPort);

}

void loop() {
  stopIfFault();

  // if there's data available, read a packet
  // parse it, and we'll get the global req_speed set.
  packetSize = UDP.parsePacket();
  if (packetSize) {
    Serial.print("Received packet of size ");
    Serial.println(packetSize);
    handle_packet();

    // send a reply full of status info
    reply_info().toCharArray(ReplyBuffer, sizeof(ReplyBuffer));
    UDP.beginPacket(UDP.remoteIP(), UDP.remotePort());
    UDP.write(ReplyBuffer);
    UDP.endPacket();
  }

  // Handle the Motor Control
  // Delay for N millis, then trigger a speed hander
  if( (millis() - last_speed_adjust ) >= ACCEL_PERIOD ) {
    set_speed(req_speed);
  }

  // Update the rolling window of current draw
  draw_window_position = draw_window_position % draw_window_size;
  draw_window[draw_window_position++] = md.getM1CurrentMilliamps();

  delay(10);
}

unsigned int current_draw() {
  int  total = 0;
  for (int i = 0; i < draw_window_size; i++) {
    total += draw_window[i];
  }
  return total/draw_window_size;
}

void handle_packet() {
  // blank the read buffer and read the packet
  memset(packetBuffer, 0, sizeof(packetBuffer));
  UDP.read(packetBuffer, packetSize);

  Serial.println("Contents:");
  Serial.println(packetBuffer);

  // Parse that string!
  // Painfully manually, but should be pretty solid?
  memset(req_string, 0, sizeof(req_string));
  req_parser = 0;
  req_direction = 1;
  if(packetBuffer[req_parser] == 'S' || packetBuffer[req_parser] == 's') {
    req_parser++;
    if(packetBuffer[req_parser++] == ' ') {
      if(packetBuffer[req_parser] == '-') {
	req_direction = -1;
	req_parser++;
      }

      // Finally, get our 3 numbers
      // (yes, nested ifs)
      if( isdigit(packetBuffer[req_parser])) {
	req_string[0] = packetBuffer[req_parser++];
	if( isdigit(packetBuffer[req_parser])) {
	  req_string[1] = packetBuffer[req_parser++];
	  if( isdigit(packetBuffer[req_parser])) {
	    req_string[2] = packetBuffer[req_parser++];
	  }
	}
      }
      // Well, we got a string
      Serial.print("Got a request: ");
      req_speed = max(min(atoi(req_string) * req_direction, SPEED_MAX), SPEED_MIN);
      Serial.println(req_speed);
    }
  }
}

// Print current state + help
String reply_info() {
  String reply = "\n\n\n";
  reply += "Cosmic Praise, Burning Man 2014, spire motor";
  reply += "\n";
  reply += "speed: ";
  reply += current_speed;
  reply += " request: ";
  reply += req_speed;
  reply += " milliamps: ";
  reply += current_draw();
  reply += "\n";
  reply += "Enter s <speed> (between -400 and 400) to set speed";
  reply += "\n";
  reply += "(Anything else to display this)";
  reply += "\n";
  return reply;
}

int calculateSpeedChange(int req_speed) {
  // If the difference is greater than X, step slowly.
  int delta_v = req_speed - current_speed;
  if( delta_v > 0) {
    // accelerating
    return min(5, delta_v);
  }
  else {
    // de-accelerating
    return max(-5, delta_v);
  }
  // WTF
  return 0;      
}


void set_speed(int req_sp) {
  int sp = current_speed + calculateSpeedChange(req_sp);
  //md.setSpeeds(sp, sp);
  md.setM1Speed(sp);

  Serial.print("current: ");
  Serial.print(current_speed);
  Serial.print(" requested: ");
  Serial.print(req_sp);
  Serial.print(" got: ");
  Serial.print(sp);
  Serial.print(" draw: ");
  Serial.print(current_draw());
  Serial.println();

  last_speed_adjust = millis();
  current_speed = sp;
}

void stopIfFault() {
  if (md.getM1Fault()) {
    Serial.println("M1 fault");
    while(1);
  }
  //  if (md.getM2Fault()) {
  //    Serial.println("M2 fault");
  //    while(1);
  //  }
}

