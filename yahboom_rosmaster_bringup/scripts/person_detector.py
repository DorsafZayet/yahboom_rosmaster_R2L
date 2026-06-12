#!/usr/bin/env python3
"""
Détecteur de personne combinant les données ultrason
Pour suivre la personne dynamique
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, PoseStamped
from visualization_msgs.msg import Marker
from sensor_msgs.msg import LaserScan
import math
import numpy as np

class PersonDetector(Node):
    def __init__(self):
        super().__init__('person_detector')
        
        # Paramètres
        self.PERSON_RADIUS = 0.3
        self.DETECTION_ANGLE = 0.5  # radians (environ 30°)
        
        # Données des capteurs
        self.ultrasonic_data = {
            'front_left': 4.0,
            'front_right': 4.0,
            'rear_left': 4.0,
            'rear_right': 4.0
        }
        
        # Position de la personne détectée
        self.person_detected = False
        self.person_x = 0.0
        self.person_y = 0.0
        
        # Publishers
        self.person_marker_pub = self.create_publisher(Marker, '/person_detector/marker', 10)
        self.person_pose_pub = self.create_publisher(PoseStamped, '/person_detector/pose', 10)
        
        # Subscribers pour les capteurs ultrason
        self.create_subscription(Float32MultiArray, '/ultrasonic/distances', self.ultrasonic_callback, 10)
        
        # Subscriber pour la personne dynamique (simulation)
        self.create_subscription(Pose, '/dynamic_person/pose', self.ground_truth_callback, 10)
        
        self.get_logger().info("Person Detector started")
    
    def ultrasonic_callback(self, msg):
        """Traite les données ultrason pour détecter une personne"""
        if len(msg.data) >= 4:
            self.ultrasonic_data['front_left'] = msg.data[0]
            self.ultrasonic_data['front_right'] = msg.data[1]
            self.ultrasonic_data['rear_left'] = msg.data[2]
            self.ultrasonic_data['rear_right'] = msg.data[3]
            
            # Détection simple : obstacle proche devant = personne
            front_min = min(self.ultrasonic_data['front_left'], self.ultrasonic_data['front_right'])
            
            if front_min < 1.0:
                self.person_detected = True
                # Estimation de la position (simplifiée)
                self.person_x = front_min * math.cos(0)
                self.person_y = 0
            else:
                self.person_detected = False
    
    def ground_truth_callback(self, msg):
        """Reçoit la position réelle de la personne (pour validation)"""
        # Publier la position réelle pour comparaison
        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "person_ground_truth"
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose = msg
        marker.pose.position.z = 0.5
        marker.scale.x = 0.3
        marker.scale.y = 0.3
        marker.scale.z = 0.3
        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 0.0
        marker.color.a = 0.5
        self.person_marker_pub.publish(marker)

def main(args=None):
    rclpy.init(args=args)
    node = PersonDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()