ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="$(xacro /workspace/src/my_robot_description/urdf/my_robot.urdf.xacro)"

ros2 run controller_manager ros2_control_node --ros-args --params-file /workspace/src/my_robot_bringup/config/my_robot_controllers.yaml

ros2 run controller_manager spawner joint_state_broadcaster

ros2 run controller_manager spawner diff_drive_controller

ros2 run rviz2 rviz2 -d /workspace/src/my_robot_description/rviz/urdf_config.rviz 

ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:/diff_drive_controller/cmd_vel -p stamped:=true