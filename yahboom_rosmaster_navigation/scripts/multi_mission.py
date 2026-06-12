#!/usr/bin/env python3
import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
import time  # Pour les pauses


def main():
    rclpy.init()
    nav = BasicNavigator()

    # Attends Nav2 prêt
    nav.waitUntilNav2Active()
    

    # Liste de goals (ex. jaune puis rouge) - adapte x/y/orientation
    goals = []

    # Goal jaune (ex. pose estimée de l'image)
    jaune = PoseStamped()
    jaune.header.frame_id = 'map'
    jaune.header.stamp = nav.get_clock().now().to_msg()
    jaune.pose.position.x = 0.0  # Adapte selon carte RViz
    jaune.pose.position.y = 2.0
    jaune.pose.orientation.w = 1.0  # Orientation 0°
    goals.append(jaune)

    # Goal rouge
    rouge = PoseStamped()
    rouge.header.frame_id = 'map'
    rouge.header.stamp = nav.get_clock().now().to_msg()
    rouge.pose.position.x = 3.0
    rouge.pose.position.y = 1.0
    rouge.pose.orientation.w = 1.0
    goals.append(rouge)

    # Envoie la séquence
    print("Démarre missions séquentielles...")
    for goal in goals:
        nav.goToPose(goal)
        while not nav.isTaskComplete():
            feedback = nav.getFeedback()
            if feedback:
                print(f"Distance restante: {feedback.distance_remaining:.2f} m")
        result = nav.getResult()
        if result == TaskResult.SUCCEEDED:
            print("Goal atteint ! Pause 5s...")
            time.sleep(5)  # ← Pause ici (5 secondes)
        else:
            print("Échec – annule")
            break

    rclpy.shutdown()

if __name__ == '__main__':
    main()