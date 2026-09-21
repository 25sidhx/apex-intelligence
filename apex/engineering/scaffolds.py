"""
Engineering Scaffolding Engine: Generates production-ready embedded firmware and ROS 2 templates.
Inspired by ECC & Embedded Harness standards.
"""

from pathlib import Path
from typing import Dict


TEMPLATES: Dict[str, Dict[str, str]] = {
    "esp32_p4_vision": {
        "CMakeLists.txt": """cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(esp32_p4_vision_node)
""",
        "main/main.c": """#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_camera.h"

static const char *TAG = "P4_VISION";

void app_main(void)
{
    ESP_LOGI(TAG, "Initializing ESP32-P4 Vision Pipeline @ 400MHz...");
    // Hardware accelerated MIPI-CSI & H.264 encode init
    while (1) {
        ESP_LOGD(TAG, "Frame captured -> Inference dispatching to ESP-DL");
        vTaskDelay(pdMS_TO_TICKS(33)); // ~30 FPS
    }
}
""",
    },
    "ros2_px4_offboard": {
        "package.xml": """<?xml version="1.0"?>
<package format="3">
  <name>px4_offboard_controller</name>
  <version>1.0.0</version>
  <description>PX4 Autonomous Offboard Control Node in ROS 2</description>
  <maintainer email="25sidhx@users.noreply.github.com">Siddhant Rahate</maintainer>
  <license>BSD-3-Clause</license>
  <buildtool_depend>ament_cmake</buildtool_depend>
  <depend>rclcpp</depend>
  <depend>px4_msgs</depend>
  <depend>geometry_msgs</depend>
</package>
""",
        "src/offboard_node.cpp": """#include <rclcpp/rclcpp.hpp>
#include <px4_msgs/msg/offboard_control_mode.hpp>
#include <px4_msgs/msg/trajectory_setpoint.hpp>
#include <px4_msgs/msg/vehicle_command.hpp>

using namespace std::chrono_literals;

class OffboardController : public rclcpp::Node {
public:
    OffboardController() : Node("px4_offboard_node") {
        offboard_control_mode_pub_ = this->create_publisher<px4_msgs::msg::OffboardControlMode>(
            "/fmu/in/offboard_control_mode", 10);
        trajectory_setpoint_pub_ = this->create_publisher<px4_msgs::msg::TrajectorySetpoint>(
            "/fmu/in/trajectory_setpoint", 10);
        timer_ = this->create_wall_timer(100ms, std::bind(&OffboardController::timer_callback, this));
        RCLCPP_INFO(this->get_logger(), "PX4 Offboard Node Initialized.");
    }

private:
    void timer_callback() {
        px4_msgs::msg::OffboardControlMode mode{};
        mode.position = true;
        mode.velocity = false;
        mode.acceleration = false;
        mode.timestamp = this->get_clock()->now().nanoseconds() / 1000;
        offboard_control_mode_pub_->publish(mode);
    }

    rclcpp::Publisher<px4_msgs::msg::OffboardControlMode>::SharedPtr offboard_control_mode_pub_;
    rclcpp::Publisher<px4_msgs::msg::TrajectorySetpoint>::SharedPtr trajectory_setpoint_pub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<OffboardController>());
    rclcpp::shutdown();
    return 0;
}
""",
    },
    "simplefoc_bldc": {
        "platformio.ini": """[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
lib_deps =
    askuric/Simple FOC @ ^2.3.2
    SPI
    Wire
""",
        "src/main.cpp": """#include <SimpleFOC.h>

// BLDC motor & driver setup
BLDCMotor motor = BLDCMotor(7); // 7 pole pairs
BLDCDriver3PWM driver = BLDCDriver3PWM(25, 26, 27, 14);

// Magnetic sensor setup
MagneticSensorI2C sensor = MagneticSensorI2C(AS5600_I2C);

void setup() {
    Serial.begin(115200);
    sensor.init();
    motor.linkSensor(&sensor);
    driver.voltage_power_supply = 12;
    driver.init();
    motor.linkDriver(&driver);
    motor.controller = MotionControlType::velocity;
    motor.init();
    motor.initFOC();
    Serial.println("SimpleFOC BLDC Driver Ready.");
}

void loop() {
    motor.loopFOC();
    motor.move(10.0f); // Target 10 rad/s
}
""",
    }
}


def scaffold_project(template_name: str, target_dir: Path) -> bool:
    """
    Scaffolds an embedded/drone project template into the designated directory.
    """
    if template_name not in TEMPLATES:
        return False

    files = TEMPLATES[template_name]
    for rel_path, content in files.items():
        dest = target_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

    return True
