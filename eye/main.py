import cv2
import numpy as np
import time
import sys
from PIL import Image
from libs.face import FaceDetector, FaceLandmarksDetector
from libs.iris import IrisDetector

def real_time_gaze_tracking():

    face_detector = FaceDetector()
    face_landmarks_detector = FaceLandmarksDetector()
    iris_detector = IrisDetector()
    
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("无法打开摄像头")
        return
    
    print("启动实时眼动追踪...")
    print("按 'q' 键退出")
    print("=" * 60)
    
    fps_counter = 0
    start_time = time.time()
    fps = 0
    
    IRIS_POINT_COLOR = (0, 0, 255)   # 红色 - 虹膜点
    LEFT_EYE_COLOR = (255, 200, 0)   # 蓝色 - 左眼中心
    RIGHT_EYE_COLOR = (0, 200, 255)  # 黄色 - 右眼中心
    
    while True:
        try:
        
            ret, frame = cap.read()
            if not ret:
                print("无法读取帧")
                time.sleep(0.1)
                continue
            
            frame = cv2.flip(frame, 1)
            
            display_frame = frame.copy()
            
            fps_counter += 1
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time > 1.0:
                fps = fps_counter / elapsed_time
                fps_counter = 0
                start_time = current_time
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
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
            
            for face_idx, face_landmarks_detection in enumerate(face_landmarks_detections):

                left_eye_image, right_eye_image, left_config, right_config = iris_detector.preprocess(
                    rgb_frame, face_landmarks_detection
                )
                
                left_eye_contour, left_eye_iris = iris_detector.predict(left_eye_image)
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
                
                left_eye_center = np.mean(left_eye_contour_2d, axis=0)
                right_eye_center = np.mean(right_eye_contour_2d, axis=0)
                
                left_iris_center = np.mean(left_iris_2d, axis=0)
                right_iris_center = np.mean(right_iris_2d, axis=0)
                
                left_gaze_vector = (left_iris_center - left_eye_center)
                right_gaze_vector = (right_iris_center - right_eye_center)

                left_gaze_vector /= np.linalg.norm(left_gaze_vector) + 1e-6
                right_gaze_vector /= np.linalg.norm(right_gaze_vector) + 1e-6
                
                def get_gaze_direction(gaze_vector):
                    x, y = gaze_vector
                    directions = []
                    if x < -0.2: directions.append("LEFT")
                    elif x > 0.2: directions.append("RIGHT")
                    if y < -0.2: directions.append("UP")
                    elif y > 0.4: directions.append("DOWN")
                    if not directions: directions.append("CENTER")
                    return " ".join(directions)
                
                left_direction = get_gaze_direction(left_gaze_vector)
                right_direction = get_gaze_direction(right_gaze_vector)
                
                print(f"人脸 {face_idx+1} 结果:")
                print(f"  左眼朝向: {left_direction} | 向量: [{left_gaze_vector[0]:.4f}, {left_gaze_vector[1]:.4f}]")
                print(f"  右眼朝向: {right_direction} | 向量: [{right_gaze_vector[0]:.4f}, {right_gaze_vector[1]:.4f}]")
                print(f"  左眼中心: ({left_eye_center[0]:.1f}, {left_eye_center[1]:.1f}) | 虹膜中心: ({left_iris_center[0]:.1f}, {left_iris_center[1]:.1f})")
                print(f"  右眼中心: ({right_eye_center[0]:.1f}, {right_eye_center[1]:.1f}) | 虹膜中心: ({right_iris_center[0]:.1f}, {right_iris_center[1]:.1f})")
                print("-" * 60)
                
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
                
                cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Left: {left_direction}", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, LEFT_EYE_COLOR, 2)
                cv2.putText(display_frame, f"Right: {right_direction}", (10, 90), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, RIGHT_EYE_COLOR, 2)
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
            # print(f"帧处理发生未知错误: {e}")
            continue
    
    # 释放摄像头
    cap.release()
    cv2.destroyAllWindows()
    print("眼动追踪已停止")

if __name__ == "__main__":
    print("开始实时眼动追踪...")
    while True:
        try:
            real_time_gaze_tracking()
        except Exception as e:
            print(f"发生异常: {e}")
            continue