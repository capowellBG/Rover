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


## Notes
```bash
git config user.name "Caleb Powell"
git config user.email "capowell@brasfieldgorrie.com"
```