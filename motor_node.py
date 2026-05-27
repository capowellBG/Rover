import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from dual_g2_hpmd_rpi import motors, MAX_SPEED


class MotorDriverNode(Node):
    def __init__(self):
        super().__init__('motor_driver')
        self.create_subscription(Twist, 'cmd_vel', self.on_cmd_vel, 10)
        self.get_logger().info('Motor driver node started')

    def on_cmd_vel(self, msg):
        linear = msg.linear.x    # -1.0 to 1.0
        angular = msg.angular.z  # -1.0 to 1.0

        left = max(-1.0, min(1.0, linear - angular))
        right = max(-1.0, min(1.0, linear + angular))

        # self.get_logger().info(f'linear={linear:.2f} angular={angular:.2f} -> L={int(left * MAX_SPEED)} R={int(right * MAX_SPEED)}')
        motors.setSpeeds(int(left * MAX_SPEED), int(right * MAX_SPEED))


def main():
    rclpy.init()
    node = MotorDriverNode()
    try:
        rclpy.spin(node)
    finally:
        motors.forceStop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
