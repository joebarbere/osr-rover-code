# ROS packages for JPL Open Source Rover Gazebo Simulation

> [!NOTE]
> This package isn't compiled with colcon by default. If you want to use this, remove the [COLCON_IGNORE file](./COLCON_IGNORE)

## Overview
Visualization and Gazebo simulation for the OSR: Gazebo Classic 11 on ROS 2 Humble,
Gazebo Harmonic on ROS 2 Jazzy. `empty_world.launch.py` picks the simulator from
`ROS_DISTRO`.

- `rviz.launch.py`: view the rover URDF in RViz
- `empty_world.launch.py`: spawn the rover in Gazebo and drive it with the **same** kinematics as the hardware stack

### Control architecture

Simulation no longer reimplements rocker-bogie math in C++. Instead:

1. `osr_control/rover` consumes `/cmd_vel` and publishes `/cmd_drive` + `/cmd_corner` using shared `osr_control.kinematics` and dimensions from `osr_bringup/config/osr_params.yaml`
2. `gazebo_command_adapter.py` bridges those commands to the Gazebo `wheel_controller` and `servo_controller`

Changing `d1`–`d4` / `wheel_radius` in `osr_params.yaml` therefore affects hardware and simulation the same way.

## Dependencies

| | ROS 2 Jazzy | ROS 2 Humble |
|---|---|---|
| **Operating system** | Ubuntu 24.04 LTS (Noble) | Ubuntu 22.04 LTS (Jammy) |
| **Gazebo** | Harmonic (`ros_gz_sim`, `gz_ros2_control`) | Classic 11 (`gazebo_ros`, `gazebo_ros2_control`) |

Gazebo Classic isn't available on Jazzy. Both also need `osr_control`,
`osr_interfaces` and `osr_bringup`, built in the same workspace.

## ROS Package Installation

With the workspace in place, rosdep installs the right set for your distro
(`package.xml` lists the Classic packages for Humble and the Harmonic ones for newer
distros):

```bash
rosdep install --from-paths src --ignore-src -y
```

Or by hand. On **Jazzy**:

```bash
sudo apt install ros-jazzy-ros-gz ros-jazzy-gz-ros2-control ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers ros-jazzy-ros2controlcli ros-jazzy-robot-state-publisher \
    ros-jazzy-joint-state-publisher-gui ros-jazzy-xacro
```

On **Humble**:

```bash
sudo apt install python3-colcon-common-extensions
sudo apt-get install ros-humble-rviz2
sudo apt-get install ros-humble-controller-manager
sudo apt-get install ros-humble-robot-state-publisher
sudo apt-get install ros-humble-joint-state-publisher
sudo apt-get install ros-humble-joint-state-publisher-gui
sudo apt-get install ros-humble-gazebo-ros-pkgs
sudo apt-get install ros-humble-trajectory-msgs
sudo apt-get install ros-humble-velocity-controllers
sudo apt-get install ros-humble-joint-trajectory-controller
sudo apt-get install ros-humble-gazebo-ros2-control-demos
```

## Installation

Build from the ROS workspace root (so `osr_control` / `osr_interfaces` / `osr_bringup` are available):

```bash
source /opt/ros/$ROS_DISTRO/setup.bash   # jazzy or humble
cd ~/osr_ws   # workspace that contains this repo's ROS/ packages
# remove COLCON_IGNORE under osr_gazebo first
colcon build --packages-select osr_interfaces osr_control osr_bringup osr_gazebo
source install/setup.bash
```

## Visualisation

```bash
ros2 launch osr_gazebo rviz.launch.py
```

## Simulation

```bash
ros2 launch osr_gazebo empty_world.launch.py
```

Drive with:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

> [!NOTE]
> Rotate-in-place on the hardware stack uses `Twist.angular.y` (joystick pitch). `teleop_twist_keyboard` only commands `angular.z`, so in-place rotation needs a publisher that sets `angular.y` with zero `linear.x`, or the intuitive/joy setup from `osr_bringup`.

## Follow-ups
- Bridge Gazebo `/joint_states` into `/drive_state` and `/corner_state` so `rover` odometry can run in sim

## The method to convert from Onshape to URDF

- The object file for the rover is available within Onshape.
- This object file can be disassembled into its individual components, such as rocker bogie1,2,3, and box, etc..
- However, directly using it as a URDF after converting it to an STL will result in significant CPU and GPU usage in RViz or Gazebo due to the file size issue.
- Therefore, the process of reducing the file size of the STL using MeshLab was carried out.
- The package provided at https://github.com/gstavrinos/calc-inertia was then used to define the inertial properties.
