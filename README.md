# Shiny Catcher
Modified Nintendo Switch Joy-Con controller to help Shiny hunting Pokémon in Pokémon FireRed and LeafGreen versions.

### Live Stats
![Encounters](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fphiphiii%2FShinyCatcher%2Frefs%2Fheads%2Fmain%2Fencounters.json&query=$.encounters&label=Encounters&color=blue&style=flat-square)
![Shiny Found](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fphiphiii%2FShinyCatcher%2Frefs%2Fheads%2Fmain%2Fencounters.json&query=$.shiny_found&label=Shiny%20Found&color=gold&style=flat-square)

First shiny: Charmander - 2025-05-05 11:28 AM (UTC) | 2228 encounters

## About the project
The Shiny Catcher is a hardware-modified Joy-Con controlled by an external ESP32 that communicates with a desktop app. Currently, the project is not a standalone bot; it is connected to a PC which handles all OpenCV work. While the Joy-Con is no longer usable as a standard controller right now, future updates might allow it to function as both a dedicated "Shiny Catcher" and a regular controller.

## Technologies
### Hardware:
- **Microcontroller** - ESP32
- **Controller** - Bootleg modified Nintendo Switch Joy-Con
- **Components:** 
  - Optoisolator PC817
  - Resistors and jumper wires
  - FPC/FFC to 2.54mm DIP Breakout Board (5-pin, 0.5mm pitch)
  - FFC/FPC Flexible Flat Ribbon Cable (5-pin, 0.5mm pitch)
  - Red LED
  - Buzzer with a generator
- **Additional:**
  - 4K HDMI to USB Capture Card
  - HDMI Cable  
  - USB-C Cable

### Software:
- **Languages:**
  - **Python with PyQt6** - for desktop App (NOT YET IMPLEMENTED)
  - **C/C++** - for controlling ESP32
- **Computer Vision** - using OpenCV
