import cv2
from ultralytics import YOLO
from ultralytics.utils import LOGGER
LOGGER.setLevel('ERROR')
model = YOLO('YOLOv10x.pt')

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("无法打开摄像头")
    exit()
    
last_detected_label = None
while True:
    ret, frame = cap.read()
    if not ret:
        print("无法读取帧")
        break
    frame = cv2.flip(frame, 1) # 水平翻转
    results = model(frame, stream=True)
    current_detected_label = None
    for result in results:
        boxes = result.boxes  # 边界框
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # 坐标
            conf = box.conf[0]  # 置信度
            cls = int(box.cls[0])  # 类别索引
            label = f"{model.names[cls]} {conf:.2f}"
            current_detected_label = model.names[cls]
            # 边界框和标签
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    if current_detected_label and conf>0.9 and current_detected_label != last_detected_label and current_detected_label != 'no_gesture':
        print(f"检测到手势：{current_detected_label}")
        last_detected_label = current_detected_label
    cv2.imshow('YOLO Real-Time Gesture Recognition', frame)
    # q退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
