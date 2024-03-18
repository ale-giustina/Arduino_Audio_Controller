#include <math.h>

String command;
String previous_state = "";
bool update=true;

void setup() {
  Serial.begin(9600); // Initialize serial communication
  Serial.setTimeout(10);
  pinMode(2, INPUT_PULLUP); // switch
  pinMode(3, INPUT_PULLUP); // upper button
  pinMode(4, INPUT_PULLUP); // lower button
  pinMode(5, OUTPUT);       // lower led
  pinMode(6, OUTPUT);       // upper led
  pinMode(7, INPUT_PULLUP); // pot. switch
}

void loop() {
  update=false;
  
  String current_state = "";

  // Check the state of each input
  if (digitalRead(2) == HIGH) current_state += "[0,"; // switch
  else current_state += "[1,";
  
  if (digitalRead(3) == HIGH) current_state += "0,"; // upper button
  else current_state += "1,";
  
  if (digitalRead(4) == HIGH) current_state += "0,"; // lower button
  else current_state += "1,";

  if (digitalRead(7) == HIGH) current_state += "0,"; // lower button
  else current_state += "1,";
  
  if (current_state != previous_state) {
    previous_state = current_state;
    update=true;
  }

  // Check the state of each potentiometer
  for (int i = 0; i < 4; i++) {

    int pot_reading = analogRead(A0 + i); // Read potentiometer input
    static int previous_pot_reading[4] = {0}; // Static array to store previous potentiometer readings
    static int pot_tresh[4] = {4,6,4,4};
    // Check if the difference between the current and previous potentiometer readings exceeds the threshold
    if (abs(int((pot_reading+previous_pot_reading[i])/2) - previous_pot_reading[i]) > pot_tresh[i]) {
      update=true;
      previous_pot_reading[i] = int((pot_reading+previous_pot_reading[i])/2); // Update previous potentiometer reading
      current_state += int((pot_reading+previous_pot_reading[i])/2);
    }
    else{

      current_state += pot_reading;

    }
    if (i < 3) {
      current_state += ","; // Add comma as delimiter between potentiometer states
    }
    if (i==3){
      current_state += "]";
    }
  }

  // Check for state changes and send data
  if (update) {
    Serial.println(current_state);
  }
  
  // Process commands from Python
  command = Serial.readStringUntil('\n');
  if (command.equals("pin5high")) digitalWrite(5, HIGH);
  else if (command.equals("pin6high")) digitalWrite(6, HIGH);
  else if (command.equals("pin5low")) digitalWrite(5, LOW);
  else if (command.equals("pin6low")) digitalWrite(6, LOW);

}