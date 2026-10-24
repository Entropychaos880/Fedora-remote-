/**
 * app.js - High-performance Trackpad Client with Gesture Recognition & Haptic Feedback
 */

(() => {
  // DOM Elements
  const trackpad = document.getElementById("trackpad");
  const touchRing = document.getElementById("touchRing");
  const dragBadge = document.getElementById("dragBadge");
  const gestureGuide = document.getElementById("gestureGuide");
  const scrollRail = document.getElementById("scrollRail");

  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");
  const statusPing = document.getElementById("statusPing");

  const btnLeftClick = document.getElementById("btnLeftClick");
  const btnMiddleClick = document.getElementById("btnMiddleClick");
  const btnRightClick = document.getElementById("btnRightClick");

  // Drawers, Modals & PiP
  const btnPipToggle = document.getElementById("btnPipToggle");
  const pipContainer = document.getElementById("pipContainer");
  const pipHeader = document.getElementById("pipHeader");
  const pipFps = document.getElementById("pipFps");
  const btnPipProfile = document.getElementById("btnPipProfile");
  const btnPipPopout = document.getElementById("btnPipPopout");
  const btnPipSize = document.getElementById("btnPipSize");
  const btnPipClose = document.getElementById("btnPipClose");
  const pipCanvas = document.getElementById("pipCanvas");
  const pipLoading = document.getElementById("pipLoading");
  const pipHiddenVideo = document.getElementById("pipHiddenVideo");
  const pipCtx = pipCanvas ? pipCanvas.getContext("2d") : null;

  const mediaDrawer = document.getElementById("mediaDrawer");
  const keyboardDrawer = document.getElementById("keyboardDrawer");
  const settingsModal = document.getElementById("settingsModal");

  const btnMedia = document.getElementById("btnMedia");
  const btnKeyboard = document.getElementById("btnKeyboard");
  const btnFullscreen = document.getElementById("btnFullscreen");
  const btnSettings = document.getElementById("btnSettings");

  const closeMediaDrawer = document.getElementById("closeMediaDrawer");
  const closeKeyboardDrawer = document.getElementById("closeKeyboardDrawer");
  const closeSettingsModal = document.getElementById("closeSettingsModal");

  const typeInput = document.getElementById("typeInput");
  const btnClearInput = document.getElementById("btnClearInput");
  const btnSendText = document.getElementById("btnSendText");
  const btnSendEnter = document.getElementById("btnSendEnter");
  const chipAutoEnter = document.getElementById("chipAutoEnter");

  // Settings Elements
  const rangeSensitivity = document.getElementById("rangeSensitivity");
  const valSensitivity = document.getElementById("valSensitivity");
  const rangeScroll = document.getElementById("rangeScroll");
  const valScroll = document.getElementById("valScroll");
  const toggleNaturalScroll = document.getElementById("toggleNaturalScroll");
  const toggleAcceleration = document.getElementById("toggleAcceleration");
  const toggleHaptics = document.getElementById("toggleHaptics");

  // Persistent Configuration
  const config = {
    sensitivity: parseFloat(localStorage.getItem("tp_sensitivity") || "1.4"),
    scrollSpeed: parseFloat(localStorage.getItem("tp_scrollSpeed") || "1.0"),
    naturalScroll: localStorage.getItem("tp_naturalScroll") !== "false",
    acceleration: localStorage.getItem("tp_acceleration") !== "false",
    haptics: localStorage.getItem("tp_haptics") !== "false",
  };

  // Sync settings UI
  rangeSensitivity.value = config.sensitivity;
  valSensitivity.textContent = `${config.sensitivity.toFixed(1)}x`;
  rangeScroll.value = config.scrollSpeed;
  valScroll.textContent = `${config.scrollSpeed.toFixed(1)}x`;
  toggleNaturalScroll.checked = config.naturalScroll;
  toggleAcceleration.checked = config.acceleration;
  toggleHaptics.checked = config.haptics;

  // Settings Event Handlers
  rangeSensitivity.addEventListener("input", (e) => {
    config.sensitivity = parseFloat(e.target.value);
    valSensitivity.textContent = `${config.sensitivity.toFixed(1)}x`;
    localStorage.setItem("tp_sensitivity", config.sensitivity);
  });

  rangeScroll.addEventListener("input", (e) => {
    config.scrollSpeed = parseFloat(e.target.value);
    valScroll.textContent = `${config.scrollSpeed.toFixed(1)}x`;
    localStorage.setItem("tp_scrollSpeed", config.scrollSpeed);
  });

  toggleNaturalScroll.addEventListener("change", (e) => {
    config.naturalScroll = e.target.checked;
    localStorage.setItem("tp_naturalScroll", config.naturalScroll);
  });

  toggleAcceleration.addEventListener("change", (e) => {
    config.acceleration = e.target.checked;
    localStorage.setItem("tp_acceleration", config.acceleration);
  });

  toggleHaptics.addEventListener("change", (e) => {
    config.haptics = e.target.checked;
    localStorage.setItem("tp_haptics", config.haptics);
  });

  // Haptic Feedback Helper
  function vibrate(pattern) {
    if (config.haptics && "vibrate" in navigator) {
      try {
        navigator.vibrate(pattern);
      } catch (err) {}
    }
  }

  // ================= Connection & Multi-Endpoint Manager =================
  const statusIndicator = document.getElementById("statusIndicator");
  const statusHostBadge = document.getElementById("statusHostBadge");
  const connectionModal = document.getElementById("connectionModal");
  const closeConnectionModal = document.getElementById("closeConnectionModal");
  const btnOpenConnManager = document.getElementById("btnOpenConnManager");
  const connEndpointsList = document.getElementById("connEndpointsList");
  const toggleAutoFallback = document.getElementById("toggleAutoFallback");
  const inputCustomHost = document.getElementById("inputCustomHost");
  const btnAddEndpoint = document.getElementById("btnAddEndpoint");
  const settingsCurrentHostDesc = document.getElementById("settingsCurrentHostDesc");

  const DEFAULT_ENDPOINTS = [
    { host: "100.98.255.122:8080", desc: "Tailscale VPN (Remote / Anywhere)", ip: "100.98.255.122" },
    { host: "10.42.0.1:8080", desc: "Laptop Wi-Fi Hotspot (Direct)", ip: "10.42.0.1" },
    { host: "192.168.0.102:8080", desc: "Ethernet / Home LAN", ip: "192.168.0.102" }
  ];

  function loadKnownEndpoints() {
    try {
      const stored = localStorage.getItem("tp_known_endpoints");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {}

    const initial = [...DEFAULT_ENDPOINTS];
    if (window.location.host && !initial.some(e => e.host === window.location.host)) {
      initial.unshift({ host: window.location.host, desc: "Current Browser Host", ip: window.location.hostname });
    }
    return initial;
  }

  function saveKnownEndpoints(endpoints) {
    try {
      localStorage.setItem("tp_known_endpoints", JSON.stringify(endpoints));
    } catch (e) {}
  }

  let knownEndpoints = loadKnownEndpoints();
  // Always connect to the host that served the page to avoid cross-IP SSL blocks!
  let activeHost = (window.location.host && window.location.host.includes(":")) 
    ? window.location.host 
    : (window.location.host ? `${window.location.host}:8080` : (localStorage.getItem("tp_active_host") || "10.42.0.1:8080"));
  localStorage.setItem("tp_active_host", activeHost);
  // Default autoFallback to false: hopping between different IPs causes SSL cert blocks on mobile browsers
  let autoFallback = localStorage.getItem("tp_auto_fallback") === "true";
  let fallbackIndex = knownEndpoints.findIndex(e => e.host === activeHost);
  if (fallbackIndex < 0) fallbackIndex = 0;
  let connectTimeoutTimer = null;

  function getHostShortLabel(host) {
    if (!host) return "Network";
    if (host.startsWith("100.") || host.includes("tailscale")) return "Tailscale";
    if (host.startsWith("10.42.") || host.includes("hotspot")) return "Hotspot";
    if (host.startsWith("192.168.") || host.startsWith("10.") || host.startsWith("172.")) return "Wi-Fi";
    if (host.includes("localhost") || host.startsWith("127.")) return "Local";
    return host.split(":")[0];
  }

  function updateStatusHostBadge() {
    if (statusHostBadge) {
      statusHostBadge.textContent = getHostShortLabel(activeHost);
      statusHostBadge.title = `Connected to ${activeHost}`;
    }
    if (settingsCurrentHostDesc) {
      settingsCurrentHostDesc.textContent = `${getHostShortLabel(activeHost)} (${activeHost})`;
    }
  }

  function handleServerEndpoints(msg) {
    if (!msg || !Array.isArray(msg.endpoints)) return;
    let changed = false;
    msg.endpoints.forEach((ep) => {
      if (!ep.host) return;
      const existing = knownEndpoints.find(k => k.host === ep.host);
      if (!existing) {
        knownEndpoints.push(ep);
        changed = true;
      } else if (ep.desc && existing.desc !== ep.desc) {
        existing.desc = ep.desc;
        changed = true;
      }
    });
    if (changed) {
      saveKnownEndpoints(knownEndpoints);
      renderEndpointsList();
    }
  }

  // ================= WebSocket Connection =================
  let socket = null;
  let isConnected = false;
  let reconnectTimer = null;
  let pingInterval = null;

  function connectWebSocket(customHost) {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      try { socket.close(); } catch (err) {}
    }

    if (customHost) {
      activeHost = customHost;
      localStorage.setItem("tp_active_host", activeHost);
      fallbackIndex = knownEndpoints.findIndex(e => e.host === activeHost);
      if (fallbackIndex < 0) fallbackIndex = 0;
    }

    const hostToTry = activeHost;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${hostToTry}/ws`;

    updateStatusHostBadge();
    statusText.textContent = `Connecting (${getHostShortLabel(hostToTry)})...`;
    statusDot.className = "status-dot disconnected";

    if (connectTimeoutTimer) {
      clearTimeout(connectTimeoutTimer);
      connectTimeoutTimer = null;
    }

    // Auto-fallback: If endpoint fails to respond within 2.5s, try next known endpoint
    if (autoFallback && knownEndpoints.length > 1) {
      connectTimeoutTimer = setTimeout(() => {
        if (!isConnected) {
          console.warn(`Connection timeout on ${hostToTry}, switching to fallback endpoint...`);
          try { socket.close(); } catch (err) {}
          cycleFallbackEndpoint();
        }
      }, 2500);
    }

    try {
      socket = new WebSocket(wsUrl);
    } catch (e) {
      scheduleReconnect();
      return;
    }

    socket.onopen = () => {
      if (connectTimeoutTimer) {
        clearTimeout(connectTimeoutTimer);
        connectTimeoutTimer = null;
      }
      isConnected = true;
      activeHost = hostToTry;
      localStorage.setItem("tp_active_host", activeHost);
      updateStatusHostBadge();
      statusText.textContent = "Connected";
      statusDot.className = "status-dot connected";
      vibrate(25);
      startPing();
      if (isPipActive) {
        sendCommand({ type: "pip_start", profile: currentProfile });
      }
      renderEndpointsList();
    };

    socket.onmessage = (event) => {
      if (event.data instanceof Blob || event.data instanceof ArrayBuffer) {
        handleScreenFrame(event.data);
        return;
      }
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "pong") {
          const latency = Math.round(performance.now() - msg.t);
          statusPing.textContent = `${latency}ms`;
        } else if (msg.type === "audio_state") {
          updateAudioStateUI(msg);
        } else if (msg.type === "sleep_timer_tick") {
          updateSleepTimerUI(msg);
        } else if (msg.type === "server_endpoints") {
          handleServerEndpoints(msg);
        } else if (msg.type === "paste_image_ack") {
          if (msg.success) {
            vibrate([20, 30, 20]);
            showToast("✓ Screenshot pasted to laptop (Ctrl+V)!");
          } else {
            alert("Failed to paste image: " + (msg.error || "Unknown error"));
          }
        }
      } catch (e) {}
    };

    socket.onclose = () => {
      isConnected = false;
      statusText.textContent = "Disconnected";
      statusDot.className = "status-dot disconnected";
      statusPing.textContent = "--ms";
      if (isPipActive && pipLoading) {
        pipLoading.classList.remove("hidden");
        pipLoading.textContent = "Reconnecting screen...";
      }
      stopPing();
      scheduleReconnect();
    };

    socket.onerror = () => {
      if (socket) socket.close();
    };
  }

  function cycleFallbackEndpoint() {
    if (!autoFallback || knownEndpoints.length <= 1) return;
    fallbackIndex = (fallbackIndex + 1) % knownEndpoints.length;
    const nextEp = knownEndpoints[fallbackIndex];
    if (nextEp && nextEp.host) {
      activeHost = nextEp.host;
      localStorage.setItem("tp_active_host", activeHost);
      connectWebSocket();
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      if (autoFallback && !isConnected) {
        cycleFallbackEndpoint();
      } else {
        connectWebSocket();
      }
    }, 1500);
  }

  // ================= Connection Modal UI =================
  function openConnectionModal() {
    vibrate(15);
    renderEndpointsList();
    if (toggleAutoFallback) {
      toggleAutoFallback.checked = autoFallback;
    }
    if (connectionModal) connectionModal.classList.add("open");
  }

  function closeConnModal() {
    if (connectionModal) connectionModal.classList.remove("open");
  }

  function renderEndpointsList() {
    if (!connEndpointsList) return;
    connEndpointsList.innerHTML = "";

    knownEndpoints.forEach((ep) => {
      const isCurrent = ep.host === activeHost;
      const item = document.createElement("div");
      item.className = `conn-endpoint-item ${isCurrent ? "active" : ""}`;

      const info = document.createElement("div");
      info.className = "conn-endpoint-info";

      const name = document.createElement("div");
      name.className = "conn-endpoint-name";
      name.textContent = ep.desc || getHostShortLabel(ep.host);

      const host = document.createElement("div");
      host.className = "conn-endpoint-host";
      host.textContent = ep.host;

      info.appendChild(name);
      info.appendChild(host);

      const actions = document.createElement("div");
      actions.className = "conn-endpoint-actions";

      if (isCurrent && isConnected) {
        const badge = document.createElement("span");
        badge.className = "btn-conn-action active-badge";
        badge.textContent = "✓ Connected";
        actions.appendChild(badge);
      } else {
        const btnConnect = document.createElement("button");
        btnConnect.className = `btn-conn-action ${isCurrent ? "" : "primary"}`;
        btnConnect.textContent = isCurrent ? "Retry" : "Connect";
        btnConnect.addEventListener("click", () => {
          vibrate(15);
          connectWebSocket(ep.host);
          closeConnModal();
        });
        actions.appendChild(btnConnect);
      }

      // Quick browser redirect option if needed
      if (!isCurrent) {
        const btnOpen = document.createElement("button");
        btnOpen.className = "btn-conn-action";
        btnOpen.textContent = "↗ URL";
        btnOpen.title = `Switch browser page to https://${ep.host}`;
        btnOpen.addEventListener("click", () => {
          window.location.href = `https://${ep.host}`;
        });
        actions.appendChild(btnOpen);
      }

      item.appendChild(info);
      item.appendChild(actions);
      connEndpointsList.appendChild(item);
    });
  }

  if (statusIndicator) {
    statusIndicator.addEventListener("click", openConnectionModal);
  }
  if (btnOpenConnManager) {
    btnOpenConnManager.addEventListener("click", () => {
      if (settingsModal) settingsModal.classList.remove("open");
      openConnectionModal();
    });
  }
  if (closeConnectionModal) {
    closeConnectionModal.addEventListener("click", closeConnModal);
  }
  if (connectionModal) {
    connectionModal.addEventListener("click", (e) => {
      if (e.target === connectionModal) closeConnModal();
    });
  }
  if (toggleAutoFallback) {
    toggleAutoFallback.addEventListener("change", (e) => {
      autoFallback = e.target.checked;
      localStorage.setItem("tp_auto_fallback", autoFallback);
    });
  }
  if (btnAddEndpoint && inputCustomHost) {
    btnAddEndpoint.addEventListener("click", () => {
      let val = inputCustomHost.value.trim().replace(/^https?:\/\//, "").replace(/\/.*$/, "");
      if (!val) return;
      if (!val.includes(":")) val += ":8080";
      if (!knownEndpoints.some(e => e.host === val)) {
        knownEndpoints.push({ host: val, desc: "Custom Endpoint", ip: val.split(":")[0] });
        saveKnownEndpoints(knownEndpoints);
        renderEndpointsList();
      }
      inputCustomHost.value = "";
      connectWebSocket(val);
      closeConnModal();
    });
  }

  function startPing() {
    stopPing();
    pingInterval = setInterval(() => {
      if (isConnected && socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "ping", t: performance.now() }));
      }
    }, 2000);
  }

  function stopPing() {
    if (pingInterval) {
      clearInterval(pingInterval);
      pingInterval = null;
    }
  }

  function sendCommand(data) {
    if (isConnected && socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data));
    }
  }

  // ================= Gesture & Touch Controller =================
  let activeTouches = 0;
  let touchStartTime = 0;
  let lastX = 0;
  let lastY = 0;
  let startX = 0;
  let startY = 0;
  let totalMoveDistance = 0;

  // Two finger scrolling tracking
  let lastMidX = 0;
  let lastMidY = 0;

  // Three finger gesture tracking
  let threeFingerStartX = 0;
  let threeFingerStartY = 0;
  let threeFingerTriggered = false;

  // Tap-and-drag lock state
  let lastTapReleaseTime = 0;
  let isDragLocked = false;

  // Hide gesture guide after first touch
  let guideDismissed = false;

  function applyPointerAcceleration(dx, dy) {
    let speed = Math.sqrt(dx * dx + dy * dy);
    let factor = config.sensitivity;

    if (config.acceleration) {
      // Smooth dynamic acceleration curve for fast flicks across monitors
      if (speed > 18) {
        factor *= 1.8;
      } else if (speed > 10) {
        factor *= 1.4;
      } else if (speed > 5) {
        factor *= 1.15;
      }
    }
    return { dx: dx * factor, dy: dy * factor };
  }

  trackpad.addEventListener("touchstart", (e) => {
    e.preventDefault();
    activeTouches = e.touches.length;
    touchStartTime = performance.now();
    totalMoveDistance = 0;

    if (!guideDismissed && gestureGuide) {
      gestureGuide.style.opacity = "0";
      guideDismissed = true;
    }

    if (activeTouches === 1) {
      const touch = e.touches[0];
      const rect = trackpad.getBoundingClientRect();
      const localX = touch.clientX - rect.left;
      const localY = touch.clientY - rect.top;

      startX = touch.clientX;
      startY = touch.clientY;
      lastX = touch.clientX;
      lastY = touch.clientY;

      // Position visual touch ring
      touchRing.style.left = `${localX}px`;
      touchRing.style.top = `${localY}px`;
      touchRing.classList.add("active");

      // Check for double-tap hold to engage Drag Lock
      const timeSinceLastTap = touchStartTime - lastTapReleaseTime;
      if (timeSinceLastTap < 280) {
        isDragLocked = true;
        dragBadge.classList.add("visible");
        sendCommand({ type: "btn_down", button: "left" });
        vibrate([20, 30, 20]);
      }
    } else if (activeTouches === 2) {
      // 2 fingers on screen: prepare for two-finger scroll
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      lastMidX = (t1.clientX + t2.clientX) / 2;
      lastMidY = (t1.clientY + t2.clientY) / 2;
      touchRing.classList.remove("active");
    } else if (activeTouches >= 3) {
      // 3 or more fingers: prepare for 3-finger desktop gestures
      touchRing.classList.remove("active");
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      const t3 = e.touches[2];
      threeFingerStartX = (t1.clientX + t2.clientX + t3.clientX) / 3;
      threeFingerStartY = (t1.clientY + t2.clientY + t3.clientY) / 3;
      threeFingerTriggered = false;
    }
  }, { passive: false });

  trackpad.addEventListener("touchmove", (e) => {
    e.preventDefault();
    const count = e.touches.length;

    if (count === 1) {
      const touch = e.touches[0];
      const rawDx = touch.clientX - lastX;
      const rawDy = touch.clientY - lastY;

      lastX = touch.clientX;
      lastY = touch.clientY;
      totalMoveDistance += Math.abs(rawDx) + Math.abs(rawDy);

      // Move visual touch ring
      const rect = trackpad.getBoundingClientRect();
      touchRing.style.left = `${touch.clientX - rect.left}px`;
      touchRing.style.top = `${touch.clientY - rect.top}px`;

      // Calculate accelerated move
      const { dx, dy } = applyPointerAcceleration(rawDx, rawDy);
      sendCommand({ type: "move", dx, dy });

    } else if (count === 2) {
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      const midX = (t1.clientX + t2.clientX) / 2;
      const midY = (t1.clientY + t2.clientY) / 2;

      const deltaX = midX - lastMidX;
      const deltaY = midY - lastMidY;

      lastMidX = midX;
      lastMidY = midY;
      totalMoveDistance += Math.abs(deltaX) + Math.abs(deltaY);

      // Two-finger smooth scrolling
      const scrollMultiplier = config.scrollSpeed * 0.45;
      const direction = config.naturalScroll ? 1 : -1;

      const scrollX = deltaX * scrollMultiplier * direction;
      const scrollY = deltaY * scrollMultiplier * direction;

      if (Math.abs(scrollX) > 0.3 || Math.abs(scrollY) > 0.3) {
        sendCommand({ type: "scroll", dx: scrollX, dy: scrollY });
      }
    } else if (count >= 3 && !threeFingerTriggered) {
      const t1 = e.touches[0];
      const t2 = e.touches[1];
      const t3 = e.touches[2];
      const midX = (t1.clientX + t2.clientX + t3.clientX) / 3;
      const midY = (t1.clientY + t2.clientY + t3.clientY) / 3;
      const dx = midX - threeFingerStartX;
      const dy = midY - threeFingerStartY;
      totalMoveDistance += Math.abs(dx) + Math.abs(dy);

      const absX = Math.abs(dx);
      const absY = Math.abs(dy);

      // Multi-Touch Thresholds (32px vertical, 38px horizontal)
      if (absY > 32 && absY > absX * 1.1) {
        threeFingerTriggered = true;
        if (dy < 0) {
          // 3-Finger Swipe UP: Toggle Activities Overview / App Grid
          sendCommand({ type: "gesture", gesture: "swipe_up" });
          vibrate([25, 45, 25]);
          showToast("▲ Activities Overview");
        } else {
          // 3-Finger Swipe DOWN: Close Overview / Return to Desktop
          sendCommand({ type: "gesture", gesture: "swipe_down" });
          vibrate([25, 45, 25]);
          showToast("▼ Desktop / Close");
        }
      } else if (absX > 38 && absX > absY * 1.1) {
        threeFingerTriggered = true;
        if (dx < 0) {
          // 3-Finger Swipe LEFT: Switch to Next Workspace
          sendCommand({ type: "gesture", gesture: "swipe_left" });
          vibrate(30);
          showToast("▶ Next Workspace");
        } else {
          // 3-Finger Swipe RIGHT: Switch to Previous Workspace
          sendCommand({ type: "gesture", gesture: "swipe_right" });
          vibrate(30);
          showToast("◀ Previous Workspace");
        }
      }
    }
  }, { passive: false });

  trackpad.addEventListener("touchend", (e) => {
    e.preventDefault();
    const duration = performance.now() - touchStartTime;
    touchRing.classList.remove("active");

    if (isDragLocked) {
      isDragLocked = false;
      dragBadge.classList.remove("visible");
      sendCommand({ type: "btn_up", button: "left" });
      vibrate(10);
      return;
    }

    // Single finger tap -> Left Click
    if (activeTouches === 1 && duration < 240 && totalMoveDistance < 12) {
      sendCommand({ type: "click", button: "left" });
      vibrate(15);
      lastTapReleaseTime = performance.now();
    }
    // Two fingers tap -> Right Click
    else if (activeTouches === 2 && duration < 280 && totalMoveDistance < 16) {
      sendCommand({ type: "click", button: "right" });
      vibrate([15, 35, 15]);
    }
    // Three fingers tap -> Middle Click (only if swipe gesture wasn't triggered)
    else if (activeTouches >= 3 && !threeFingerTriggered && duration < 320 && totalMoveDistance < 22) {
      sendCommand({ type: "click", button: "middle" });
      vibrate([20, 20, 20]);
    }

    activeTouches = e.touches.length;
    if (activeTouches === 0) {
      threeFingerTriggered = false;
    }
  }, { passive: false });

  trackpad.addEventListener("touchcancel", () => {
    touchRing.classList.remove("active");
    if (isDragLocked) {
      isDragLocked = false;
      dragBadge.classList.remove("visible");
      sendCommand({ type: "btn_up", button: "left" });
    }
    activeTouches = 0;
  });

  // ================= Dedicated Scroll Rail (Right Edge) =================
  let railStartY = 0;
  let railLastY = 0;

  scrollRail.addEventListener("touchstart", (e) => {
    e.preventDefault();
    if (e.touches.length > 0) {
      railStartY = e.touches[0].clientY;
      railLastY = railStartY;
      vibrate(8);
    }
  }, { passive: false });

  scrollRail.addEventListener("touchmove", (e) => {
    e.preventDefault();
    if (e.touches.length > 0) {
      const currentY = e.touches[0].clientY;
      const deltaY = currentY - railLastY;
      railLastY = currentY;

      const direction = config.naturalScroll ? 1 : -1;
      const scrollY = deltaY * config.scrollSpeed * 0.7 * direction;

      if (Math.abs(scrollY) > 0.2) {
        sendCommand({ type: "scroll", dx: 0, dy: scrollY });
      }
    }
  }, { passive: false });

  // ================= Physical Buttons (Left / Mid / Right) =================
  function setupButton(element, btnName) {
    element.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      element.classList.add("active");
      sendCommand({ type: "btn_down", button: btnName });
      vibrate(20);
    });

    const release = (e) => {
      if (element.classList.contains("active")) {
        e.preventDefault();
        element.classList.remove("active");
        sendCommand({ type: "btn_up", button: btnName });
      }
    };

    element.addEventListener("pointerup", release);
    element.addEventListener("pointercancel", release);
    element.addEventListener("pointerleave", release);
  }

  setupButton(btnLeftClick, "left");
  setupButton(btnMiddleClick, "middle");
  setupButton(btnRightClick, "right");

  // ================= Media Keys & Drawer =================
  document.querySelectorAll("[data-key]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.getAttribute("data-key");
      sendCommand({ type: "key", key });
      vibrate(15);
    });
  });

  btnMedia.addEventListener("click", () => {
    const isOpen = mediaDrawer.classList.toggle("open");
    btnMedia.classList.toggle("active", isOpen);
    vibrate(10);
  });
  closeMediaDrawer.addEventListener("click", () => {
    mediaDrawer.classList.remove("open");
    btnMedia.classList.remove("active");
  });

  // ================= Keyboard Drawer =================
  btnKeyboard.addEventListener("click", () => {
    const isOpen = keyboardDrawer.classList.toggle("open");
    btnKeyboard.classList.toggle("active", isOpen);
    if (isOpen) {
      setTimeout(() => typeInput.focus(), 200);
    }
    vibrate(10);
  });
  if (closeKeyboardDrawer) {
    closeKeyboardDrawer.addEventListener("click", () => {
      keyboardDrawer.classList.remove("open");
      btnKeyboard.classList.remove("active");
    });
  }
  // Auto-search chip toggle
  if (chipAutoEnter) {
    const isAuto = localStorage.getItem("tp_autoEnter") !== "false";
    chipAutoEnter.classList.toggle("active", isAuto);
    chipAutoEnter.addEventListener("click", () => {
      const active = chipAutoEnter.classList.toggle("active");
      localStorage.setItem("tp_autoEnter", active);
      vibrate(10);
    });
  }

  // Live clear button visibility
  typeInput.addEventListener("input", () => {
    if (btnClearInput) {
      btnClearInput.style.display = typeInput.value.length > 0 ? "flex" : "none";
    }
  });

  if (btnClearInput) {
    btnClearInput.addEventListener("click", () => {
      typeInput.value = "";
      btnClearInput.style.display = "none";
      typeInput.focus();
      vibrate(10);
    });
  }

  // ================= Screenshot / Image Paste & Attachment =================
  const btnAttachImage = document.getElementById("btnAttachImage");
  const fileImagePicker = document.getElementById("fileImagePicker");
  const attachedImageCard = document.getElementById("attachedImageCard");
  const attachedImgPreview = document.getElementById("attachedImgPreview");
  const attachedImgSize = document.getElementById("attachedImgSize");
  const btnRemoveAttachedImg = document.getElementById("btnRemoveAttachedImg");
  const btnPasteImgLaptop = document.getElementById("btnPasteImgLaptop");
  const btnOcrExtract = document.getElementById("btnOcrExtract");
  const txtOcrBtn = document.getElementById("txtOcrBtn");

  let attachedImageData = null;

  function handleImageFile(file) {
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      attachedImageData = e.target.result;
      const sizeKb = Math.round(file.size / 1024);
      if (attachedImgPreview) attachedImgPreview.src = attachedImageData;
      if (attachedImgSize) attachedImgSize.textContent = `${sizeKb} KB`;
      if (attachedImageCard) attachedImageCard.style.display = "flex";
      vibrate(15);
      showToast("📷 Screenshot attached to input!");
    };
    reader.readAsDataURL(file);
  }

  function clearAttachedImage() {
    attachedImageData = null;
    if (attachedImageCard) attachedImageCard.style.display = "none";
    if (attachedImgPreview) attachedImgPreview.src = "";
    if (fileImagePicker) fileImagePicker.value = "";
  }

  if (btnRemoveAttachedImg) {
    btnRemoveAttachedImg.addEventListener("click", clearAttachedImage);
  }

  // Paste listener directly on typeInput
  typeInput.addEventListener("paste", (e) => {
    const items = (e.clipboardData || window.clipboardData)?.items;
    if (!items) return;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf("image") !== -1) {
        e.preventDefault();
        const blob = items[i].getAsFile();
        handleImageFile(blob);
        break;
      }
    }
  });

  window.addEventListener("paste", (e) => {
    if (keyboardDrawer && keyboardDrawer.classList.contains("open")) {
      const items = (e.clipboardData || window.clipboardData)?.items;
      if (!items) return;
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") !== -1) {
          const blob = items[i].getAsFile();
          handleImageFile(blob);
          break;
        }
      }
    }
  });

  if (btnAttachImage) {
    btnAttachImage.addEventListener("click", async () => {
      vibrate(10);
      try {
        if (navigator.clipboard && navigator.clipboard.read) {
          const clipItems = await navigator.clipboard.read();
          for (const item of clipItems) {
            const imgType = item.types.find(t => t.startsWith("image/"));
            if (imgType) {
              const blob = await item.getType(imgType);
              handleImageFile(blob);
              return;
            }
          }
        }
      } catch (err) {}
      if (fileImagePicker) fileImagePicker.click();
    });
  }

  if (fileImagePicker) {
    fileImagePicker.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (file) handleImageFile(file);
    });
  }

  function sendAttachedImage(pressEnter = false) {
    if (!attachedImageData) return;
    vibrate(25);
    sendCommand({
      type: "paste_image",
      image: attachedImageData,
      enter: pressEnter,
      auto_paste: true
    });
    clearAttachedImage();
  }

  if (btnPasteImgLaptop) {
    btnPasteImgLaptop.addEventListener("click", () => {
      sendAttachedImage(false);
    });
  }

  // OCR Text Extraction using dynamic Tesseract.js
  async function performOcr() {
    if (!attachedImageData) return;
    vibrate(15);
    if (txtOcrBtn) txtOcrBtn.textContent = "Reading...";
    if (btnOcrExtract) btnOcrExtract.disabled = true;

    try {
      if (!window.Tesseract) {
        await new Promise((resolve, reject) => {
          const s = document.createElement("script");
          s.src = "https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js";
          s.onload = resolve;
          s.onerror = reject;
          document.head.appendChild(s);
        });
      }

      const { data: { text } } = await Tesseract.recognize(attachedImageData, 'eng');
      const cleanText = text.replace(/[\r\n]+/g, " ").trim();
      if (cleanText) {
        typeInput.value = cleanText;
        if (btnClearInput) btnClearInput.style.display = "flex";
        vibrate(20);
        clearAttachedImage();
        typeInput.focus();
        showToast("✓ Text extracted into search box!");
      } else {
        alert("No readable text detected. You can still tap 'Paste on Laptop (Ctrl+V)'!");
      }
    } catch (err) {
      console.warn("OCR error:", err);
      alert("Could not extract text. You can still tap 'Paste on Laptop (Ctrl+V)' to send the screenshot!");
    } finally {
      if (txtOcrBtn) txtOcrBtn.textContent = "Extract Text";
      if (btnOcrExtract) btnOcrExtract.disabled = false;
    }
  }

  if (btnOcrExtract) {
    btnOcrExtract.addEventListener("click", performOcr);
  }

  function sendTypedText(forceEnter = false) {
    const text = typeInput.value;
    const autoEnterActive = chipAutoEnter ? chipAutoEnter.classList.contains("active") : true;
    const shouldEnter = forceEnter || autoEnterActive;

    if (attachedImageData) {
      sendAttachedImage(shouldEnter);
      if (text) {
        setTimeout(() => {
          sendCommand({ type: "type", text, enter: shouldEnter });
          typeInput.value = "";
          if (btnClearInput) btnClearInput.style.display = "none";
        }, 80);
      }
      return;
    }

    if (text) {
      sendCommand({ type: "type", text, enter: shouldEnter });
      typeInput.value = "";
      if (btnClearInput) btnClearInput.style.display = "none";
      vibrate(25);
    } else if (shouldEnter) {
      // If text box is empty, send direct Enter key to initiate search or submit
      sendCommand({ type: "key", key: "enter" });
      vibrate(20);
    }
  }

  function showToast(text) {
    let toast = document.getElementById("appToast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "appToast";
      toast.style.cssText = "position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:rgba(14,20,36,0.96);border:1px solid rgba(0,242,254,0.4);color:#00f2fe;padding:8px 18px;border-radius:20px;font-size:0.80rem;font-weight:600;z-index:9999;box-shadow:0 8px 24px rgba(0,0,0,0.6);pointer-events:none;transition:opacity 0.25s ease;opacity:0;";
      document.body.appendChild(toast);
    }
    toast.textContent = text;
    toast.style.opacity = "1";
    setTimeout(() => {
      toast.style.opacity = "0";
    }, 2500);
  }

  if (btnSendText) {
    btnSendText.addEventListener("click", () => {
      sendTypedText(false);
    });
  }

  if (btnSendEnter) {
    btnSendEnter.addEventListener("click", () => {
      sendTypedText(true);
    });
  }

  typeInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      // On mobile keyboard Enter, trigger search (send + Enter)
      sendTypedText(true);
    }
  });

  // ================= Settings Modal =================
  btnSettings.addEventListener("click", () => {
    settingsModal.classList.add("open");
    vibrate(10);
  });
  closeSettingsModal.addEventListener("click", () => {
    settingsModal.classList.remove("open");
  });
  settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) {
      settingsModal.classList.remove("open");
    }
  });

  // ================= Sound System & Audio Hub =================
  const mediaPlayerName = document.getElementById("mediaPlayerName");
  const mediaStatus = document.getElementById("mediaStatus");
  const mediaTitle = document.getElementById("mediaTitle");
  const mediaArtist = document.getElementById("mediaArtist");
  const btnMediaPrev = document.getElementById("btnMediaPrev");
  const btnMediaPlayPause = document.getElementById("btnMediaPlayPause");
  const svgPlayPause = document.getElementById("svgPlayPause");
  const btnMediaNext = document.getElementById("btnMediaNext");

  const sliderVolume = document.getElementById("sliderVolume");
  const lblVolumePercent = document.getElementById("lblVolumePercent");
  const btnToggleMute = document.getElementById("btnToggleMute");
  const lblActiveSink = document.getElementById("lblActiveSink");
  const btnSwitchSink = document.getElementById("btnSwitchSink");

  const btnPushToTalk = document.getElementById("btnPushToTalk");
  const lblMicStatus = document.getElementById("lblMicStatus");

  const lblSleepTimer = document.getElementById("lblSleepTimer");
  const btnCancelTimer = document.getElementById("btnCancelTimer");

  let currentSinks = [];
  let isVolumeDragging = false;

  function updateAudioStateUI(state) {
    if (!state) return;

    // 1. Now Playing
    if (state.now_playing) {
      const np = state.now_playing;
      if (mediaTitle) mediaTitle.textContent = np.title || "No active media";
      if (mediaArtist) mediaArtist.textContent = np.artist || (np.has_media ? "Playing on Laptop" : "");
      if (mediaPlayerName) mediaPlayerName.textContent = np.player || "Media";
      if (mediaStatus) {
        mediaStatus.textContent = np.status;
        mediaStatus.style.color = np.status === "Playing" ? "var(--color-success)" : "var(--text-muted)";
      }

      // Update Play/Pause icon
      if (svgPlayPause) {
        if (np.status === "Playing") {
          // Pause icon (two vertical bars)
          svgPlayPause.innerHTML = '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';
        } else {
          // Play triangle
          svgPlayPause.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"/>';
        }
      }
    }

    // 2. Volume
    if (sliderVolume && !isVolumeDragging) {
      sliderVolume.value = state.volume;
    }
    if (lblVolumePercent) {
      lblVolumePercent.textContent = (state.muted ? "MUTED" : `${state.volume}%`);
      lblVolumePercent.style.color = state.muted ? "var(--color-error)" : "var(--accent-cyan)";
    }

    // 3. Audio Sinks
    if (state.sinks && Array.isArray(state.sinks)) {
      currentSinks = state.sinks;
      const activeSink = currentSinks.find(s => s.is_default);
      if (lblActiveSink) {
        lblActiveSink.textContent = activeSink ? activeSink.label : "Default Audio Sink";
      }
    }

    // 4. Sleep timer remaining
    if (state.sleep_timer_remaining !== undefined) {
      updateSleepTimerRemaining(state.sleep_timer_remaining);
    }
  }

  function updateSleepTimerRemaining(seconds) {
    if (!lblSleepTimer) return;
    if (seconds > 0) {
      const m = Math.floor(seconds / 60);
      const s = seconds % 60;
      lblSleepTimer.textContent = `${m}:${s < 10 ? '0' : ''}${s}`;
      if (btnCancelTimer) btnCancelTimer.style.display = "inline-block";
    } else {
      lblSleepTimer.textContent = "Off";
      if (btnCancelTimer) btnCancelTimer.style.display = "none";
      document.querySelectorAll(".timer-chip").forEach(c => c.classList.remove("active"));
    }
  }

  function updateSleepTimerUI(msg) {
    updateSleepTimerRemaining(msg.remaining || 0);
  }

  // Media Playback Controls
  if (btnMediaPlayPause) {
    btnMediaPlayPause.addEventListener("click", () => {
      sendCommand({ type: "media_action", action: "playpause" });
      vibrate(20);
    });
  }
  if (btnMediaNext) {
    btnMediaNext.addEventListener("click", () => {
      sendCommand({ type: "media_action", action: "next" });
      vibrate(15);
    });
  }
  if (btnMediaPrev) {
    btnMediaPrev.addEventListener("click", () => {
      sendCommand({ type: "media_action", action: "prev" });
      vibrate(15);
    });
  }

  // Volume Slider Controls
  if (sliderVolume) {
    sliderVolume.addEventListener("pointerdown", () => { isVolumeDragging = true; });
    sliderVolume.addEventListener("pointerup", () => {
      isVolumeDragging = false;
      sendCommand({ type: "set_volume", volume: parseInt(sliderVolume.value) });
    });
    sliderVolume.addEventListener("input", (e) => {
      const vol = parseInt(e.target.value);
      if (lblVolumePercent) lblVolumePercent.textContent = `${vol}%`;
      sendCommand({ type: "set_volume", volume: vol });
    });
  }

  if (btnToggleMute) {
    btnToggleMute.addEventListener("click", () => {
      sendCommand({ type: "toggle_mute" });
      vibrate(15);
    });
  }

  // Audio Output Switcher (ECOMAX Bluetooth vs Laptop Speakers)
  if (btnSwitchSink) {
    btnSwitchSink.addEventListener("click", () => {
      if (!currentSinks || currentSinks.length < 2) return;
      const altSink = currentSinks.find(s => !s.is_default);
      if (altSink) {
        sendCommand({ type: "switch_sink", sink: altSink.name });
        vibrate(25);
      }
    });
  }

  // ================= Wireless Megaphone (Phone Mic -> WebSocket PCM) =================
  let micAudioContext = null;
  let micMediaStream = null;
  let micProcessor = null;
  let isTalking = false;

  async function startPushToTalk() {
    if (isTalking) return;
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Microphone access is not supported or requires a secure context (HTTPS/localhost).");
        return;
      }

      micMediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });

      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      micAudioContext = new AudioCtx({ sampleRate: 16000 });
      const source = micAudioContext.createMediaStreamSource(micMediaStream);

      // Buffer size 2048 at 16000Hz = ~128ms chunks
      micProcessor = micAudioContext.createScriptProcessor(2048, 1, 1);

      micProcessor.onaudioprocess = (e) => {
        if (!isTalking || !socket || socket.readyState !== WebSocket.OPEN) return;
        const inputData = e.inputBuffer.getChannelData(0);
        const pcm16 = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          pcm16[i] = Math.max(-32768, Math.min(32767, Math.round(inputData[i] * 32767)));
        }
        socket.send(pcm16.buffer);
      };

      source.connect(micProcessor);
      micProcessor.connect(micAudioContext.destination);

      sendCommand({ type: "mic_start" });
      isTalking = true;
      if (btnPushToTalk) btnPushToTalk.classList.add("talking");
      if (lblMicStatus) lblMicStatus.textContent = "BROADCASTING LIVE...";
      vibrate([25, 40, 25]);
    } catch (err) {
      console.error("Mic access error:", err);
      alert("Please allow microphone permissions to use the wireless megaphone.");
    }
  }

  function stopPushToTalk() {
    if (!isTalking) return;
    isTalking = false;
    sendCommand({ type: "mic_stop" });

    if (btnPushToTalk) btnPushToTalk.classList.remove("talking");
    if (lblMicStatus) lblMicStatus.textContent = "HOLD TO TALK";

    if (micProcessor) {
      try { micProcessor.disconnect(); } catch (e) {}
      micProcessor = null;
    }
    if (micAudioContext) {
      try { micAudioContext.close(); } catch (e) {}
      micAudioContext = null;
    }
    if (micMediaStream) {
      try { micMediaStream.getTracks().forEach(t => t.stop()); } catch (e) {}
      micMediaStream = null;
    }
    vibrate(15);
  }

  if (btnPushToTalk) {
    btnPushToTalk.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      startPushToTalk();
    });
    const endTalk = (e) => {
      if (isTalking) {
        e.preventDefault();
        stopPushToTalk();
      }
    };
    btnPushToTalk.addEventListener("pointerup", endTalk);
    btnPushToTalk.addEventListener("pointercancel", endTalk);
    btnPushToTalk.addEventListener("pointerleave", endTalk);
  }

  // ================= Subwoofer Soundboard SFX =================
  document.querySelectorAll("[data-sfx]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sfx = btn.getAttribute("data-sfx");
      sendCommand({ type: "play_sfx", name: sfx });
      vibrate([20, 30, 20]);
    });
  });

  // ================= Fade-out Sleep Timer =================
  document.querySelectorAll("[data-mins]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const mins = parseFloat(btn.getAttribute("data-mins"));
      document.querySelectorAll(".timer-chip").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      sendCommand({ type: "start_sleep_timer", minutes: mins });
      if (btnCancelTimer) btnCancelTimer.style.display = "inline-block";
      vibrate(20);
    });
  });

  if (btnCancelTimer) {
    btnCancelTimer.addEventListener("click", () => {
      sendCommand({ type: "cancel_sleep_timer" });
      document.querySelectorAll(".timer-chip").forEach(c => c.classList.remove("active"));
      btnCancelTimer.style.display = "none";
      if (lblSleepTimer) lblSleepTimer.textContent = "Off";
      vibrate(15);
    });
  }

  // Refresh audio state whenever media drawer is opened
  if (btnMedia) {
    btnMedia.addEventListener("click", () => {
      sendCommand({ type: "get_audio_state" });
    });
  }

  // ================= Floating Picture-in-Picture (PiP) Screen Viewer =================
  let isPipActive = false;
  let pipSizeIndex = 0; // 0: default (275px), 1: wide (340px), 2: mini (195px)
  const pipSizes = ["", "wide", "mini"];
  const pipProfiles = ["balanced", "eco", "hd"];
  let currentProfile = localStorage.getItem("tp_pip_profile") || "balanced";

  let frameCount = 0;
  let bytesInInterval = 0;
  let lastStatTime = performance.now();

  async function handleScreenFrame(data) {
    if (!isPipActive || !pipCtx) return;
    const blob = data instanceof Blob ? data : new Blob([data], { type: "image/webp" });
    bytesInInterval += blob.size;

    try {
      if (window.createImageBitmap) {
        const bitmap = await createImageBitmap(blob);
        pipCtx.drawImage(bitmap, 0, 0, pipCanvas.width, pipCanvas.height);
        bitmap.close();
      } else {
        const url = URL.createObjectURL(blob);
        const img = new Image();
        img.onload = () => {
          pipCtx.drawImage(img, 0, 0, pipCanvas.width, pipCanvas.height);
          URL.revokeObjectURL(url);
        };
        img.src = url;
      }

      if (pipLoading && !pipLoading.classList.contains("hidden")) {
        pipLoading.classList.add("hidden");
      }

      // Calculate live FPS & Bandwidth Throughput
      frameCount++;
      const now = performance.now();
      const elapsed = now - lastStatTime;
      if (elapsed >= 1000) {
        const currentFps = Math.round((frameCount * 1000) / elapsed);
        const currentKbps = Math.round(bytesInInterval / 1024);
        frameCount = 0;
        bytesInInterval = 0;
        lastStatTime = now;
        if (pipFps) {
          pipFps.textContent = `${currentFps} fps`;
          pipFps.title = `${currentFps} fps · ${currentKbps} KB/s`;
        }
      }
    } catch (err) {
      console.warn("Screen frame render error:", err);
    }
  }

  function updateProfileBadgeUI() {
    if (!btnPipProfile) return;
    const txt = document.getElementById("txtPipProfile");
    if (txt) {
      txt.textContent = currentProfile.toUpperCase();
    } else {
      btnPipProfile.textContent = currentProfile.toUpperCase();
    }
    btnPipProfile.className = "pip-profile-badge";
    if (currentProfile === "eco") {
      btnPipProfile.classList.add("eco");
    } else if (currentProfile === "hd") {
      btnPipProfile.classList.add("hd");
    }
  }

  function cyclePipProfile(e) {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    vibrate(15);
    const curIdx = pipProfiles.indexOf(currentProfile);
    currentProfile = pipProfiles[(curIdx + 1) % pipProfiles.length];
    localStorage.setItem("tp_pip_profile", currentProfile);
    updateProfileBadgeUI();
    if (isPipActive) {
      sendCommand({ type: "pip_set_profile", profile: currentProfile });
    }
  }

  function togglePip(forceState) {
    const nextState = forceState !== undefined ? forceState : !isPipActive;
    if (nextState === isPipActive) return;
    isPipActive = nextState;
    vibrate(20);

    if (isPipActive) {
      pipContainer.style.display = "block";
      btnPipToggle.classList.add("active");
      if (pipLoading) {
        pipLoading.classList.remove("hidden");
        pipLoading.textContent = "Connecting live display...";
      }
      // Ensure it starts centered if not user-positioned
      if (!pipContainer.dataset.userPositioned) {
        pipContainer.style.left = "50%";
        pipContainer.style.transform = "translateX(-50%)";
        pipContainer.style.top = "14px";
        pipContainer.style.right = "auto";
      }
      updateProfileBadgeUI();
      sendCommand({ type: "pip_start", profile: currentProfile });
    } else {
      pipContainer.style.display = "none";
      btnPipToggle.classList.remove("active");
      sendCommand({ type: "pip_stop" });
      if (document.pictureInPictureElement) {
        document.exitPictureInPicture().catch(() => {});
      }
    }
  }

  function cyclePipSize() {
    vibrate(12);
    pipSizes.forEach(cls => cls && pipContainer.classList.remove(cls));
    pipSizeIndex = (pipSizeIndex + 1) % pipSizes.length;
    const nextClass = pipSizes[pipSizeIndex];
    if (nextClass) {
      pipContainer.classList.add(nextClass);
    }
    // Re-verify positioning: keep centered if not user dragged
    if (!pipContainer.dataset.userPositioned) {
      pipContainer.style.left = "50%";
      pipContainer.style.transform = "translateX(-50%)";
    } else {
      const maxLeft = Math.max(8, window.innerWidth - pipContainer.offsetWidth - 8);
      const curLeft = parseFloat(pipContainer.style.left) || 8;
      if (curLeft > maxLeft) {
        pipContainer.style.left = `${maxLeft}px`;
      }
    }
  }

  async function toggleNativePip() {
    if (!pipCanvas || !pipHiddenVideo) return;
    vibrate(20);
    try {
      if (document.pictureInPictureElement) {
        await document.exitPictureInPicture();
        return;
      }
      if (!pipHiddenVideo.srcObject) {
        const stream = pipCanvas.captureStream(12);
        pipHiddenVideo.srcObject = stream;
        await pipHiddenVideo.play().catch(() => {});
      }
      if (pipHiddenVideo.requestPictureInPicture) {
        await pipHiddenVideo.requestPictureInPicture();
      } else {
        alert("System Picture-in-Picture window is not supported on this browser.");
      }
    } catch (err) {
      console.warn("Native PiP error:", err);
    }
  }

  if (btnPipToggle) {
    btnPipToggle.addEventListener("click", () => togglePip());
  }
  if (btnPipClose) {
    btnPipClose.addEventListener("pointerdown", (e) => e.stopPropagation());
    btnPipClose.addEventListener("click", (e) => {
      e.stopPropagation();
      togglePip(false);
    });
  }
  if (btnPipSize) {
    btnPipSize.addEventListener("pointerdown", (e) => e.stopPropagation());
    btnPipSize.addEventListener("click", (e) => {
      e.stopPropagation();
      cyclePipSize();
    });
  }
  if (btnPipPopout) {
    btnPipPopout.addEventListener("pointerdown", (e) => e.stopPropagation());
    btnPipPopout.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleNativePip();
    });
  }
  if (btnPipProfile) {
    btnPipProfile.addEventListener("pointerdown", (e) => e.stopPropagation());
    btnPipProfile.addEventListener("click", cyclePipProfile);
    updateProfileBadgeUI();
  }

  // Draggable PiP Window
  if (pipHeader) {
    let isPointerDown = false;
    let isDraggingPip = false;
    let pipStartX = 0;
    let pipStartY = 0;
    let pipInitialLeft = 0;
    let pipInitialTop = 0;
    let activePointerId = null;
    let hasSnappedCenter = false;
    let lastHeaderTapTime = 0;

    function recenterPip() {
      vibrate(20);
      delete pipContainer.dataset.userPositioned;
      pipContainer.style.left = "50%";
      pipContainer.style.transform = "translateX(-50%)";
      pipContainer.style.top = "14px";
      pipContainer.style.right = "auto";
    }

    pipHeader.addEventListener("pointerdown", (e) => {
      // Ignore drags originating on buttons or the profile badge
      if (e.target.closest("button, .pip-btn, .pip-profile-badge")) return;

      isPointerDown = true;
      isDraggingPip = false;
      hasSnappedCenter = false;
      activePointerId = e.pointerId;
      pipStartX = e.clientX;
      pipStartY = e.clientY;
      const rect = pipContainer.getBoundingClientRect();
      pipInitialLeft = rect.left;
      pipInitialTop = rect.top;
    });

    pipHeader.addEventListener("pointermove", (e) => {
      if (!isPointerDown) return;
      const dx = e.clientX - pipStartX;
      const dy = e.clientY - pipStartY;

      // Slop threshold: require > 6px movement before starting drag
      if (!isDraggingPip) {
        if (Math.hypot(dx, dy) > 6) {
          isDraggingPip = true;
          pipContainer.dataset.userPositioned = "true";
          try {
            pipHeader.setPointerCapture(activePointerId);
          } catch (err) {}
          pipContainer.style.transform = "none";
          pipContainer.style.right = "auto";
          pipContainer.style.left = `${pipInitialLeft}px`;
          pipContainer.style.top = `${pipInitialTop}px`;
        } else {
          return;
        }
      }

      const maxLeft = Math.max(8, window.innerWidth - pipContainer.offsetWidth - 8);
      const maxTop = Math.max(8, window.innerHeight - pipContainer.offsetHeight - 8);
      const targetLeft = pipInitialLeft + dx;
      const targetTop = pipInitialTop + dy;

      // Smart Snap-to-Center:
      // If within 18px of exact horizontal center, snap into center!
      const centerLeft = Math.round((window.innerWidth - pipContainer.offsetWidth) / 2);
      const isNearCenter = Math.abs(targetLeft - centerLeft) < 18;
      const newLeft = isNearCenter ? centerLeft : Math.max(8, Math.min(maxLeft, targetLeft));
      const newTop = Math.max(8, Math.min(maxTop, targetTop));

      if (isNearCenter && !hasSnappedCenter) {
        vibrate(10);
        hasSnappedCenter = true;
      } else if (!isNearCenter && hasSnappedCenter) {
        hasSnappedCenter = false;
      }

      pipContainer.style.left = `${newLeft}px`;
      pipContainer.style.top = `${newTop}px`;
    });

    const stopDragPip = (e) => {
      if (isDraggingPip && activePointerId !== null) {
        try {
          pipHeader.releasePointerCapture(activePointerId);
        } catch (err) {}
      }
      isPointerDown = false;
      isDraggingPip = false;
      activePointerId = null;
      hasSnappedCenter = false;
    };

    pipHeader.addEventListener("pointerup", (e) => {
      if (!e.target.closest("button, .pip-btn, .pip-profile-badge")) {
        const now = performance.now();
        if (!isDraggingPip && (now - lastHeaderTapTime < 350)) {
          // Double-tap on header to re-center
          recenterPip();
          lastHeaderTapTime = 0;
          stopDragPip(e);
          return;
        }
        lastHeaderTapTime = now;
      }
      stopDragPip(e);
    });

    pipHeader.addEventListener("pointercancel", stopDragPip);

    pipHeader.addEventListener("dblclick", (e) => {
      if (!e.target.closest("button, .pip-btn, .pip-profile-badge")) {
        recenterPip();
      }
    });

    // Auto-reclamp or maintain center on orientation change / screen resize
    window.addEventListener("resize", () => {
      if (isPipActive && pipContainer) {
        if (!pipContainer.dataset.userPositioned) {
          pipContainer.style.left = "50%";
          pipContainer.style.transform = "translateX(-50%)";
        } else {
          const maxLeft = Math.max(8, window.innerWidth - pipContainer.offsetWidth - 8);
          const maxTop = Math.max(8, window.innerHeight - pipContainer.offsetHeight - 8);
          const curLeft = parseFloat(pipContainer.style.left) || 8;
          const curTop = parseFloat(pipContainer.style.top) || 14;
          pipContainer.style.left = `${Math.min(maxLeft, Math.max(8, curLeft))}px`;
          pipContainer.style.top = `${Math.min(maxTop, Math.max(8, curTop))}px`;
        }
      }
    });
  }

  // ================= Fullscreen Mode =================
  btnFullscreen.addEventListener("click", () => {
    vibrate(15);
    if (!document.fullscreenElement) {
      if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else if (document.documentElement.webkitRequestFullscreen) {
        document.documentElement.webkitRequestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
    }
  });

  // ================= Progressive Web App (PWA) =================
  const btnInstallPwa = document.getElementById("btnInstallPwa");
  const txtInstallPwa = document.getElementById("txtInstallPwa");
  const pwaStatusDesc = document.getElementById("pwaStatusDesc");
  let deferredInstallPrompt = null;

  // Check if running as installed standalone PWA
  const isStandalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;

  if (isStandalone) {
    if (btnInstallPwa) {
      btnInstallPwa.classList.add("installed");
      btnInstallPwa.disabled = true;
    }
    if (txtInstallPwa) txtInstallPwa.textContent = "Installed on Phone";
    if (pwaStatusDesc) pwaStatusDesc.textContent = "Running in standalone fullscreen mode";
  }

  // Register Service Worker
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js")
        .then((reg) => console.log("Service Worker registered with scope:", reg.scope))
        .catch((err) => console.warn("Service Worker registration failed:", err));
    });
  }

  // Capture beforeinstallprompt event (Chrome, Android, Edge)
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    if (btnInstallPwa && !isStandalone) {
      btnInstallPwa.classList.remove("installed");
      btnInstallPwa.disabled = false;
      if (txtInstallPwa) txtInstallPwa.textContent = "Install App";
      if (pwaStatusDesc) pwaStatusDesc.textContent = "Tap to add to your phone's home screen";
    }
  });

  window.addEventListener("appinstalled", () => {
    deferredInstallPrompt = null;
    if (btnInstallPwa) {
      btnInstallPwa.classList.add("installed");
      btnInstallPwa.disabled = true;
    }
    if (txtInstallPwa) txtInstallPwa.textContent = "Installed on Phone";
    if (pwaStatusDesc) pwaStatusDesc.textContent = "Installed! You can launch it from your home screen.";
  });

  if (btnInstallPwa) {
    btnInstallPwa.addEventListener("click", async () => {
      vibrate(20);
      if (deferredInstallPrompt) {
        deferredInstallPrompt.prompt();
        const { outcome } = await deferredInstallPrompt.userChoice;
        if (outcome === "accepted") {
          deferredInstallPrompt = null;
          btnInstallPwa.classList.add("installed");
          btnInstallPwa.disabled = true;
          if (txtInstallPwa) txtInstallPwa.textContent = "Installed on Phone";
        }
      } else if (isStandalone) {
        alert("Fedora Cursor is already installed and running as a standalone app!");
      } else {
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
        if (isIOS) {
          alert("To install on iOS:\n1. Tap the Share button in Safari (square with up arrow)\n2. Scroll down and tap 'Add to Home Screen'\n3. Open Fedora Cursor from your Home Screen!");
        } else {
          alert("To install on your phone:\n1. Tap the browser menu (⋮ at top-right)\n2. Select 'Install app' or 'Add to Home screen'\n3. Launch Fedora Cursor directly from your home screen!");
        }
      }
    });
  }

  // Initialize Connection
  connectWebSocket();

})();
