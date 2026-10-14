
#!/usr/bin/env python3

import math
import rclpy

from rclpy.node import Node
from rclpy.action import ActionClient

from geometry_msgs.msg import Point, PointStamped
from visualization_msgs.msg import Marker, MarkerArray
from std_srvs.srv import Trigger

from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus


class RectanglePatrol(Node):

    def __init__(self):
        super().__init__('rectangle_patrol')

        self.points = []
        self.running = False
        self.goal_pending = False
        self.active_goal = None
        self.current_index = 0
        self.laps = 0

        # Retry configuration
        self.retry_count = 0
        self.max_retries = 2
        self.retry_delay = 2.0
        self.retry_timer = None

        # Foxglove clicked points
        self.create_subscription(
            PointStamped,
            '/patrol/clicked_point',
            self.point_callback,
            10
        )

        # Visualization markers
        self.marker_pub = self.create_publisher(
            MarkerArray,
            '/patrol/markers',
            10
        )

        self.create_timer(2.0, self.publish_markers)

        # Nav2 action client
        self.nav_client = ActionClient(
            self,
            NavigateToPose,
            '/navigate_to_pose'
        )

        # Patrol control services
        self.create_service(
            Trigger, '/patrol/start', self.start_callback
        )
        self.create_service(
            Trigger, '/patrol/stop', self.stop_callback
        )
        self.create_service(
            Trigger, '/patrol/clear', self.clear_callback
        )

        self.get_logger().info(
            'Ready. Select 4 waypoints in Foxglove.'
        )

    def is_busy(self):
        return (
            self.running
            or self.goal_pending
            or self.active_goal is not None
            or self.retry_timer is not None
        )

    def point_callback(self, msg):
        """Receive waypoint coordinates from Foxglove."""

        if self.is_busy():
            self.get_logger().warn(
                'Cannot edit waypoints during navigation.'
            )
            return

        if len(self.points) >= 4:
            self.get_logger().warn(
                'Already have 4 points. Use /patrol/clear.'
            )
            return

        if msg.header.frame_id.lstrip('/') != 'map':
            self.get_logger().warn(
                f'Expected map frame, got {msg.header.frame_id}'
            )
            return

        x = float(msg.point.x)
        y = float(msg.point.y)

        if not math.isfinite(x) or not math.isfinite(y):
            self.get_logger().warn('Invalid waypoint.')
            return

        self.points.append((x, y))

        self.get_logger().info(
            f'Waypoint {len(self.points)}: ({x:.2f}, {y:.2f})'
        )

        self.publish_markers()

        if len(self.points) == 4:
            self.get_logger().info(
                'All 4 waypoints selected. '
                'Inspect route, then call /patrol/start.'
            )

    def heading_to_next(self, index):
        """Face the next corner of the route."""

        x1, y1 = self.points[index]
        x2, y2 = self.points[(index + 1) % 4]

        return math.atan2(y2 - y1, x2 - x1)

    def publish_markers(self):
        """Visualize the waypoints and route in Foxglove."""

        if not self.points:
            return

        markers = MarkerArray()
        stamp = self.get_clock().now().to_msg()

        # Connecting route
        line = Marker()
        line.header.frame_id = 'map'
        line.header.stamp = stamp
        line.ns = 'patrol_route'
        line.id = 0
        line.type = Marker.LINE_STRIP
        line.action = Marker.ADD
        line.pose.orientation.w = 1.0

        line.scale.x = 0.05
        line.color.r = 1.0
        line.color.g = 0.8
        line.color.a = 1.0

        route = list(self.points)

        if len(route) == 4:
            route.append(route[0])

        for x, y in route:
            line.points.append(
                Point(x=float(x), y=float(y), z=0.1)
            )

        markers.markers.append(line)

        # Arrows and waypoint labels
        for i, (x, y) in enumerate(self.points):

            if len(self.points) == 4:
                yaw = self.heading_to_next(i)
            elif i < len(self.points) - 1:
                nx, ny = self.points[i + 1]
                yaw = math.atan2(ny - y, nx - x)
            else:
                yaw = 0.0

            arrow = Marker()
            arrow.header.frame_id = 'map'
            arrow.header.stamp = stamp
            arrow.ns = 'patrol_arrows'
            arrow.id = i
            arrow.type = Marker.ARROW
            arrow.action = Marker.ADD

            arrow.pose.position.x = x
            arrow.pose.position.y = y
            arrow.pose.position.z = 0.15

            arrow.pose.orientation.z = math.sin(yaw / 2)
            arrow.pose.orientation.w = math.cos(yaw / 2)

            arrow.scale.x = 0.35
            arrow.scale.y = 0.10
            arrow.scale.z = 0.10

            arrow.color.g = 1.0
            arrow.color.a = 1.0

            markers.markers.append(arrow)

            label = Marker()
            label.header.frame_id = 'map'
            label.header.stamp = stamp
            label.ns = 'patrol_labels'
            label.id = i
            label.type = Marker.TEXT_VIEW_FACING
            label.action = Marker.ADD

            label.pose.position.x = x
            label.pose.position.y = y
            label.pose.position.z = 0.5
            label.pose.orientation.w = 1.0

            label.scale.z = 0.25
            label.color.r = 1.0
            label.color.g = 1.0
            label.color.b = 1.0
            label.color.a = 1.0

            label.text = f'WP{i + 1}'
            markers.markers.append(label)

        self.marker_pub.publish(markers)

    def start_callback(self, request, response):
        """Start patrolling the selected waypoints."""

        if self.is_busy():
            response.success = False
            response.message = 'Patrol already running or stopping.'
            return response

        if len(self.points) != 4:
            response.success = False
            response.message = 'Select 4 waypoints first.'
            return response

        # Validate separation between consecutive corners
        for i in range(4):
            x1, y1 = self.points[i]
            x2, y2 = self.points[(i + 1) % 4]

            if math.hypot(x2 - x1, y2 - y1) < 0.3:
                response.success = False
                response.message = 'Waypoints too close.'
                return response

        if not self.nav_client.server_is_ready():
            response.success = False
            response.message = 'Nav2 unavailable.'
            return response

        self.running = True
        self.current_index = 0
        self.laps = 0
        self.retry_count = 0

        self.get_logger().info('Starting patrol.')
        self.send_next_goal()

        response.success = True
        response.message = 'Patrol started.'
        return response

    def send_next_goal(self):
        """Send the current waypoint to Nav2."""

        if not self.running:
            return

        i = self.current_index
        x, y = self.points[i]
        yaw = self.heading_to_next(i)

        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'

        # Zero timestamp uses latest available transform
        goal.pose.header.stamp.sec = 0
        goal.pose.header.stamp.nanosec = 0

        goal.pose.pose.position.x = float(x)
        goal.pose.pose.position.y = float(y)
        goal.pose.pose.orientation.z = math.sin(yaw / 2)
        goal.pose.pose.orientation.w = math.cos(yaw / 2)

        self.get_logger().info(
            f'Navigating to WP{i + 1}: '
            f'({x:.2f}, {y:.2f}) '
            f'[Attempt {self.retry_count + 1}/'
            f'{self.max_retries + 1}]'
        )

        self.goal_pending = True

        future = self.nav_client.send_goal_async(goal)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        """Handle Nav2 goal acceptance."""

        self.goal_pending = False

        try:
            handle = future.result()
        except Exception as error:
            self.get_logger().error(
                f'Goal request error: {error}'
            )
            self.running = False
            return

        if handle is None or not handle.accepted:
            self.get_logger().error(
                'Nav2 rejected goal. Patrol stopped.'
            )
            self.running = False
            return

        self.active_goal = handle

        result_future = handle.get_result_async()
        result_future.add_done_callback(self.goal_result_callback)

        # Stop may have been requested while goal was pending
        if not self.running:
            self.cancel_current_goal()

    def goal_result_callback(self, future):
        """Advance on success, retry the same goal on abort."""

        try:
            result = future.result()
        except Exception as error:
            self.active_goal = None
            self.get_logger().error(
                f'Navigation result error: {error}'
            )
            self.running = False
            return

        self.active_goal = None

        if not self.running:
            self.get_logger().info('Patrol stopped.')
            return

        if result is None:
            self.get_logger().error(
                'No navigation result. Patrol stopped.'
            )
            self.running = False
            return

        # Successful navigation
        if result.status == GoalStatus.STATUS_SUCCEEDED:

            self.get_logger().info(
                f'Waypoint {self.current_index + 1} reached.'
            )

            self.retry_count = 0
            self.current_index = (self.current_index + 1) % 4

            if self.current_index == 0:
                self.laps += 1
                self.get_logger().info(
                    f'Lap {self.laps} complete.'
                )

            self.send_next_goal()
            return

        # Status 6: navigation aborted
        if result.status == GoalStatus.STATUS_ABORTED:

            if self.retry_count < self.max_retries:

                self.retry_count += 1

                self.get_logger().warn(
                    f'WP{self.current_index + 1} aborted. '
                    f'Retrying in {self.retry_delay:.1f}s '
                    f'({self.retry_count}/{self.max_retries} retries).'
                )

                self.retry_timer = self.create_timer(
                    self.retry_delay,
                    self.retry_current_goal
                )
                return

        # Other failures, or maximum retries reached
        self.get_logger().error(
            f'WP{self.current_index + 1} failed '
            f'(status {result.status}). Patrol stopped.'
        )

        self.running = False

    def retry_current_goal(self):
        """Retry the failed waypoint after a delay."""

        self.cancel_retry_timer()

        if not self.running:
            return

        if not self.nav_client.server_is_ready():
            self.get_logger().error(
                'Nav2 unavailable. Patrol stopped.'
            )
            self.running = False
            return

        self.send_next_goal()

    def cancel_retry_timer(self):
        """Cancel any pending retry."""

        if self.retry_timer is not None:
            timer = self.retry_timer
            self.retry_timer = None
            timer.cancel()
            self.destroy_timer(timer)

    def cancel_current_goal(self):
        """Request cancellation of active navigation."""

        if self.active_goal is not None:
            try:
                self.active_goal.cancel_goal_async()
            except Exception as error:
                self.get_logger().error(
                    f'Cancellation request failed: {error}'
                )

    def stop_callback(self, request, response):
        """Stop patrol and cancel pending actions."""

        self.running = False
        self.cancel_retry_timer()
        self.cancel_current_goal()

        response.success = True
        response.message = (
            'Stop requested. Confirm robot has stopped.'
        )

        self.get_logger().info('Patrol stop requested.')
        return response

    def clear_callback(self, request, response):
        """Clear all selected waypoints."""

        if self.is_busy():
            response.success = False
            response.message = 'Stop patrol before clearing.'
            return response

        self.points.clear()
        self.current_index = 0
        self.laps = 0
        self.retry_count = 0

        delete = Marker()
        delete.header.frame_id = 'map'
        delete.action = Marker.DELETEALL

        markers = MarkerArray()
        markers.markers.append(delete)
        self.marker_pub.publish(markers)

        self.get_logger().info('Waypoints cleared.')

        response.success = True
        response.message = 'Ready for 4 new points.'
        return response


def main():
    rclpy.init()
    node = RectanglePatrol()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.running = False
        node.cancel_retry_timer()
        node.cancel_current_goal()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
