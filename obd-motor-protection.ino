/*********************************************************************************************************************
 * Project : OBD Motor Protection
 * Author  : PEB <pebdev@lavache.com> 
 * Date    : 2023.10.29
 *********************************************************************************************************************
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *********************************************************************************************************************/


/** I N C L U D E S **************************************************************************************************/
#include <mcp_can.h>


/** D E F I N E S ****************************************************************************************************/
// VERSION
#define VERSION_SW                          "v1.01"

// Pinout
#define PINOUT_OUT_BUZZER                   (3)
#define PINOUT_OUT_LED_ACTIVITY             (4)

// OBD data type
#define OBD_TYPE_ENGINE_LOAD                (1)
#define OBD_TYPE_FUEL_TRIME                 (2)
#define OBD_TYPE_INJECTION_TIME             (3)
#define OBD_TYPE_ENGINE_SPEED               (4)

// Configurations
#define CONFIG_SOUND_ENABLED                (1)     // 1: Enabled | 0: Disabled
#define CONFIG_LIMIT_MAX_INJECTION_TIME     (2.5)


/** D E C L A R A T I O N S ******************************************************************************************/
// MCP2515 configuration
const int MCP_CS_PIN  = 10;
const int MCP_INT_PIN = 2;
MCP_CAN CAN(MCP_CS_PIN);

// Internal variable of our system
bool   LED_activity_state = false;
double UDS_engine_load    = 0.0;
double UDS_fuel_trime     = 0.0;
double UDS_injection_time = 0.0;
double UDS_engine_speed   = 0.0;


/** M A I N  F U N C T I O N S ***************************************************************************************/
void setup (void)
{
  // Debug connection
  Serial.begin(115200);
  Serial.print("version : ");
  Serial.println(VERSION_SW);

  // Initilization
  led_init();
  sound_init();
  obd_init();
}

/*-------------------------------------------------------------------------------------------------------------------*/
void loop (void)
{
  uint8_t data_engine_load[]    = {0x02, 0x01, 0x04, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};
  uint8_t data_fuel_trime[]     = {0x02, 0x01, 0x06, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};
  uint8_t data_injection_time[] = {0x03, 0x22, 0x12, 0x8C, 0x00, 0x00, 0x00, 0x00};
  uint8_t data_engine_speed[]   = {0x02, 0x01, 0x0C, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};

  // Read wanted CAN data
  //UDS_engine_load     = obd_read_value(OBD_TYPE_ENGINE_LOAD, 0x7DF, sizeof(data_engine_load), data_engine_load);            // Calculated engine load
  //UDS_fuel_trime      = obd_read_value(OBD_TYPE_FUEL_TRIME, 0x7DF, sizeof(data_fuel_trime), data_fuel_trime);               // Short term fuel trim (bank 1)
  UDS_injection_time  = obd_read_value(OBD_TYPE_INJECTION_TIME, 0x7E0, sizeof(data_injection_time), data_injection_time);     // Injection time
  UDS_engine_speed    = obd_read_value(OBD_TYPE_ENGINE_SPEED, 0x7DF, sizeof(data_engine_speed), data_engine_speed);           // Engine speed

  // Play a sound to alert driver from the critical motor state
  if (obd_critical_motor_state())
  {
    sound_alert();
  }

  // Led activity
  led_activity();
}


/** O B D ************************************************************************************************************/
void obd_init (void)
{
  // CAN connection to inject simulated data
  Serial.print("Attempting to connect to CAN bus ...");

  // start the CAN bus at 500 kbps
  if (CAN.begin(MCP_ANY, CAN_500KBPS, MCP_8MHZ) != CAN_OK)
  {
    Serial.println("Starting CAN failed!");
    while (1);
  }

  // Configure mode and interruption
  CAN.setMode(MCP_NORMAL);
  pinMode(MCP_INT_PIN, INPUT);
  Serial.println("CAN connection is established");
}

