let isAnimationShown = true;
let isLoggedIn = false;
let currentUser = null;
let isAdmin = false;

// 页面加载即弹出登录
document.addEventListener("DOMContentLoaded", function () {
  document.getElementById("login-modal").style.display = "flex";
});

// 切换视图按钮逻辑
document.getElementById("toggle-view").onclick = function () {
  if (!isLoggedIn) {
    document.getElementById("login-modal").style.display = "flex";
    return;
  }

  // 检查权限：非管理员不能切换到日志视图
  if (isAnimationShown && !isAdmin) {
    alert("权限不足，只有管理员可以查看操作日志！");
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

document.getElementById("login-btn").onclick = function () {
  const username = document.getElementById("username").value.trim();
  if (!username) {
    showLoginError("请输入用户名");
    return;
  }

  fetch("http://localhost:5000/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        currentUser = username;
        isAdmin = data.is_admin;
        finishLogin();
      } else {
        showLoginError(data.message || "登录失败");
      }
    })
    .catch((err) => {
      showLoginError("请求登录接口失败");
      console.error(err);
    });
};



function finishLogin() {
  isLoggedIn = true;
  document.getElementById("login-modal").style.display = "none";

  // 显示动画区域
  document.getElementById("animation-area").style.display = "flex";
  document.getElementById("log-area").style.display = "none";
  isAnimationShown = true;

  // 显示用户名
  const userDisplay = document.getElementById("user-display");
  userDisplay.textContent = `当前用户：${currentUser}${isAdmin ? "（管理员）" : "（普通用户）"}`;

  fetchGestureResult(); 
  fetchVoiceResult();
  fetchHeadResult();
  fetchEyeResult();
  // 错开时间启动，每个初始延迟不同
  setTimeout(() => {
    fetchGestureResult();
    setInterval(fetchGestureResult, 1000); // 每4秒轮询
  }, 0); // 立即执行

  setTimeout(() => {
    fetchVoiceResult();
    setInterval(fetchVoiceResult, 1000); // 每4秒轮询
  }, 200); // 延迟1秒启动

  setTimeout(() => {
    fetchHeadResult();
    setInterval(fetchHeadResult, 1000); // 每4秒轮询
  }, 400); // 延迟2秒启动

  setTimeout(() => {
    fetchEyeResult();
    setInterval(fetchEyeResult, 1000); // 每4秒轮询
  }, 800); // 延迟3秒启动
  }

function showLoginError(message) {
  document.getElementById("login-error").innerText = message;
  setTimeout(() => {
    document.getElementById("login-modal").style.display = "none";
  }, 1000);
}



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
    case 5:
      return { type: "fatigue_r", message: "驾驶员状态正常" };
    case 6:
      return { type: "ac_r", message: "关闭空调" };
    case 7:
      return { type: "music_r", message: "停止播放音乐" };
    default:
      return { type: "unknown", message: "未知操作" };
  }
}

// 更新融合执行结果
function updateFusionResult(type, message) {
  const fusionContent = document.getElementById("fusion-content");

  // 清空内容
  fusionContent.innerHTML = '';


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
  } else if (type === "ac_r") {
    const iconAC = document.getElementById("icon-ac");
    iconAC.classList.remove("active");
    fusionContent.innerHTML = `<div>🚗 已执行：<strong>${message}</strong></div>`;
  } else if (type === "fatigue_r") {
    const iconFatigue = document.getElementById("icon-fatigue");
    iconFatigue.classList.remove("fatigue-active");
    document.getElementById("alert-content").innerText = message;
  } else if (type === "music_r") {
    const iconMUSIC = document.getElementById("icon-music");
    iconMUSIC.classList.remove("active");
    fusionContent.innerHTML = `<div>🎵 已执行：<strong>${message}</strong></div>`;
  }
  else {
    fusionContent.innerHTML = `<div>⚠️ ${message}</div>`;
  }

  // 添加日志
  const logList = document.getElementById("log-list");
  const li = document.createElement("li");
  li.textContent = `执行 ${message}`;
  logList.appendChild(li);
}

// 获取后端数据并触发更新
function fetchGestureResult() {
  fetch('http://localhost:5000/gesture-result') 
    .then(response => response.json())
    .then(data => {
      let result;
      if (typeof data.code !== 'undefined') {
        // 返回的是数字
        result = mapResultCode(data.code);
      } 
      updateFusionResult(result.type, result.message);
    })
    .catch(error => {
      console.error('获取结果失败:', error);
    });
}

function fetchVoiceResult() {
  fetch('http://localhost:5000/voice-result') 
    .then(response => response.json())
    .then(data => {
      let result;
      if (typeof data.code !== 'undefined') {
        // 返回的是数字
        result = mapResultCode(data.code);
      } 
      updateFusionResult(result.type, result.message);
    })
    .catch(error => {
      console.error('获取结果失败:', error);
    });
}

function fetchHeadResult() {
  fetch('http://localhost:5000/head-result') 
    .then(response => response.json())
    .then(data => {
      let result;
      if (typeof data.code !== 'undefined') {
        // 返回的是数字
        result = mapResultCode(data.code);
      } 
      updateFusionResult(result.type, result.message);
    })
    .catch(error => {
      console.error('获取结果失败:', error);
    });
}

function fetchEyeResult() {
  fetch('http://localhost:5000/eye-result') 
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
      console.error('获取结果失败:', error);
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


