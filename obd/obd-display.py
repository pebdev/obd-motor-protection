
import argparse
import matplotlib.pyplot as plt

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
# @param data_list : list of data.
# @return parsed data.
#---------------------------------------------------------------------------------------------------------------------
def data_parser (data_list):
  retval = {}
  excludeList = ["44"]

  for data in data_list:
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
        value = int(rawValue,16)*0.25
      
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

    if (len(retval[rawKey]['x']) > 0):
      retval[rawKey]['x'].append(retval[rawKey]['x'][-1]+1)
    else:
      retval[rawKey]['x'].append(1)

    retval[rawKey]['y'].append(value)

  return retval


#---------------------------------------------------------------------------------------------------------------------
# @brief [PRIVATE] Draw curve.
# @param dataDict : data to draw.
#---------------------------------------------------------------------------------------------------------------------
def draw_curve (dataDict):
  
  for key in dataDict:
    
    plt.figure(figsize=(15, 6))
    plt.xlabel('index')
    plt.ylabel('value')

    if (key == KEY_engine_speed):
      plt.title('Engine speed (RPM)')
    elif (key == KEY_injection_time):
      plt.title('Injection time (ms)')
    else:
      plt.title('Curve '+key)
    
    print ("KEY:"+key)
    plt.plot(dataDict[key]['x'], dataDict[key]['y'], label="PID-"+str(key))

  plt.legend()
  plt.show()


#---------------------------------------------------------------------------------------------------------------------
# @brief [PRIVATE] Main function.
#---------------------------------------------------------------------------------------------------------------------
def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('file', help='name of the file')
  args = parser.parse_args()

  # read and draw
  data_file = read_file(args.file)
  data_parsed = data_parser(data_file)
  draw_curve(data_parsed)


#---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
