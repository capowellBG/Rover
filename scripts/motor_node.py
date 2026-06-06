import math

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState
from dual_g2_hpmd_rpi import motors, MAX_SPEED

WATCHDOG_TIMEOUT = 0.5   # seconds
PUBLISH_HZ = 30.0
# Tune this to match actual top wheel speed; affects visual spin rate only
MAX_WHEEL_RAD_S = 6.0

JOINTS = ['front_left_joint', 'front_right_joint', 'rear_left_joint', 'rear_right_joint']


class MotorDriverNode(Node):
    def __init__(self):
        super().__init__('motor_driver')
        self.create_subscription(Twist, 'cmd_vel', self.on_cmd_vel, 10)
        self._js_pub = self.create_publisher(JointState, 'joint_states', 10)
        self.watchdog = self.create_timer(WATCHDOG_TIMEOUT, self.on_watchdog_timeout)
        self._js_timer = self.create_timer(1.0 / PUBLISH_HZ, self._publish_joint_states)
        self._moving = False
        self._left_vel = 0.0
        self._right_vel = 0.0
        self._positions = [0.0] * 4
        self._last_time = self.get_clock().now()
        self.get_logger().info('Motor driver node started')

    def on_cmd_vel(self, msg):
        linear = -msg.linear.x   # -1.0 to 1.0
        angular = -msg.angular.z  # -1.0 to 1.0

        left = max(-1.0, min(1.0, linear - angular))
        right = max(-1.0, min(1.0, linear + angular))

        motors.setSpeeds(int(left * MAX_SPEED), int(right * MAX_SPEED))
        self._left_vel = left * MAX_WHEEL_RAD_S
        self._right_vel = right * MAX_WHEEL_RAD_S
        self._moving = True
        self.watchdog.reset()

    def _publish_joint_states(self):
        now = self.get_clock().now()
        dt = (now - self._last_time).nanoseconds * 1e-9
        self._last_time = now

        # front_left, front_right, rear_left, rear_right
        vels = [self._left_vel, self._right_vel, self._left_vel, self._right_vel]
        for i, v in enumerate(vels):
            self._positions[i] = (self._positions[i] + v * dt) % (2.0 * math.pi)

        msg = JointState()
        msg.header.stamp = now.to_msg()
        msg.name = JOINTS
        msg.position = list(self._positions)
        msg.velocity = vels
        self._js_pub.publish(msg)

    def on_watchdog_timeout(self):
        if self._moving:
            motors.setSpeeds(0, 0)
            # self.get_logger().warn('cmd_vel watchdog timeout — motors stopped')
            self._moving = False
            self._left_vel = 0.0
            self._right_vel = 0.0


def main():
    rclpy.init()
    node = MotorDriverNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        motors.forceStop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()