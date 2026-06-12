# launch/ultrasonic_bridge.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

SENSORS = ["us_front_left", "us_front_right", "us_rear_left", "us_rear_right"]

def generate_launch_description():
    bridges = []
    for name in SENSORS:
        bridges.append(Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            name=f"bridge_{name}",
            arguments=[
                f"/ultrasonic/{name}@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan"
            ],
            output="screen",
        ))
    return LaunchDescription(bridges)