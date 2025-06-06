import sys
from pathlib import Path

script_dir = Path(__file__).parent
sys.path.append(str(script_dir / "libs"))

import cv2
import numpy as np
import time
from face import FaceDetector, FaceLandmarksDetector
from iris import IrisDetector
from collections import deque
from multiprocessing import Queue
from ultralytics import YOLO
from ultralytics.utils import LOGGER

last_detected_label = None
LOGGER.setLevel('ERROR')

def gesture_recognition(frame,model,queue):
    global last_detected_label
    results = model(frame, stream=True)
    current_detected_label = None
    conf = 0.0

    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])  # 确保 conf 是 Python float
            cls = int(box.cls[0])
            label = f"{model.names[cls]} {conf:.2f}"
            current_detected_label = model.names[cls]

            # 绘制边界框和标签
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    if (
        current_detected_label
        and conf > 0.9
        and current_detected_label != last_detected_label
        and current_detected_label != 'no_gesture'
    ):
        queue.put(current_detected_label)
        print(f"Detected gesture: {current_detected_label}")
        last_detected_label = current_detected_label

    return frame#cv2.imshow('YOLO Real-Time Gesture Recognition', frame)

prev_gaze_zone = None

def real_time_tracking(gesture_queue, eye_queue, head_queue):

    global prev_gaze_zone

    face_detector = FaceDetector()
    face_landmarks_detector = FaceLandmarksDetector()
    iris_detector = IrisDetector()
    
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    # 旋转矩阵转欧拉角
    def rotation_matrix_to_euler_angles(R):
        sy = np.sqrt(R[0,0] * R[0,0] + R[1,0] * R[1,0])
        singular = sy < 1e-6
        if not singular:
            x = np.arctan2(R[2,1], R[2,2])
            y = np.arctan2(-R[2,0], sy)
            z = np.arctan2(R[1,0], R[0,0])
        else:
            x = np.arctan2(-R[1,2], R[1,1])
            y = np.arctan2(-R[2,0], sy)
            z = 0
        return np.array([x, y, z])  # 返回俯仰、偏航、滚转（弧度）

    def compensate_head_pose(gaze_vector, head_rotation):
        compensated_vector = gaze_vector.copy()
        # 补偿偏航角（yaw）对水平视线的影响
        compensated_vector[0] -= head_rotation[1] * 0.5
        # 补偿俯仰角（pitch）对垂直视线的影响
        compensated_vector[1] -= head_rotation[0] * 0.5
        return compensated_vector
    
    fps_counter = 0
    start_time = time.time()
    fps = 0
    
    IRIS_POINT_COLOR = (0, 0, 255)   # 红色 - 虹膜点
    LEFT_EYE_COLOR = (255, 200, 0)   # 蓝色 - 左眼中心
    RIGHT_EYE_COLOR = (0, 200, 255)  # 黄色 - 右眼中心

    center_threshold_x = 0.20
    center_threshold_y = 0.20
    total_frames = 0

    pitch_history = deque(maxlen=15)  # 存储最近10帧的俯仰角
    yaw_history = deque(maxlen=15)    # 存储最近10帧的偏航角
    nod_threshold = 0.4               # 点头检测阈值（弧度）
    shake_threshold = 0.4             # 摇头检测阈值（弧度）
    nod_display_frames = 15           # 点头结果显示帧数
    shake_display_frames = 15         # 摇头结果显示帧数
    nod_counter = 0                   # 点头结果显示计数器
    shake_counter = 0                 # 摇头结果显示计数器
    current_nod_state = "NORMAL"      # 当前点头状态
    current_shake_state = "NORMAL"    # 当前摇头状态
    last_action_time = time.time()    # 上次动作检测时间
    action_cooldown = 0.5             # 动作冷却时间（秒）
    NOD_THRESHOLD_DEG = 30.0  # 点头阈值30度
    SHAKE_THRESHOLD_DEG = 60.0  # 摇头阈值80度
    
    current_dir = Path(__file__).parent
    model_path = current_dir / "YOLOv10x.pt"
    model = YOLO(str(model_path))
    
    if not cap.isOpened():
        print("无法打开摄像头")
        exit()


    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("无法读取帧")
                time.sleep(0.1)
                continue
            frame = cv2.flip(frame, 1)  # 水平翻转
            display_frame = frame.copy()
            display_frame = gesture_recognition(display_frame, model, gesture_queue)
            
            fps_counter += 1
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time > 1.0:
                fps = fps_counter / elapsed_time
                fps_counter = 0
                start_time = current_time
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.uint8)
            
            try:
                face_detections = face_detector.predict(rgb_frame)
            except Exception as e:
                print(f"未检测到瞳孔: {e}")

                cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, "No Eyes or Single Eye in the Camera", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(display_frame, "Press 'q' to quit", (10, display_frame.shape[0] - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                cv2.imshow('Real-Time Gaze Tracking', display_frame)
                
                key = cv2.waitKey(1)
                if key == ord('q'):
                    print("用户请求退出...")
                    cap.release()
                    cv2.destroyAllWindows()
                    sys.exit()
                continue
            
            # 人脸关键点检测
            try:
                face_landmarks_detections = face_landmarks_detector.predict(rgb_frame)
            except Exception as e:
                print(f"未检测到人脸: {e}")
                cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, "No Face in the Camera", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(display_frame, "Press 'q' to quit", (10, display_frame.shape[0] - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.imshow('Real-Time Gaze Tracking', display_frame)
                key = cv2.waitKey(1)
                if key == ord('q'):
                    print("用户请求退出...")
                    cap.release()
                    cv2.destroyAllWindows()
                    sys.exit()
                continue

            head_pose = np.zeros(3)

            image_size = (frame.shape[1], frame.shape[0])

            focal_length = image_size[0]
            center = (image_size[0]/2, image_size[1]/2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype="float32")

            dist_coeffs = np.zeros((4, 1))  # 假设无畸变

            
            for face_landmarks_detection in face_landmarks_detections:
                # 234 右耳轮廓
                # 454 左耳轮廓
                # 1 鼻尖
                # 374 左眼
                # 145 右眼
                # 13 嘴巴中心

                indices=[1, 9, 57, 130, 287, 359]

                # 获取索引对应的 x, y，并乘上图像尺寸
                image_points = (face_landmarks_detection[indices])[:, :2]

                # 转换为 float64 类型
                image_points = np.array(image_points, dtype=np.float64)

                model_points = np.array([
                    [285, 528, 200],
                    [285, 371, 152],
                    [197, 574, 128],
                    [173, 425, 108],
                    [360, 574, 128],
                    [391, 425, 108]
                ], dtype=np.float64)

                try:
                    (success, rotation_vector, translation_vector) = cv2.solvePnP(
                        model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)
                    
                    # 转换为旋转矩阵
                    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
                    
                    # 转换为欧拉角（俯仰、偏航、滚转）
                    head_pose = rotation_matrix_to_euler_angles(rotation_matrix)
                except Exception as e:
                    print(f"头部姿态估计失败: {e}")

                # ========眼部识别=========

                # print(face_detections)
                left_eye_image, right_eye_image, left_config, right_config = iris_detector.preprocess(
                    rgb_frame, face_landmarks_detection
                )
                
                left_eye_contour, left_eye_iris = iris_detector.predict(left_eye_image, isLeft=True)
                right_eye_contour, right_eye_iris = iris_detector.predict(right_eye_image, isLeft=False)
                
                ori_left_eye_contour, ori_left_iris = iris_detector.postprocess(
                    left_eye_contour, left_eye_iris, left_config
                )
                ori_right_eye_contour, ori_right_iris = iris_detector.postprocess(
                    right_eye_contour, right_eye_iris, right_config
                )
                
                left_eye_contour_2d = ori_left_eye_contour[:, :2]
                left_iris_2d = ori_left_iris[:, :2]
                right_eye_contour_2d = ori_right_eye_contour[:, :2]
                right_iris_2d = ori_right_iris[:, :2]

                if left_eye_contour_2d.shape[0] == 0 or left_iris_2d.shape[0] == 0:
                    print("左眼轮廓或虹膜数据为空，跳过该帧")
                    continue

                if right_eye_contour_2d.shape[0] == 0 or right_iris_2d.shape[0] == 0:
                    print("左眼轮廓或虹膜数据为空，跳过该帧")
                    continue
                # print(left_eye_contour_2d)
                left_eye_center = np.mean(left_eye_contour_2d, axis=0)
                right_eye_center = np.mean(right_eye_contour_2d, axis=0)
                # print(left_eye_center)
                # print(left_iris_2d)
                left_iris_center = left_iris_2d[0]
                right_iris_center = right_iris_2d[0]
                # print(left_iris_center)
                left_gaze_vector = (left_iris_center - left_eye_center)
                right_gaze_vector = (right_iris_center - right_eye_center)

                left_gaze_vector /= np.linalg.norm(left_gaze_vector) + 1e-6
                right_gaze_vector /= np.linalg.norm(right_gaze_vector) + 1e-6

                # 融合视线向量（提升精度）
                fused_gaze_vector = (left_gaze_vector + right_gaze_vector) / 2.0

                left_compensated = compensate_head_pose(left_gaze_vector, head_pose)
                right_compensated = compensate_head_pose(right_gaze_vector, head_pose)
                fused_gaze_vector = (left_compensated + right_compensated) / 2.0
                
                # fused_gaze_vector /= np.linalg.norm(fused_gaze_vector) + 1e-6

                def get_gaze_direction(gaze_vector):
                    x, y = gaze_vector
                    directions = []
                    if x < -0.2: directions.append("LEFT")
                    elif x > 0.2: directions.append("RIGHT")
                    if y < -0.8: directions.append("UP")
                    elif y > 0.6: directions.append("DOWN")
                    if not directions: directions.append("CENTER")
                    return " ".join(directions)

                def get_gaze_zone(gaze_vector):
                    x, y = gaze_vector
                    # 定义九宫格区域
                    if x < -center_threshold_x and y < -center_threshold_y:
                        return "UP-LEFT"
                    # elif abs(x) <= center_threshold_x and y < -center_threshold_y:
                    #     return "UP"
                    elif x > center_threshold_x and y < -center_threshold_y:
                        return "UP-RIGHT"
                    elif x < -center_threshold_x and abs(y) <= center_threshold_y:
                        return "LEFT"
                    elif x > center_threshold_x and abs(y) <= center_threshold_y:
                        return "RIGHT"
                    elif x < -center_threshold_x and y > center_threshold_y:
                        return "DOWN-LEFT"
                    # elif abs(x) <= center_threshold_x and y > center_threshold_y:
                    #     return "DOWN"
                    elif x > center_threshold_x and y > center_threshold_y:
                        return "DOWN-RIGHT"
                    else:
                        return "CENTER"

                left_direction = get_gaze_direction(left_gaze_vector)
                right_direction = get_gaze_direction(right_gaze_vector)
                fused_direction = get_gaze_direction(fused_gaze_vector)

                right_eye = face_detections[0]["right_eye"]
                left_eye = face_detections[0]["left_eye"]
                nose_tip = face_detections[0]["nose_tip"]
                mouth_center = face_detections[0]["mouth_center"]
                right_ear_tragion = face_detections[0]["right_ear_tragion"]
                left_ear_tragion = face_detections[0]["left_ear_tragion"]

                # ===============头部姿势识别=================
                # 获取当前帧的俯仰角和偏航角（弧度）
                pitch = head_pose[0]
                yaw = head_pose[1]
                
                # 添加到历史记录
                pitch_history.append(pitch)
                yaw_history.append(yaw)

                current_time = time.time()
                can_detect_action = (current_time - last_action_time) > action_cooldown
                
                # 检测点头动作（俯仰角变化）
                if len(pitch_history) >= 8 and can_detect_action:
                    # 获取最近8帧数据
                    recent_pitch = list(pitch_history)[-8:]
                    
                    recent_pitch_deg = [np.degrees(p) for p in recent_pitch]
                    
                    pitch_min_deg = min(recent_pitch_deg)
                    pitch_max_deg = max(recent_pitch_deg)
                    pitch_range_deg = pitch_max_deg - pitch_min_deg
                    
                    pitch_changes_deg = [recent_pitch_deg[i] - recent_pitch_deg[i-1] for i in range(1, len(recent_pitch_deg))]
                    
                    consistent_up = sum(1 for change in pitch_changes_deg[:4] if change > 0) >= 2  # 前4帧中至少2帧向上
                    consistent_down = sum(1 for change in pitch_changes_deg[:4] if change < 0) >= 2  # 前4帧中至少2帧向下
                    
                    if pitch_range_deg > NOD_THRESHOLD_DEG and (consistent_up or consistent_down):
                        avg_change = np.mean(pitch_changes_deg[:4])
                        
                        if avg_change > 0:
                            current_nod_state = "NODDING UP"
                        else:
                            current_nod_state = "NODDING DOWN"
                        
                        if len(pitch_changes_deg) >= 6:
                            confirm_trend = True
                            for i in range(4, 6):
                                if (avg_change > 0 and pitch_changes_deg[i] < 0) or (avg_change < 0 and pitch_changes_deg[i] > 0):
                                    confirm_trend = False
                                    break
                            
                            if confirm_trend:
                                nod_counter = nod_display_frames
                                last_action_time = current_time
                                print(f"检测到点头动作: {current_nod_state} ({pitch_range_deg:.1f}度)")
                                head_queue.put("NOD")
                                # 重置摇头检测历史，防止同时触发
                                yaw_history.clear()

                # 检测摇头动作（偏航角变化）
                if len(yaw_history) >= 8 and can_detect_action:
                    # 获取最近8帧数据
                    recent_yaw = list(yaw_history)[-8:]
                    
                    # 转换为度数
                    recent_yaw_deg = [np.degrees(y) for y in recent_yaw]
                    
                    yaw_min_deg = min(recent_yaw_deg)
                    yaw_max_deg = max(recent_yaw_deg)
                    yaw_range_deg = yaw_max_deg - yaw_min_deg

                    yaw_changes_deg = [recent_yaw_deg[i] - recent_yaw_deg[i-1] for i in range(1, len(recent_yaw_deg))]

                    consistent_left = sum(1 for change in yaw_changes_deg[:4] if change < 0) >= 2  # 前4帧中至少2帧向左
                    consistent_right = sum(1 for change in yaw_changes_deg[:4] if change > 0) >= 2  # 前4帧中至少2帧向右
                    
                    if yaw_range_deg > SHAKE_THRESHOLD_DEG and (consistent_left or consistent_right):
                        avg_change = np.mean(yaw_changes_deg[:4])
                        
                        if avg_change > 0:
                            current_shake_state = "SHAKING LEFT"
                        else:
                            current_shake_state = "SHAKING RIGHT"
                        
                        if len(yaw_changes_deg) >= 6:
                            confirm_trend = True
                            for i in range(4, 6):
                                if (avg_change > 0 and yaw_changes_deg[i] < 0) or (avg_change < 0 and yaw_changes_deg[i] > 0):
                                    confirm_trend = False
                                    break
                            
                            if confirm_trend:
                                shake_counter = shake_display_frames
                                last_action_time = current_time
                                print(f"检测到摇头动作: {current_shake_state} ({yaw_range_deg:.1f}度)")
                                head_queue.put("SHAKE")
                                pitch_history.clear()

                if nod_counter > 0:
                    nod_counter -= 1
                if shake_counter > 0:
                    shake_counter -= 1

                gaze_zone = get_gaze_zone(fused_gaze_vector)

                if gaze_zone != prev_gaze_zone:
                    print(f"  头部姿态: P:{np.degrees(head_pose[0]):.1f}°, Y:{np.degrees(head_pose[1]):.1f}°, R:{np.degrees(head_pose[2]):.1f}°")
                    print(f"  眼睛朝向: {gaze_zone}")
                    eye_queue.put(gaze_zone)
                    print("-" * 60) 
                
                prev_gaze_zone = gaze_zone

                # ============== 绘制头部姿势信息 ==============
                # 显示头部姿态信息
                cv2.putText(display_frame, f"Head: P:{np.degrees(head_pose[0]):.1f}°, Y:{np.degrees(head_pose[1]):.1f}°", 
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 0), 2)
                # face_landmarks_detector.visualize(rgb_frame, face_landmarks_detections, None, [1, 145, 374, 13, 234, 454])
                # 显示点头状态
                if nod_counter > 0:
                    cv2.putText(display_frame, f"Head: {current_nod_state}", 
                                (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # 显示摇头状态
                if shake_counter > 0:
                    cv2.putText(display_frame, f"Head: {current_shake_state}", 
                                (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # ============== 绘制眼部 ==============
                if left_iris_2d is not None and len(left_iris_2d) > 0:
                    for point in left_iris_2d:
                        x, y = point
                        cv2.circle(display_frame, (int(x), int(y)), 1, IRIS_POINT_COLOR, -1)

                if right_iris_2d is not None and len(right_iris_2d) > 0:
                    for point in right_iris_2d:
                        x, y = point
                        cv2.circle(display_frame, (int(x), int(y)), 1, IRIS_POINT_COLOR, -1)

                if left_eye_center is not None:
                    cv2.circle(display_frame, (int(left_eye_center[0]), int(left_eye_center[1])), 
                            3, LEFT_EYE_COLOR, -1)
                if right_eye_center is not None:
                    cv2.circle(display_frame, (int(right_eye_center[0]), int(right_eye_center[1])), 
                            3, RIGHT_EYE_COLOR, -1)

                # ============== 其他UI元素 ==============
                cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Zone: {gaze_zone}", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                            (0, 255, 0) if gaze_zone == "CENTER" else (0, 200, 255), 2)
                # cv2.putText(display_frame, f"Center: {center_frequency:.1f}%", (10, 90), 
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, "Press 'q' to quit", (10, display_frame.shape[0] - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow('Real-Time Gaze Tracking', display_frame)
            
            key = cv2.waitKey(1)
            if key == ord('q'):
                print("用户请求退出...")
                cap.release()
                cv2.destroyAllWindows()
                sys.exit()
        except Exception as e:
            continue
    
    cap.release()
    cv2.destroyAllWindows()

def fusion_gesture_start(gesture_queue, eye_queue, head_queue):
    while True:
        try:
            real_time_tracking(gesture_queue, eye_queue, head_queue)
        except Exception as e:
            print(f"发生异常: {e}")
            continue