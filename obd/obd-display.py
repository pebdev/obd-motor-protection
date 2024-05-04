# -*- coding: utf-8 -*-
########################################################################################################################
# Project : OBD Display
# Author  : PEB <pebdev@lavache.com>
# Date    : 24.01.2024
########################################################################################################################
# Copyright (C) 2024
# This file is copyright under the latest version of the EUPL.
# Please see LICENSE file for your rights under this license.
########################################################################################################################

# I M P O R T ##########################################################################################################
import argparse
import matplotlib.pyplot as plt


# D E C L A R A T I O N S ##############################################################################################
KEY_engine_speed    = "0C"
KEY_injection_time  = "12"


#---------------------------------------------------------------------------------------------------------------------
# @brief [PRIVATE] Read data from the file.
# @param file : file to open.
# @return data extracted from the file.
#---------------------------------------------------------------------------------------------------------------------
def read_file (file):
  retval = []

  with open(file, 'r') as f:
    for line in f:
      frameData = line.split(' ')

      if (len(frameData) > 2):

        messageData = frameData[2].split('#')
        if (len(messageData) > 1):

          pid  = messageData[0]
          data = messageData[1]

          if(pid == "7E8"):
            retval.append(data)

  return retval


#---------------------------------------------------------------------------------------------------------------------
# @brief [PRIVATE] Parse data extracted form the file.
# @param data_list    : list of data.
# @param start_offset : offset of the first data.
# @return parsed data.
#---------------------------------------------------------------------------------------------------------------------
def data_parser (data_list, start_offset):
  retval = {}
  excludeList = ["44"]

  for idx,data in enumerate(data_list):
    size      = int(data[:2])
    rawKey    = data[4:6]
    rawValue  = data[6:(size+1)*2]
    value     = None

    if (rawKey in excludeList):
      continue

    if (not rawKey in retval):
      print("Added new PID "+str(rawKey))
      retval[rawKey] = {}
      retval[rawKey]['x'] = []
      retval[rawKey]['y'] = []

    try:
      if (rawKey == "04"):
        value = 1/2.55	 * int(rawValue,16)

      elif (rawKey == "06"):
        value = 1/1.28 * int(rawValue,16) - 100

      elif (rawKey == "0B"):
        value = int(rawValue,16)

      elif (rawKey == "0E"):
        value = -64 + 0.5 * int(rawValue,16)

      elif (rawKey == KEY_engine_speed):
        value = (int(rawValue,16)*0.25)/1000
      
      elif (rawKey == KEY_injection_time):
        value = int(rawValue[2:],16)/2500
        
      else:
        value = int(rawValue,16)
      
      #print ("-----------------------")
      #print ("frame: "+str(data))
      #print ("size : "+str(size))
      #print ("raw  : "+str(rawValue))
      #print ("value: "+str(value))

    except:
      print ("Invalid value (frame:"+str(data))
      return retval

    if (idx >= start_offset):
      retval[rawKey]['x'].append(idx)
      retval[rawKey]['y'].append(value)

  return retval


#---------------------------------------------------------------------------------------------------------------------
# @brief [PRIVATE] Draw curve.
# @param dataDict : data to draw.
# @return number of data
#---------------------------------------------------------------------------------------------------------------------
def draw_curve (dataDict):

  plt.figure(figsize=(15, 6))
  plt.xlabel('index')
  plt.ylabel('value')
  
  for key in reversed(dataDict):
    labelName = ""

    if (key == KEY_engine_speed):
      plt.title('Engine speed (RPM)/1000')
      labelName = "engine speed (RPM/1000)"

    elif (key == KEY_injection_time):
      plt.title('Injection time (ms)')
      labelName = "injection time (ms)"

    else:
      plt.title('Curve '+key)
    
    print ("KEY:"+key)
    plt.plot(dataDict[key]['x'], dataDict[key]['y'], label=labelName)

  return dataDict[key]['x'][-1]


#---------------------------------------------------------------------------------------------------------------------
# @brief [PRIVATE] Draw curve.
# @param dataDict : data to draw.
# @return number of data
#---------------------------------------------------------------------------------------------------------------------
def draw_metrics (dataDict):
  key_m1                = 'metric-fs'
  dataDict[key_m1]      = {}
  dataDict[key_m1]['x'] = []
  dataDict[key_m1]['y'] = []

  print("A="+str(len(dataDict[KEY_injection_time]['y']))+" B="+str(len(dataDict[KEY_engine_speed]['y'])))

  for idx,val in enumerate(dataDict[KEY_injection_time]['x']):

    if (idx < len(dataDict[KEY_engine_speed]['y'])):
      dataDict[key_m1]['x'].append(val)
      dataDict[key_m1]['y'].append((dataDict[KEY_engine_speed]['y'][idx]*pow(dataDict[KEY_injection_time]['y'][idx],dataDict[KEY_injection_time]['y'][idx])))

  plt.plot(dataDict[key_m1]['x'], dataDict[key_m1]['y'], label="key_m1")
  plt.hlines(2.5, 0, dataDict[KEY_injection_time]['x'][-1], color='r', linestyle='--', label='critical threshold')
  plt.hlines(13.0, 0, dataDict[KEY_injection_time]['x'][-1], color='r', linestyle='--', label='critical threshold')


#---------------------------------------------------------------------------------------------------------------------
# @brief [PRIVATE] Main function.
#---------------------------------------------------------------------------------------------------------------------
def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--file', help='name of the file')
  parser.add_argument('-s', '--offstart', help='offset of the first data', default=0)
  args = parser.parse_args()

  # read and draw
  data_file = read_file(args.file)
  data_parsed = data_parser(data_file, args.offstart)
  size = draw_curve(data_parsed)
  draw_metrics (data_parsed)

  plt.legend()
  plt.show()



#---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
