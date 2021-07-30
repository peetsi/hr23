
/*
 * hzrr200 Regler EEPROM read-write
 * Datei "hr2_eeprom.h"
 * 
 * 
 * 
 */


#ifndef hr2_doc_h
#define hr2_doc_h

/* 
 *  
 *  
FRAGEN AN BURKHARD DOBLINGER:
=============================
- Timing bei Zimmertemperatur Regler?
- Regelparameter factory settings durchgehen und festlegen



*/

/*  *************************
 *  CHANGE ON VERSION UPDATES
 *  *************************
 *  see file "hr2_regler.h" and change version 
 *  Name, revision number, date for software and hardware as required
 */

/*  *********************
 *  ZUSÄTZLICHE LIBRARIES
 *  *********************
 *  see: hr2_reg0Xpl.ino
 */

/*  *******************************
 *  PROGRAMMIERUNG DES ARDUINO NANO
 *  *******************************
 *  The program uses almost the whole FLASH meory of the AtMega328 uC.
 *  Make sure the new bootloader for the Arduino Nano is installed:
 *  1. install new bootloader on Nano if needed:
 *    1.1. use an ISP programmer, e.g. Atmel ISP Mk2 or ArduinoISP
 *         (can be wired and loaded to e.g. an Arduino Nano,
 *         examples 11. ArduinoISP; wire and program it)
 *    1.2. select from Tools (Werkzeuge): 
 *         - Board: "Arduino Nano"
 *         - Controller: "ATmega328P" (NOT old Bootlaoder!!!)
 *         - USB Port to which the ISP programmer is connected
 *         - Programmer: <select your ISP programmer>
 *    1.3. Start Tools (Werkzeuge) -> burn bootloader (Bootloader brennen) 
 *    
 *    2. program the "hr2" Software:
 *      2.1. - connect the Nano to USB port, 
 *           - select Board, Processor and Port;
 *           - program as usual with "upload" button, Sketch->Upload, or Ctrl-U
 *      2.2. If the ISP programmer is connected, you can use it instead
 *           - connect and setup as described in 1.2.
 *           - upload using programmer (Hochladen mit Programmer), or Shift-Ctrl-U
 */



/*  ******************
 *  Data organization:
 *  ******************

1. Module Data
--------------
There are two main types of operation data:
S: Status information which shows state- or measured values
P: Parameter data which can be stored in EEPROM in the modules
S and P are kept in separate data structures in the Modules and here.

Parameter data of this module are stored and operated from in RAM.
It can be stored in EEPROM and recalled from EEPROM.
It can be sent to the 'Zentrale' from RAM or be received from 'Zentrale' to RAM.

Up to 30 modules can be connected in one RS-485 Network.
Each Module contains 3 Regulators 1,2,3 or index 0,1,2; 
- all regulators are normally 'Ruecklaufregler'
- reg1 (idx=0) is always set to active; 
- reg2 or reg3 (idx=1 or =2) may be activated by jumper settings on PCB
- reg2 (idx=1) may be switched to regulate a room-temperature; selected by jumper settings.

The data structures are set accordingly:
A list of up to 30 modules with module-related data, each contains a list with
tree regulator data sets is defined for each S (status) and P (parameters).

1.1. Status data (S)
- - - - - - - - - - -
- can be read from the modules
- are stored in intervals to a log-file
- are diplayed on demand on the screen

1.2. Parameter data (P)
- - - - - - - - - - - -
- handling insinde a module by commands:
  - set to factory settings (data reside in RAM)
  - store actual setting in RAM to EEPROM
  - read from EERPOM to actual setting in RAM
- transfer Parameter between module and Zentrale:
  - read parameter from module RAM to Zentrale
  - write parameter from Zentrale to module RAM
  - store parameter of a module to a file in Zentrale
  - read parameter of a module from file in Zentrale
  - The parameter files ar ein radable form and may be set manually.

  1.3. Module parameter data handling:
- - - - - - -- - - - - - -- - - - - -
- After start the module software tries to read parameter data from EEPROM into RAM.
- If this fails, it reads parameter from FLASH memory to RAM and stores them to EEPROM.
- RAM parameter data can be changed from Zentrale with specific commands, e.g. for tests
- another command stores the RAM parameter to EEPROM to make them permanent after a new-start
- another command reads EEPROM data to RAM to recover its original stat
- another command sets RAM-data to factory settings.

 */




/*  *********************************
    Bedienung des hzrr200 Regler Moduls
    ***********************************

Status LCD
==========
*** Tastenbelegung:
Taste SW1 -> Service LCD


Service LCD
===========
*** Tastenbelegung:
Taste SW1 -> Funktionswahl
Tasten SW2...SW4 -> Motor1 bis 3, Funktion ausführen
Taste SW5 -> Verlassen des Service Menüs

nach 10 Minuten automatisches Verlassen des Service Menüs


LCD Beleuchtung
===============
automatisch abschalten nach 10 Minuten, parametriert




*/
#endif   //  hr2_doc_h
