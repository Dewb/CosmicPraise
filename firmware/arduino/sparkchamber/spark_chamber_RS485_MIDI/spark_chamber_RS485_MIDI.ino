
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

#define BUTTON2  3
#define BUTTON3  4

#define LED1  7
#define LED2  6

byte note;
int pot;
byte byte1;
byte byte2;
byte byte3;

volatile int triggers_received = 0;

#define Pin13LED         13


void setup() {
  setupMIDI();
  setupInput();
}

void setupMIDI() {

  pinMode(LED1,OUTPUT);   
  pinMode(LED2,OUTPUT);

  pinMode(BUTTON2,INPUT);
  pinMode(BUTTON3,INPUT);

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

void setupInput() {
  pinMode(Pin13LED, OUTPUT);  
  // interrupt 0 = pin 2 
  attachInterrupt(0, triggered, RISING); 
}

void triggered() {
  triggers_received++;
}

void loop () {

  // Send MIDI in response to buttons (debugging/future use)

  //pot = analogRead(0);
  //note = pot/8;  // convert value to value 0-127
  
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
   
  // Send a note for every TTL low->high event we recieve on pin 2
  if (triggers_received > 0) {
      Midi_Send(0x90, 0x40, 0x7F);
      digitalWrite(Pin13LED, HIGH); 
      triggers_received--; 
    }
   } else { 
     digitalWrite(Pin13LED, LOW);  
   }
     

}

void Midi_Send(byte cmd, byte data1, byte data2) {
  Serial.write(cmd);
  Serial.write(data1);
  Serial.write(data2);
}

char button(char button_num)
{
  return (!(digitalRead(button_num)));
}
