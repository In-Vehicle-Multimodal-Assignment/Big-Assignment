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

  if (username === "admin" && password === "1234") {
    isLoggedIn = true;
    document.getElementById("login-modal").style.display = "none";

    // 自动切换到日志视图
    document.getElementById("animation-area").style.display = "none";
    document.getElementById("log-area").style.display = "block";
    isAnimationShown = false;
  } else {
    document.getElementById("login-error").innerText = "用户名或密码错误";
  }
};


// 模拟多模态融合执行结果
function updateFusionResult(type, message) {
  const fusionContent = document.getElementById("fusion-content");
  const icons = document.querySelectorAll(".icon");

  fusionContent.innerHTML = ''; // 清空内容

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
  }

  // 添加日志
  const logList = document.getElementById("log-list");
  const li = document.createElement("li");
  li.textContent = `执行 ${message}`;
  logList.appendChild(li);
}


// 模拟指令执行（调试用）
setTimeout(() => {
  updateFusionResult("ac", "空调打开 22°C");
}, 2000);

setTimeout(() => {
  updateFusionResult("fatigue", "警告：检测到疲劳驾驶！");
}, 5000);


