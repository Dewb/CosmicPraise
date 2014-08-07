
// Cosmic Praise RS485-MIDI adapter
// Michael Dewberry
//
// based on Sparkfun MIDI shield sample
// https://www.sparkfun.com/products/9595
// and
// RS485 soft-serial example
// http://arduino-info.wikispaces.com/SoftwareSerialRS485Example

// MIDI Shield components
#define KNOB1  0
#define KNOB2  1

#define BUTTON1  2
#define BUTTON2  3
#define BUTTON3  4

#define LED1  7
#define LED2  6

byte note;
int pot;
byte byte1;
byte byte2;
byte byte3;

// Software Serial for RS485 (converted to TTL by external circuit)

#include <SoftwareSerial.h>
#define SSerialRX        10  //Serial Receive pin
#define SSerialTX        11  //Serial Transmit pin
#define SSerialTxControl 12  //RS485 Direction control

#define RS485Transmit    HIGH
#define RS485Receive     LOW

#define Pin13LED         13

SoftwareSerial RS485Serial(SSerialRX, SSerialTX);

int byteReceived;
int byteSend;

void setup() {
  setupMIDI();
  setupRS485();
}

void setupMIDI() {

  pinMode(LED1,OUTPUT);   
  pinMode(LED2,OUTPUT);

  pinMode(BUTTON1,INPUT);
  pinMode(BUTTON2,INPUT);
  pinMode(BUTTON3,INPUT);

  digitalWrite(BUTTON1,HIGH);
  digitalWrite(BUTTON2,HIGH);
  digitalWrite(BUTTON3,HIGH);

  for(int i = 0;i < 10;i++) // Flash on startup
  {
    digitalWrite(LED1,HIGH);  
    digitalWrite(LED2,LOW);
    delay(30);
    digitalWrite(LED1,LOW);  
    digitalWrite(LED2,HIGH);
    delay(30);
  }
  digitalWrite(LED1,HIGH);   
  digitalWrite(LED2,HIGH);

  // MIDI baudrate = 31250
  Serial.begin(31250);     
}

void setupRS485() {
  pinMode(Pin13LED, OUTPUT);   
  pinMode(SSerialTxControl, OUTPUT);    
  digitalWrite(SSerialTxControl, RS485Receive);   
  
  RS485Serial.begin(4800);  
}

void loop () {

  // Send MIDI in response to buttons (debugging/future use)

  //pot = analogRead(0);
  //note = pot/8;  // convert value to value 0-127
  
  if(button(BUTTON1))
  {  
    Midi_Send(0x90,0x21,0x45);
    while(button(BUTTON1));
  }
  if(button(BUTTON2))
  {  
    Midi_Send(0x90,0x22,0x45);
    while(button(BUTTON2));
  }
  if(button(BUTTON3))
  {  
    Midi_Send(0x90,0x23,0x45);
    while(button(BUTTON3));
  }
  
  // Loopback MIDI IN port to MIDI OUT (debugging/future use)
  if(Serial.available() > 0)
  {
    byte1 = Serial.read();
    byte2 = Serial.read();
    byte3 = Serial.read();

    Midi_Send(byte1, byte2, byte3);
  }
   
   
  if (RS485Serial.available()) {
    digitalWrite(Pin13LED, HIGH);  
    byteReceived = RS485Serial.read(); 

    Midi_Send(0x90, 0x40, 0xFF);

    delay(10);
    digitalWrite(Pin13LED, LOW);  
   }
     

}

void Midi_Send(byte cmd, byte data1, byte data2) {
  Serial.write(cmd);
  Serial.write(data1);
  Serial.write(data2);
}

void blink(){
  digitalWrite(LED1, HIGH);
  delay(100);
  digitalWrite(LED1, LOW);
  delay(100);
}

char button(char button_num)
{
  return (!(digitalRead(button_num)));
}
