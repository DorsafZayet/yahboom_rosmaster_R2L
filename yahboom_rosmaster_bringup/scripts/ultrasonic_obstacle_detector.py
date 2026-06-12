#!/usr/bin/env python3
# ultrasonic_obstacle_detector.py

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Range
from std_msgs.msg import Bool
import math

SENSORS = ["us_front_left", "us_front_right", "us_rear_left", "us_rear_right"]

class UltrasonicDetector(Node):
    def __init__(self):
        super().__init__("ultrasonic_obstacle_detector")

        # Paramètres
        self.declare_parameter("alert_distance", 0.30)   # 30 cm → alerte
        self.declare_parameter("stop_distance",  0.15)   # 15 cm → arrêt

        self.alert_dist = self.get_parameter("alert_distance").value
        self.stop_dist  = self.get_parameter("stop_distance").value

        self.latest = {name: None for name in SENSORS}

        # Subscribers LaserScan brut (depuis gz bridge)
        for name in SENSORS:
            self.create_subscription(
                LaserScan,
                f"/ultrasonic/{name}",
                lambda msg, n=name: self._laser_cb(msg, n),
                10
            )

        # Publishers Range propres (un par capteur)
        self.range_pubs = {
            name: self.create_publisher(Range, f"/range/{name}", 10)
            for name in SENSORS
        }

        # Publisher alerte globale
        self.alert_pub = self.create_publisher(Bool, "/obstacle_detected", 10)
        self.stop_pub  = self.create_publisher(Bool, "/obstacle_stop",     10)

        # Timer 20 Hz
        self.create_timer(0.05, self._publish_loop)
        self.get_logger().info("Ultrasonic obstacle detector started.")

    def _laser_cb(self, msg: LaserScan, sensor_name: str):
        """Convertit LaserScan → distance minimale (proxy sonar)."""
        valid = [r for r in msg.ranges
                 if msg.range_min < r < msg.range_max and not math.isnan(r)]
        self.latest[sensor_name] = min(valid) if valid else msg.range_max

        # Publie aussi un Range propre
        range_msg = Range()
        range_msg.header = msg.header
        range_msg.header.frame_id = f"{sensor_name}_link"
        range_msg.radiation_type = Range.ULTRASOUND
        range_msg.field_of_view   = 0.2618   # 15°
        range_msg.min_range = msg.range_min
        range_msg.max_range = msg.range_max
        range_msg.range = self.latest[sensor_name]
        self.range_pubs[sensor_name].publish(range_msg)

    def _publish_loop(self):
        distances = [d for d in self.latest.values() if d is not None]
        if not distances:
            return

        min_dist = min(distances)

        alert = Bool(data=min_dist < self.alert_dist)
        stop  = Bool(data=min_dist < self.stop_dist)
        self.alert_pub.publish(alert)
        self.stop_pub.publish(stop)

        if stop.data:
            self.get_logger().warn(
                f"STOP ! Obstacle à {min_dist:.2f} m", throttle_duration_sec=1.0)
        elif alert.data:
            self.get_logger().info(
                f"Obstacle proche : {min_dist:.2f} m", throttle_duration_sec=2.0)


def main(args=None):
    rclpy.init(args=args)
    node = UltrasonicDetector()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()