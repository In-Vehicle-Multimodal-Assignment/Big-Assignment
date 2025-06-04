import pyaudio
import wave
from transformers import pipeline

# 音频参数配置
framerate = 16000  # 采样率
NUM_SAMPLES = 2000  # 每个缓冲区的样本数
channels = 1       # 声道数（单声道）
sampwidth = 2      # 样本宽度（16位）
TIME = 10          # 时间基数

def save_wave_file(filename, data):
    """保存音频为WAV文件"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(b"".join(data))

def record(f, time=5):
    """录音函数"""
    p = pyaudio.PyAudio()
    
    # 列出所有可用的输入设备
    print("\n可用输入设备：")
    input_devices = []
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info["maxInputChannels"] > 0:
            print(f"设备ID {i}: {dev_info['name']} (输入声道: {dev_info['maxInputChannels']})")
            input_devices.append(i)
    
    if not input_devices:
        print("未找到可用的输入设备！")
        return
    
    # 自动选择第一个可用的输入设备
    input_device_index = input_devices[0]
    print(f"\n正在使用设备ID {input_device_index}")
    
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=framerate,
            input=True,
            frames_per_buffer=NUM_SAMPLES,
            input_device_index=input_device_index
        )
        
        my_buf = []
        print(f"\n录音中({time}秒)...")
        for _ in range(int(TIME * time)):
            audio_data = stream.read(NUM_SAMPLES)
            my_buf.append(audio_data)
            print(".", end="", flush=True)
        
        save_wave_file(f, my_buf)
        print(f"\n录音已保存为: {f}")
        
    except Exception as e:
        print(f"\n录音出错: {str(e)}")
    finally:
        stream.close()
        p.terminate()

# 录音
# record("test1.wav", time=5)

# 语音识别
try:
    print("\n开始语音识别...")
    transcriber = pipeline(
        "automatic-speech-recognition",
        model="./model",
        device='cuda'
    )
    
    transcriber.model.config.forced_decoder_ids = (
        transcriber.tokenizer.get_decoder_prompt_ids(
            language="zh",
            task="transcribe"
        )
    )
    flag = True
    while True:
      if flag:
        transcription = transcriber("test.wav")
        flag = False
      else:
        transcription = transcriber("test1.wav")
        flag = True
        
      print("\n识别结果:", transcription)
except Exception as e:
    print(f"\n语音识别出错: {str(e)}")