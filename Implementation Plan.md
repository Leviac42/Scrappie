Scrappie Robot Implementation Plan
Goal Description
Build a ROS2-based software stack for the "Scrappie" robot using the specified hardware (Jetson Orin Nano, RealSense, Mobile Base). The system will support mapping, navigation, and person following, all containerized via Docker.

Hardware & Architecture
Robot Computer: Jetson Orin Nano (Target Deployment) / PC (Development)
Sensors:
2x Intel RealSense D435i (Front & Rear coverage)
HC-SR04 (Sonar - Optional backup)
Actuation: MDDS30 Driver + 24v Motors (Differential Drive)
Middleware: ROS2 Humble Hawksbill
Software Components
1. Docker Environment [/docker]
Dockerfile: Multi-stage build (Dev vs Jetson Prod).
docker-compose.yml: Services for base, front_cam, rear_cam, nav.
2. Robot Description [src/scrappie_description]
Integrate existing jazzy_elite_es.urdf.xarco.
Update: Add mount point and TF link for second RealSense camera (Rear facing).
3. Base Control [src/scrappie_base]
Node: Differential drive controller.
Interface: Interacts with MDDS30 via Serial.
Odometry: Primary: Visual Odometry (Fused from both cameras or just Front).
4. Perception & Mapping [src/scrappie_slam]
Front Camera: Visual Odometry + Person Tracking + Obstacle Avoidance.
Rear Camera: Rear Obstacle Avoidance + 360 Mapping.
Fusion: Combine LaserScans from both cameras into a single costmap source.
5. Navigation [src/scrappie_nav]
Stack: Nav2 (Navigation 2).
Config: Planners, Controllers.
Follow: Custom behavior tree node to use Front Camera detections.
Step-by-Step Implementation
Phase 1: Environment Setup ✅ COMPLETED
 ✅ Create Dockerfile with ROS2 Humble, Nav2, and RealSense dependencies.
 ✅ Create docker-compose.yml.
 ✅ Create ROS2 Workspace structure (src/).
 ✅ All packages built successfully

Phase 2: Description & Simulation ✅ COMPLETED
 ✅ Update URDF to include 2nd camera.
 ✅ Verify in Rviz - launch file created.
 ✅ Robot description package complete

Phase 3: Hardware Integration ✅ COMPLETED
 ✅ Motor Driver Node (scrappie_base) - MDDS30 serial interface.
 ✅ Dual Camera Launch file (dual_realsense.launch.py).
 ✅ Scan merger utility for 360° coverage.
 ✅ Base controller with odometry publishing.

Phase 4: Navigation & Application 🚧 READY FOR TESTING
 ✅ Configure Nav2 to use 2x Scan sources.
 🚧 Create follow_person node (planned).
 🚧 Test autonomous navigation.
 🚧 Map environment with SLAM.

Phase 5: Person Following 🚧 PLANNED
 🚧 Implement person detection (YOLO/MediaPipe).
 🚧 Create person tracking behavior.
 🚧 Integrate with Nav2 behavior tree.

Phase 6: Production Deployment 🚧 PLANNED
 🚧 Deploy to Jetson Orin Nano.
 🚧 Performance tuning and optimization.
 🚧 Create systemd service for auto-start.
 🚧 Safety features (emergency stop, collision avoidance).

Phase 7: Jetson Optimization ✅ COMPLETED
 ✅ Created Jetson-specific Dockerfile with NVIDIA L4T base
 ✅ Configured GPIO UART (/dev/ttyTHS0) for serial communication
 ✅ Built optimized docker-compose for Jetson with NVIDIA runtime
 ✅ Created automated setup script (setup_jetson.sh)
 ✅ Jetson-specific launch files and configurations
 ✅ Complete deployment documentation (JETSON_DEPLOYMENT.md)
 ✅ Development vs Production comparison guide
User Review Required
Deployment: confirmed deployment target is Jetson. Dockerfile will be set up for cross-platform dev where possible, but optimized for Jetson later.