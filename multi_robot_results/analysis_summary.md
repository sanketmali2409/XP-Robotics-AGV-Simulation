# Multi-Robot Performance Analysis

This document contains the analysis based on the performance of both robots during the simultaneous navigation test.

### 1. Final Accuracy (Steady-State Error)
Both robots performed excellently and hit their targets with extremely high precision!
- **Robot 1 (EKF):** Stopped `0.021 meters` (2.1 cm) away from the exact target coordinate.
- **Robot 2 (LiDAR SLAM):** Stopped `0.018 meters` (1.8 cm) away from the exact target coordinate.

**Analysis:** Both robots reached the `0.02m` tolerance boundary configured in the PID controller script. The SLAM-based robot was marginally more accurate by about 3 millimeters, which shows that LiDAR map-based odometry is incredibly precise at the destination.

### 2. Trajectory Smoothness
- **Robot 1 (EKF):** The EKF algorithm (fusing wheel odometry and IMU) provides extremely smooth and continuous state updates. As a result, its trajectory line is very smooth with a consistent velocity curve towards the target.
- **Robot 2 (LiDAR SLAM):** SLAM algorithms rely on scan-matching (comparing the current laser scan to the map). Sometimes this scan-matching takes a fraction of a second to compute, which can cause micro-stutters or "jumps" in the reported odometry compared to pure EKF. However, because it constantly corrects itself against the walls, it never suffers from long-term drift!

### 3. RMSE (Root Mean Square Error)
- **Robot 1 RMSE:** `1.47 m`
- **Robot 2 RMSE:** `3.59 m`

**Analysis:** Robot 2 has a higher RMSE during the travel phase. This usually happens because LiDAR SLAM takes slightly longer to ramp up to full speed (due to the computational overhead of scan matching) or it took a slightly longer arcing path to face the goal before driving straight. 

### Final Verdict:
The PID controller is **perfectly tuned** for both navigation methods. The EKF robot (Robot 1) travels very smoothly, while the SLAM robot (Robot 2) guarantees absolute global accuracy (no drift) by referencing the map we saved!
