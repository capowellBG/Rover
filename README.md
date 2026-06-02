# Rover Setup

## Host Setup (run once on the Pi)

Install Docker following the official guide:
https://docs.docker.com/engine/install/

Add your user to the docker group so you can run Docker without sudo:
```bash
sudo usermod -aG docker $USER
```

Install utilities needed for group changes to take effect:
```bash
sudo apt install util-linux-extra
```

Apply the new group membership in the current shell:
```bash
newgrp docker
```

Enable the pigpio daemon so it starts automatically on boot (required for GPIO/motor control):
```bash
sudo systemctl enable pigpiod
```

## Running the Container

Build the Docker image:
```bash
docker build -t rover .
```

Start the container:
```bash
docker compose up
```

## Wi-Fi

```bash
sudo nmcli con add type wifi ifname wlan0 con-name "Rover-Hotspot" autoconnect no ssid "Rover"
sudo nmcli con modify "Rover-Hotspot" 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
sudo nmcli con modify "Rover-Hotspot" wifi-sec.key-mgmt wpa-psk wifi-sec.psk 'B&GSP!R!T'
sudo nmcli con modify "Rover-Hotspot" ipv4.addresses 10.42.0.1/24
```

```bash
sudo nmcli con up Rover-Hotspot
```

```bash
sudo nmcli con up BG
```

```bash
ssh brasfield@10.42.0.1
```


## Notes
```bash
git config user.name "Caleb Powell"
git config user.email "capowell@brasfieldgorrie.com"
```

```bash
git config user.name "Gabriel McMillan"
git config user.email "gabezmcmillan@gmail.com"
```

https://abyz.me.uk/rpi/pigpio/download.html