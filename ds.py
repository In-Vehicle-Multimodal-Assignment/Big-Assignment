
api_key="sk-ddlgzbwkuxqojvfxpyylmwhcgnyrvxswoplcfekdzffsclmq"
import json
import requests
url = "https://api.siliconflow.cn/v1/chat/completions"
payload = {
    "model": "Qwen/Qwen3-8B",
    "messages": [
        {
            "role": "user",
            "content": "I am Jody!"
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

headers = {
    "Authorization": "Bearer sk-ddlgzbwkuxqojvfxpyylmwhcgnyrvxswoplcfekdzffsclmq",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

response_data = json.loads(response.text)
content = response_data["choices"][0]["message"]["content"]
content = content.strip().replace("\\n", "\n")
print(content)

payload["messages"].append({
    "role": "assistant",
    "content": content
})
payload["messages"].append({
    "role": "user",
    "content": "What is my name?"
})

response = requests.request("POST", url, json=payload, headers=headers)
response_data = json.loads(response.text)
content = response_data["choices"][0]["message"]["content"]
content = content.strip().replace("\\n", "\n")

print(content)