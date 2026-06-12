#include <chrono>
#include <functional>
#include <memory>
#include <vector>
#include <algorithm>
#include <cmath>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "tf2/utils.h" // Pour transformer l'angle du robot

using namespace std::chrono_literals;

class ObstacleAvoidanceController : public rclcpp::Node {
public:
    ObstacleAvoidanceController() : Node("obstacle_avoidance_controller") {
        publisher_ = this->create_publisher<geometry_msgs::msg::TwistStamped>("/mecanum_drive_controller/cmd_vel", 10);
        
        subscription_scan_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
            "/scan", 10, std::bind(&ObstacleAvoidanceController::scan_callback, this, std::placeholders::_1));
        
        subscription_odom_ = this->create_subscription<nav_msgs::msg::Odometry>(
            "/odom", 10, std::bind(&ObstacleAvoidanceController::odom_callback, this, std::placeholders::_1));

        timer_ = this->create_wall_timer(100ms, std::bind(&ObstacleAvoidanceController::control_loop, this));

        // Cible (Point Rouge)
        goal_x_ = 4.0;
        goal_y_ = 3.5;
        
        // Paramètres
        robot_speed_ = 0.5;
        turn_speed_ = 0.6;
        dist_threshold_ = 0.3;
        angle_threshold_ = 0.15; // Précision de l'angle
    }

private:
    void odom_callback(const nav_msgs::msg::Odometry::SharedPtr msg) {
        current_x_ = msg->pose.pose.position.x;
        current_y_ = msg->pose.pose.position.y;

        // Convertir l'orientation (Quaternion -> Yaw)
        tf2::Quaternion q(
            msg->pose.pose.orientation.x,
            msg->pose.pose.orientation.y,
            msg->pose.pose.orientation.z,
            msg->pose.pose.orientation.w);
        tf2::Matrix3x3 m(q);
        double roll, pitch;
        m.getRPY(roll, pitch, current_yaw_);
    }

    void scan_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg) {
        auto min_it = std::min_element(msg->ranges.begin() + 300, msg->ranges.begin() + 420);
        obstacle_detected_ = (*min_it < 0.8);
    }

    void control_loop() {
        auto drive_msg = geometry_msgs::msg::TwistStamped();
        drive_msg.header.stamp = this->now();
        drive_msg.header.frame_id = "base_link";

        // 1. Calculer la distance et l'angle vers la cible
        double dx = goal_x_ - current_x_;
        double dy = goal_y_ - current_y_;
        double dist = std::sqrt(dx*dx + dy*dy);
        double angle_to_goal = std::atan2(dy, dx);
        double angle_diff = angle_to_goal - current_yaw_;

        // Normaliser l'angle entre -PI et PI
        while (angle_diff > M_PI) angle_diff -= 2 * M_PI;
        while (angle_diff < -M_PI) angle_diff += 2 * M_PI;

        if (dist < dist_threshold_) {
            RCLCPP_INFO(this->get_logger(), "Arrivé au point rouge !");
            stop_robot(drive_msg);
        } 
        else if (obstacle_detected_) {
            RCLCPP_WARN(this->get_logger(), "Obstacle ! Pivotement...");
            drive_msg.twist.angular.z = turn_speed_;
        }
        else if (std::abs(angle_diff) > angle_threshold_) {
            // S'orienter vers la cible (chemin le plus court)
            drive_msg.twist.angular.z = (angle_diff > 0) ? turn_speed_ : -turn_speed_;
        }
        else {
            // Foncer vers la cible
            drive_msg.twist.linear.x = robot_speed_;
        }
        publisher_->publish(drive_msg);
    }

    void stop_robot(geometry_msgs::msg::TwistStamped &msg) {
        msg.twist.linear.x = 0.0;
        msg.twist.angular.z = 0.0;
    }

    rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr publisher_;
    rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr subscription_scan_;
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr subscription_odom_;
    rclcpp::TimerBase::SharedPtr timer_;
    bool obstacle_detected_ = false;
    double current_x_, current_y_, current_yaw_;
    double goal_x_, goal_y_, robot_speed_, turn_speed_, dist_threshold_, angle_threshold_;
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ObstacleAvoidanceController>());
    rclcpp::shutdown();
    return 0;
}