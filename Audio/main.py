from pathlib import Path
import wave
import pyaudio
from transformers import pipeline
import json
import requests

# 音频参数配置
framerate = 16000  # 采样率
NUM_SAMPLES = 2000  # 每个缓冲区的样本数
channels = 1       # 声道数（单声道）
sampwidth = 2      # 样本宽度（16位）
TIME = 10          # 时间基数

transcriber = None
p = None
input_device_index = None

# 获取model目录的绝对路径
model_path = str(Path(__file__).parent / "model")  # 自动处理路径分隔符

def save_wave_file(filename, data):
    """保存音频为WAV文件"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(b"".join(data))

def record(f, time=3):
    global p, input_device_index
    try:
        script_dir = Path(__file__).parent
        wav_path = script_dir / f

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

        save_wave_file(str(wav_path), my_buf)
        #print(f"\n录音已保存为: {f}")
        
    except Exception as e:
        print(f"\n录音出错: {str(e)}")
    finally:
        stream.stop_stream()
        stream.close()

# 识别指令
def recognized_command(command):

    """处理识别到的指令"""

    if command == "确认":
        return 1
    elif command == "拒绝":
        return 2
    elif command == "打开空调":
        return 3
    elif command == "打开音乐":
        return 4
    elif command == "已注意道路":
        return 5
    else:
        return 0

# 工具启动
def audio_start():
    global transcriber, p, input_device_index
    transcriber = pipeline(
        "automatic-speech-recognition",
        model=model_path,
        device='cpu'
    )
    transcriber.model.config.forced_decoder_ids = (
        transcriber.tokenizer.get_decoder_prompt_ids(
            language="zh",
            task="transcribe"
        )
    )

    p = pyaudio.PyAudio()
    input_devices = []
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info["maxInputChannels"] > 0:
            input_devices.append(i)
    input_device_index = input_devices[0]
    print(f"正在使用设备ID {input_device_index}")

# 音频识别函数
def audio_recognition():
    global transcriber
    wav_file = Path(__file__).parent / "audio.wav"
    record("audio.wav",time=3)
    transcription = transcriber(str(wav_file))
    print("识别结果:", transcription["text"])
    url = "https://api.siliconflow.cn/v1/chat/completions"
    payload = {
        "model": "THUDM/GLM-4-9B-0414",
        "messages": [
            {
                "role": "user",
                "content": "我有以下五种指令：确认，拒绝，打开空调，打开音乐，已注意道路。下面是用户说的一句话:" + transcription["text"] + "。请你理解意图，分析出是哪种指令，输出指令名字即可，如果都不是就输出一个字无。切记不要输出多余的字:"
            }
        ],
        "stream": False,
        "max_tokens": 512,
        "thinking_budget": 4096,
        "response_format": {"type": "text"},
        "tools": [
            {
                "type": "function",
                "function": {
                    "description": "<string>",
                    "name": "<string>",
                    "parameters": {},
                    "strict": False
                }
            }
        ]
    }
    print(payload["messages"][0]["content"])
    headers = {
        "Authorization": "Bearer sk-ddlgzbwkuxqojvfxpyylmwhcgnyrvxswoplcfekdzffsclmq",
        "Content-Type": "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    response_data = json.loads(response.text)
    content = response_data["choices"][0]["message"]["content"]
    content = content.strip().replace("\\n", "\n")
    return recognized_command(content)