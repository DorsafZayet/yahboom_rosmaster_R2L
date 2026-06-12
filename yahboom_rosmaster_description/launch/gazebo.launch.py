import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_description = get_package_share_directory('yahboom_rosmaster_description')
    xacro_file = os.path.join(pkg_description, 'urdf', 'robots', 'rosmaster_x3.urdf.xacro')

    # On force l'argument use_gazebo à True
    robot_description_raw = xacro.process_file(
        xacro_file, 
        mappings={'use_gazebo': 'true'}
    ).toxml()

    # 1. Lancer Gazebo Sim (Nouveau Gazebo)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )

    # 2. Robot State Publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_raw,
            'use_sim_time': True
        }]
    )

    # 3. Faire apparaître le robot (Spawn) dans Gazebo Sim
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'rosmaster_x3', '-allow_renaming', 'true'],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        node_robot_state_publisher,
        spawn_entity
    ])