/*-------------------------------------------------------------------------------------------------------------------*/
double obd_read_value (uint8_t _obd_data_type, uint16_t _addr, uint8_t _lenght, uint8_t* _request)
{
  double retval = -1.0;
  long unsigned int rxId = 0;
  uint8_t rxBuf[8] = {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00};
  uint8_t len = 0;
  
  // Send request
  obd_send_packet(_addr, _lenght, _request);

  // Loop until we receive the wanted PID
  for (uint8_t i=0; i<10; i++)
  {
    // "Interrupt" pin check
    if (!digitalRead(MCP_INT_PIN))
    {
      // Read can message
      CAN.readMsgBuf(&rxId, &len, rxBuf);

      // Read CAN buffer only ECU response
      if (rxId != 0x7E8)
      {
        //Serial.print("INVALID ID, REJECTED : ");
        //Serial.println(rxId, HEX);
        continue;
      }

      // Check if it's our frame
      bool is_invalid_frame = false;
      for (uint8_t j=2; j<4; j++)
      {
        // If we can't find ID, we skip this frame
        if (rxBuf[j] != _request[j])
        {
          is_invalid_frame = true;
          Serial.println("INVALID FRAME, REJECTED");
          break;
        }
      }

      // If this frame is valid, we return data
      if (is_invalid_frame == false)
      {
        retval = obd_extract_value(_obd_data_type, rxBuf);
      }

      break;
    }

    delay(30);
  }

  return retval;
}

/*-------------------------------------------------------------------------------------------------------------------*/
double obd_extract_value (uint8_t _obd_data_type, uint8_t* _data)
{
  double retval = 0.0;

  switch(_obd_data_type)
  {
    case OBD_TYPE_INJECTION_TIME:
      retval = ((double)(_data[6]*256+_data[7])/2500.0);
      break;
    case OBD_TYPE_ENGINE_SPEED:
      retval = ((double)(_data[3]*256+_data[4])*0.25);
      break;
    default:
      Serial.println("INVALID OBD DATA TYPE");
  }

  Serial.println(retval);

  return retval;
}

/*-------------------------------------------------------------------------------------------------------------------*/
void obd_send_packet (uint16_t _addr, uint8_t _lenght, uint8_t* _data)
{
  delay(60);

  if (CAN.sendMsgBuf(_addr, 0, _lenght, _data) != CAN_OK)
  {
    Serial.println("Error Sending Message...");
  }
}

/*-------------------------------------------------------------------------------------------------------------------*/
bool obd_critical_motor_state (void)
{
  bool retval = false;

  if ((UDS_engine_speed > 1500) && (UDS_injection_time > CONFIG_LIMIT_MAX_INJECTION_TIME))
  {
    retval = true;
    //Serial.print("/!\\ CRITICAL MOTOR STAT /!\\");
  }

  return retval;
}


/** L E D ************************************************************************************************************/
void led_init (void)
{
  // Pinout
  pinMode(PINOUT_OUT_LED_ACTIVITY, OUTPUT);
}

/*-------------------------------------------------------------------------------------------------------------------*/
void led_activity (void)
{
  LED_activity_state = !LED_activity_state;
  digitalWrite(PINOUT_OUT_LED_ACTIVITY, LED_activity_state);
}


/** S O U N D ********************************************************************************************************/
void sound_init (void)
{
  // Pinout
  pinMode(PINOUT_OUT_BUZZER, OUTPUT);

  // Play sound to notify that the box is ready
  #if CONFIG_SOUND_ENABLED == 1
  tone(PINOUT_OUT_BUZZER, 4000, 250);
  delay(500);
  tone(PINOUT_OUT_BUZZER, 4000, 250);
  delay(500);
  #endif
  noTone(PINOUT_OUT_BUZZER);
}

/*-------------------------------------------------------------------------------------------------------------------*/
void sound_alert (void)
{
  #if CONFIG_SOUND_ENABLED == 1
  const byte countNotes = 8;
  int frequences[countNotes] = {
    4000, 4000, 4000, 4000, 4000, 4000, 4000, 4000
  };
  int durations[countNotes] = {
    30, 30, 30, 30, 30, 30, 30, 30
  };

  for (int i=0; i<countNotes; i++)
  {
    tone(PINOUT_OUT_BUZZER, frequences[i], durations[i] * 2);
    delay(durations[i] * 2);
    noTone(PINOUT_OUT_BUZZER);
  }
  #endif
}
