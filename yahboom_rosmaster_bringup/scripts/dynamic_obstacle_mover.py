#!/usr/bin/env python3
"""
dynamic_obstacle_mover.py
─────────────────────────
Déplace un obstacle dynamique dans Gazebo Harmonic via le service set_pose.

Deux modes disponibles :
  • circle  : trajectoire circulaire continue
  • waypoints : suit une liste de points (interpolation linéaire)

Paramètres ROS2 :
  model_name    (str)   : nom du modèle Gazebo          [dynamic_obstacle]
  world_name    (str)   : nom du world Gazebo            [test_world]
  mode          (str)   : 'circle' ou 'waypoints'        [circle]
  radius        (float) : rayon du cercle (m)            [2.0]
  center_x      (float) : centre X du cercle             [0.0]
  center_y      (float) : centre Y du cercle             [0.0]
  height        (float) : hauteur Z fixe (m)             [0.2]
  speed         (float) : vitesse angulaire (rad/s)      [0.5]
  linear_speed  (float) : vitesse linéaire waypoints m/s [0.5]
  update_rate   (float) : fréquence de mise à jour (Hz)  [50.0]
  waypoints     (str)   : JSON list [[x,y],[x,y],...]    ['[]']
  loop          (bool)  : boucler les waypoints          [true]

Usage :
  ros2 run yahboom_rosmaster_bringup dynamic_obstacle_mover.py \
    --ros-args -p mode:=circle -p radius:=2.0 -p speed:=0.4

  ros2 run yahboom_rosmaster_bringup dynamic_obstacle_mover.py \
    --ros-args -p mode:=waypoints \
      -p "waypoints:=[[2,0],[2,2],[0,2],[-2,2],[-2,0],[-2,-2],[0,-2],[2,-2]]" \
      -p linear_speed:=0.6 \
      -p loop:=true
"""

import rclpy
from rclpy.node import Node
import math
import json

# Import Gazebo Transport (gz-python)
try:
    from gz.msgs10.pose_pb2 import Pose
    from gz.msgs10.boolean_pb2 import Boolean
    from gz.transport13 import Node as GzNode
    GZ_AVAILABLE = True
except ImportError:
    GZ_AVAILABLE = False


