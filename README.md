# yahboom_rosmaster_R2L

Projet ROS 2 pour le robot **Yahboom ROSMASTER R2L** — simulation Gazebo, navigation, localisation et contrôle mecanum.

---

## Table des matières

- [Prérequis](#prérequis)
- [Installation de ROS 2 Jazzy](#installation-de-ros-2-jazzy)
- [Installation de Gazebo Harmonic](#installation-de-gazebo-harmonic)
- [Installation de RViz2](#installation-de-rviz2)
- [Cloner et compiler le projet](#cloner-et-compiler-le-projet)
- [Lancer la simulation](#lancer-la-simulation)
- [Structure du projet](#structure-du-projet)

---

## Prérequis

- **OS** : Ubuntu 24.04 LTS (Noble Numbat)
- **ROS 2** : Jazzy Jalisco
- **Simulateur** : Gazebo Harmonic
- **Git** installé

---

## Installation de ROS 2 Jazzy

### 1. Configurer la locale

```bash
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 2. Ajouter les dépôts ROS 2

```bash
sudo apt install -y curl gnupg2 lsb-release software-properties-common

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
```

### 3. Installer ROS 2 Jazzy

```bash
sudo apt install -y ros-jazzy-desktop
sudo apt install -y ros-dev-tools python3-colcon-common-extensions python3-rosdep
```

### 4. Initialiser rosdep

```bash
sudo rosdep init
rosdep update
```

### 5. Sourcer ROS 2

```bash
# Pour la session courante
source /opt/ros/jazzy/setup.bash

# Pour toutes les sessions (permanent)
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 6. Vérifier l'installation

```bash
ros2 --version
```

---

## Installation de Gazebo Harmonic

### 1. Ajouter le dépôt Gazebo

```bash
sudo curl -sSL https://packages.osrfoundation.org/gazebo.gpg \
  -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] \
  http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

sudo apt update
```

### 2. Installer Gazebo Harmonic

```bash
sudo apt install -y gz-harmonic
```

### 3. Installer le bridge ROS 2 ↔ Gazebo

```bash
sudo apt install -y ros-jazzy-ros-gz
```

### 4. Vérifier l'installation

```bash
gz sim --version
```

---

## Installation de RViz2

RViz2 est inclus dans `ros-jazzy-desktop`. Si besoin, l'installer séparément :

```bash
sudo apt install -y ros-jazzy-rviz2
```

### Vérifier

```bash
ros2 pkg list | grep rviz2
```

---

## Cloner et compiler le projet

### 1. Créer le workspace

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
```

### 2. Cloner le dépôt

```bash
git clone https://github.com/Eyasaafi/yahboom_rosmaster_R2L.git
# ou
git clone https://github.com/DorsafZayet/yahboom_rosmaster_R2L.git
```

### 3. Installer les dépendances

```bash
cd ~/ros2_ws

rosdep install --from-paths src --ignore-src -r -y
```

Dépendances supplémentaires recommandées :

```bash
sudo apt install -y \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-nav2-bringup \
  ros-jazzy-robot-localization \
  ros-jazzy-slam-toolbox \
  ros-jazzy-twist-mux
```

### 4. Compiler le workspace

```bash
cd ~/ros2_ws
colcon build --symlink-install
```

### 5. Sourcer le workspace

```bash
# Pour la session courante
source ~/ros2_ws/install/setup.bash

# Pour toutes les sessions (permanent)
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## Lancer la simulation

### Ouvrir Gazebo (monde vide)

```bash
gz sim
```

### Ouvrir RViz2 (vide)

```bash
rviz2
```

### Lancer le robot dans Gazebo

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch yahboom_rosmaster_bringup bringup.launch.py
```

### Lancer uniquement la description URDF

```bash
ros2 launch yahboom_rosmaster_description display.launch.py
```

### Lancer la simulation Gazebo complète

```bash
ros2 launch yahboom_rosmaster_gazebo gazebo.launch.py
```

---

## Structure du projet

```
yahboom_rosmaster_R2L/
├── mecanum_drive_controller/        # Contrôleur roues mecanum
├── yahboom_rosmaster/               # Package principal
├── yahboom_rosmaster_bringup/       # Launch files de démarrage
├── yahboom_rosmaster_description/   # URDF / modèle du robot
├── yahboom_rosmaster_docking/       # Docking autonome
├── yahboom_rosmaster_gazebo/        # Simulation Gazebo
├── yahboom_rosmaster_localization/  # Localisation (EKF)
├── yahboom_rosmaster_msgs/          # Messages et services custom
├── yahboom_rosmaster_navigation/    # Navigation autonome (Nav2)
└── yahboom_rosmaster_system_tests/  # Tests système
```

---
<img width="1920" height="1080" alt="envi(1)" src="https://github.com/user-attachments/assets/5452c3ca-8a74-4c64-9824-c4ad1d5b542a" />
<img width="1920" height="1080" alt="robotrvizzzz" src="https://github.com/user-attachments/assets/c7748857-2a42-4735-a8bb-9cf1f3f60152" />


## Auteurs

- **Eya Saafi** — [@Eyasaafi](https://github.com/Eyasaafi)
- **Dorsaf Zayet** — [@DorsafZayet](https://github.com/DorsafZayet)
