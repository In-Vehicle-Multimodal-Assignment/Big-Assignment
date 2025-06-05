let isAnimationShown = true;
let isLoggedIn = false; // 用户登录状态标记

document.getElementById("toggle-view").onclick = function () {
  if (!isLoggedIn) {
    // 弹出登录框而不是切换视图
    document.getElementById("login-modal").style.display = "flex";
    return;
  }

  const animationArea = document.getElementById("animation-area");
  const logArea = document.getElementById("log-area");

  if (isAnimationShown) {
    animationArea.style.display = "none";
    logArea.style.display = "block";
  } else {
    animationArea.style.display = "flex";
    logArea.style.display = "none";
  }

  isAnimationShown = !isAnimationShown;
};

// 登录按钮逻辑
document.getElementById("login-btn").onclick = function () {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;

  fetch("admins.json")
    .then((res) => res.json())
    .then((admins) => {
      const match = admins.find(
        (admin) => admin.username === username && admin.password === password
      );

      if (match) {
        isLoggedIn = true;
        document.getElementById("login-modal").style.display = "none";

        // 显示日志区
        document.getElementById("animation-area").style.display = "none";
        document.getElementById("log-area").style.display = "block";
        isAnimationShown = false;
      } else {
        document.getElementById("login-error").innerText = "用户名或密码错误";
        setTimeout(() => {
          document.getElementById("login-modal").style.display = "none";
        }, 700);  // 登录失败也关闭框
      }
    })
    .catch((err) => {
      document.getElementById("login-error").innerText = "加载用户信息失败";
      document.getElementById("login-modal").style.display = "none"; // 出错也关闭框
      console.error(err);
    });
};



// 模拟多模态融合执行结果
// 数字与操作映射
function mapResultCode(code) {
  switch (code) {  
    case 2:
      return { type: "fatigue", message: "驾驶员疲劳，请注意休息" };
    case 3:
      return { type: "ac", message: "打开空调" };
    case 4:
      return { type: "music", message: "播放音乐" };
    default:
      return { type: "unknown", message: "未知操作" };
  }
}

// 更新融合执行结果
function updateFusionResult(type, message) {
  const fusionContent = document.getElementById("fusion-content");
  const icons = document.querySelectorAll(".icon");

  // 清空内容
  fusionContent.innerHTML = '';

  // 重置所有图标状态
  icons.forEach(icon => {
    icon.classList.remove("active", "fatigue-active");
  });

  // 激活目标图标并更新内容
  if (type === "ac") {
    const iconAC = document.getElementById("icon-ac");
    iconAC.classList.add("active");
    fusionContent.innerHTML = `<div>🚗 已执行：<strong>${message}</strong></div>`;
  } else if (type === "fatigue") {
    const iconFatigue = document.getElementById("icon-fatigue");
    iconFatigue.classList.add("fatigue-active");
    document.getElementById("alert-content").innerText = message;
  } else if (type === "music") {
    const iconMUSIC = document.getElementById("icon-music");
    iconMUSIC.classList.add("active");
    fusionContent.innerHTML = `<div>🎵 已执行：<strong>${message}</strong></div>`;
  }else {
    fusionContent.innerHTML = `<div>⚠️ ${message}</div>`;
  }

  // 添加日志
  const logList = document.getElementById("log-list");
  const li = document.createElement("li");
  li.textContent = `执行 ${message}`;
  logList.appendChild(li);
}

// 获取后端数据并触发更新
function fetchFusionResult() {
  fetch('http://localhost:5001/fusion-result') 
    .then(response => response.json())
    .then(data => {
      let result;
      if (typeof data.code !== 'undefined') {
        // 返回的是数字
        result = mapResultCode(data.code);
      } else {
        // 结构化返回 { type: "", message: "" }
        result = data;
      }
      updateFusionResult(result.type, result.message);
    })
    .catch(error => {
      console.error('获取融合结果失败:', error);
    });
}


//语音
const voiceBtn = document.getElementById("toggle-voice");
const animationArea = document.getElementById("icon-voice");

voiceBtn.onclick = () => {
  animationArea.style.backgroundColor = "yellow"; // 开始录音，变黄色

  fetch("http://localhost:5000/start-record", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ flag: true })  // 向后端发送标志位
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        animationArea.style.backgroundColor = "green"; // 录音结束变绿色

        setTimeout(() => {
          animationArea.style.backgroundColor = "#eee"; // 恢复原色
        }, 1000);
      } else {
        animationArea.style.backgroundColor = "#e57373"; // 出错提示
        setTimeout(() => {
          animationArea.style.backgroundColor = "#eee"; // 恢复原色
        }, 1000);
        console.error("后端返回失败状态");
      }
    })
    .catch(err => {
      console.error(err);
      animationArea.style.backgroundColor = "#e57373"; // 出错提示
    });
};

// 模拟指令执行（调试用）
//setTimeout(() => {
//  updateFusionResult("ac", "空调打开 22°C");
//}, 2000);

//setTimeout(() => {
//  updateFusionResult("fatigue", "警告：检测到疲劳驾驶！");
//}, 5000);

// 启动定时获取
window.onload = function () {
  fetchFusionResult(); // 页面加载立即执行一次
  setInterval(fetchFusionResult, 3000); // 每5秒执行一次
};
