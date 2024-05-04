# CAN interface
echo "waiting for CAN interface..."
while true
do
  if [ ! -z "$(ifconfig -a | grep 'can0')"  ]; then
    break
  else
    sleep 1
  fi
done

echo "configuring CAN interface..."
sudo ifconfig can0 down 
sleep 1
sudo ip link set can0 type can termination 120 bitrate 500000
sudo ifconfig can0 up
sudo ip -details link show can0
sleep 1