class DynamicObstacleMover(Node):

    def __init__(self):
        super().__init__("dynamic_obstacle_mover")

        # ── Déclaration des paramètres ──────────────────────────────────────
        self.declare_parameter("model_name",   "dynamic_obstacle")
        self.declare_parameter("world_name",   "test_world")
        self.declare_parameter("mode",         "circle")       # circle | waypoints
        self.declare_parameter("radius",       2.0)
        self.declare_parameter("center_x",     0.0)
        self.declare_parameter("center_y",     0.0)
        self.declare_parameter("height",       0.2)
        self.declare_parameter("speed",        0.5)            # rad/s (circle)
        self.declare_parameter("linear_speed", 0.5)            # m/s   (waypoints)
        self.declare_parameter("update_rate",  50.0)
        self.declare_parameter("waypoints",    "[]")           # JSON string
        self.declare_parameter("loop",         True)

        # ── Lecture des paramètres ──────────────────────────────────────────
        self.model_name   = self.get_parameter("model_name").value
        self.world_name   = self.get_parameter("world_name").value
        self.mode         = self.get_parameter("mode").value
        self.radius       = self.get_parameter("radius").value
        self.cx           = self.get_parameter("center_x").value
        self.cy           = self.get_parameter("center_y").value
        self.height       = self.get_parameter("height").value
        self.speed        = self.get_parameter("speed").value
        self.linear_speed = self.get_parameter("linear_speed").value
        update_rate       = self.get_parameter("update_rate").value
        self.loop         = self.get_parameter("loop").value

        self.dt = 1.0 / update_rate

        # ── Waypoints ───────────────────────────────────────────────────────
        raw_wp = self.get_parameter("waypoints").value
        try:
            self.waypoints = json.loads(raw_wp)
        except json.JSONDecodeError:
            self.get_logger().error(f"JSON waypoints invalide : {raw_wp}")
            self.waypoints = []

        # ── État interne ────────────────────────────────────────────────────
        self.angle       = 0.0        # pour mode circle
        self.wp_index    = 0          # index waypoint courant
        self.wp_progress = 0.0        # progression [0..1] entre deux waypoints
        self.done        = False      # fin de trajectoire (loop=false)

        # ── Gazebo Transport ────────────────────────────────────────────────
        if not GZ_AVAILABLE:
            self.get_logger().error(
                "gz-python non disponible ! "
                "Installe : pip install gz-python --break-system-packages"
            )
            return

        self.gz_node      = GzNode()
        self.service_name = f"/world/{self.world_name}/set_pose"

        # Vérification du mode
        if self.mode == "waypoints" and len(self.waypoints) < 2:
            self.get_logger().warn(
                "Mode waypoints : il faut au moins 2 points. "
                "Basculement en mode circle."
            )
            self.mode = "circle"

        self.get_logger().info(
            f"[DynamicObstacleMover] modèle='{self.model_name}' "
            f"world='{self.world_name}' mode='{self.mode}'"
        )

        if self.mode == "circle":
            self.get_logger().info(
                f"  Cercle : centre=({self.cx},{self.cy}) "
                f"r={self.radius}m vitesse={self.speed} rad/s"
            )
        else:
            self.get_logger().info(
                f"  Waypoints ({len(self.waypoints)} pts) "
                f"vitesse={self.linear_speed} m/s loop={self.loop}"
            )
            for i, wp in enumerate(self.waypoints):
                self.get_logger().info(f"    [{i}] x={wp[0]:.2f} y={wp[1]:.2f}")

        # ── Timer principal ─────────────────────────────────────────────────
        self.timer = self.create_timer(self.dt, self._update)

    # ────────────────────────────────────────────────────────────────────────
    # Callback principal
    # ────────────────────────────────────────────────────────────────────────
    def _update(self):
        if self.done:
            return

        if self.mode == "circle":
            x, y, yaw = self._compute_circle()
        else:
            result = self._compute_waypoints()
            if result is None:
                return
            x, y, yaw = result

        self._set_pose(x, y, self.height, yaw)

    # ────────────────────────────────────────────────────────────────────────
    # Mode circle
    # ────────────────────────────────────────────────────────────────────────
    def _compute_circle(self):
        self.angle += self.speed * self.dt
        if self.angle > 2 * math.pi:
            self.angle -= 2 * math.pi

        x   = self.cx + self.radius * math.cos(self.angle)
        y   = self.cy + self.radius * math.sin(self.angle)
        yaw = self.angle + math.pi / 2   # face à la direction du mouvement
        return x, y, yaw

    # ────────────────────────────────────────────────────────────────────────
    # Mode waypoints
    # ────────────────────────────────────────────────────────────────────────
    def _compute_waypoints(self):
        if self.wp_index >= len(self.waypoints) - 1:
            if self.loop:
                self.wp_index    = 0
                self.wp_progress = 0.0
            else:
                self.get_logger().info("Trajectoire terminée.", once=True)
                self.done = True
                return None

        # Points courant et suivant
        p0 = self.waypoints[self.wp_index]
        p1 = self.waypoints[self.wp_index + 1]

        dx   = p1[0] - p0[0]
        dy   = p1[1] - p0[1]
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 1e-6:
            self.wp_index    += 1
            self.wp_progress  = 0.0
            return self._compute_waypoints()

        # Avancement
        step              = (self.linear_speed * self.dt) / dist
        self.wp_progress += step

        if self.wp_progress >= 1.0:
            self.wp_progress = 0.0
            self.wp_index   += 1
            # Récursion pour cas limite
            return self._compute_waypoints()

        x   = p0[0] + self.wp_progress * dx
        y   = p0[1] + self.wp_progress * dy
        yaw = math.atan2(dy, dx)
        return x, y, yaw

    # ────────────────────────────────────────────────────────────────────────
    # Envoi de la pose à Gazebo via service set_pose
    # ────────────────────────────────────────────────────────────────────────
    def _set_pose(self, x: float, y: float, z: float, yaw: float):
        pose_msg      = Pose()
        pose_msg.name = self.model_name

        pose_msg.position.x = x
        pose_msg.position.y = y
        pose_msg.position.z = z

        # Quaternion depuis yaw (roll=pitch=0)
        pose_msg.orientation.x = 0.0
        pose_msg.orientation.y = 0.0
        pose_msg.orientation.z = math.sin(yaw / 2.0)
        pose_msg.orientation.w = math.cos(yaw / 2.0)

        result, success = self.gz_node.request(
            self.service_name,
            pose_msg,
            Pose,
            Boolean,
            timeout=100
        )

        if not success:
            self.get_logger().warn(
                f"set_pose échoué pour '{self.model_name}'",
                throttle_duration_sec=5.0
            )


# ────────────────────────────────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)
    node = DynamicObstacleMover()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()