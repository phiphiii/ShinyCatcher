# Shiny Catcher
Modified Nintendo Switch Joy-Con controller to help Shiny hunting Pokémon in Pokémon FireRed and LeafGreen versions.
## About the project
The Shiny Catcher is a hardware-modified Joy-Con controlled by an external ESP32 that communicates with a desktop app. Currently, project is a not standalone bot, it is connected to PC which handles all opencv work. While the Joy-Con is no longer usable as a standard controller right now, future updates might allow it to function as both a dedicated "Shiny Catcher" and a regular controller.
## Technologies
### Hardware:
- **Microcontroller:** - ESP32
- **Controller:** - Bootleg modified Nintendo Switch Joy-Con
- **Compontents:** 
  - Optoisolator PC817
  - Resistors and jumper wires
  - Digital potentiomater X9C103S
 - **Additional:**
  - 4K HDMI to USB Capture Card
  - HDMI Cable  
### Softwere
- **Languages:**
   - **Python with PyQt6** - for desktop App
   - **C/C++** - for controling ESP32
- **Computer Vison** - using openCV 
- 