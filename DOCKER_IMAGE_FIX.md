# Docker Image Fix - JetPack 6.x

## Issue
The image `dustynv/ros:humble-desktop-l4t-r36.3.0` doesn't exist on Docker Hub.

## Solution
Updated to use: `dustynv/ros:humble-ros-base-l4t-r36.3.0`

This is the correct image for JetPack 6.x (L4T R36.3.0).

## What Changed
- **Base Image**: Now using `humble-ros-base` instead of `humble-desktop`
- **Desktop Tools**: Added RViz2 and rqt tools manually
- **Result**: Same functionality, correct image tag

## Updated Files
- `docker/Dockerfile.jetson` - Fixed base image and added desktop tools

## Next Steps
Re-run the build on your Jetson:

```bash
# Transfer updated Dockerfile
scp docker/Dockerfile.jetson aswingley@192.168.1.119:~/Scrappie/docker/

# SSH into Jetson and rebuild
ssh aswingley@192.168.1.119
cd ~/Scrappie
docker-compose -f docker/docker-compose.jetson.yml build
```

The build should work now!
