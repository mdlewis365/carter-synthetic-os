/*
 * SPDX-License-Identifier: AGPL-3.0-only
 * Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
 */

"use strict";

const runtime = {
  csrf: "",
  sessionId: "",
  provider: "unknown",
  micActive: false,
  cameraActive: false,
  attention: "background",
  audio: null,
  cameraStream: null,
  speaking: false,
  ttsUrl: null,
};

const byId = (id) => document.getElementById(id);

function setBusy(element, busy) {
  element.disabled = Boolean(busy);
  element.setAttribute("aria-busy", String(Boolean(busy)));
}

function appendMessage(role, text, className) {
  const article = document.createElement("article");
  article.className = "message " + (className || "");
  const heading = document.createElement("strong");
  heading.textContent = role;
  const content = document.createElement("p");
  content.textContent = String(text || "");
  article.append(heading, content);
  byId("chat-output").appendChild(article);
  byId("chat-output").scrollTop = byId("chat-output").scrollHeight;
  return content;
}

async function api(path, options) {
  const requestOptions = Object.assign(
    { credentials: "same-origin", headers: {} },
    options || {}
  );
  requestOptions.headers = Object.assign({}, requestOptions.headers);
  if (runtime.csrf && requestOptions.method && requestOptions.method !== "GET") {
    requestOptions.headers["X-CSRF-Token"] = runtime.csrf;
  }
  if (
    requestOptions.body &&
    !(requestOptions.body instanceof FormData) &&
    !requestOptions.headers["Content-Type"]
  ) {
    requestOptions.headers["Content-Type"] = "application/json";
  }
  const response = await fetch(path, requestOptions);
  const data = await response.json().catch(() => ({
    error: "invalid_server_response",
  }));
  if (!response.ok) {
    throw new Error(data.error || data.message || "request_failed");
  }
  return data;
}

async function initializeSession() {
  const data = await api("/api/session", { method: "GET" });
  runtime.csrf = data.csrf_token;
  runtime.sessionId = data.session_id;
  runtime.provider = data.provider;
  byId("provider-status").textContent =
    "Provider: " + data.provider + (data.mock ? " (mock)" : "");
  byId("provider-mode-label").textContent = data.mock
    ? "Mock provider is deterministic, not a language model"
    : "Configured provider: " + data.provider;
  byId("transcription-status").textContent = data.audio_cloud_transfer
    ? "Transcription: " + data.transcription_provider + " cloud"
    : "Transcription: disabled";
  byId("transcription-status").classList.toggle(
    "is-active",
    Boolean(data.audio_cloud_transfer)
  );
  byId("session-status").textContent =
    "Session: " + data.session_id.slice(0, 8);
  await Promise.all([
    api("/api/csc/hearing", {
      method: "POST",
      body: JSON.stringify({ active: false }),
    }),
    api("/api/csc/camera", {
      method: "POST",
      body: JSON.stringify({ active: false }),
    }),
  ]);
  await refreshSensoryState();
}

function installTabs() {
  const tabs = Array.from(document.querySelectorAll("[data-tab]"));
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activateTab(tab.dataset.tab));
    tab.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key)) {
        return;
      }
      event.preventDefault();
      const offset = event.key === "ArrowRight" ? 1 : -1;
      const next = tabs[(index + offset + tabs.length) % tabs.length];
      activateTab(next.dataset.tab);
      next.focus();
    });
  });
}

function activateTab(name) {
  document.querySelectorAll("[data-tab]").forEach((tab) => {
    const active = tab.dataset.tab === name;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
  });
  document.querySelectorAll("[role=tabpanel]").forEach((panel) => {
    const active = panel.id === "panel-" + name;
    panel.hidden = !active;
    panel.classList.toggle("is-active", active);
  });
}

function parseSseBlock(block) {
  const lines = block.split(/\r?\n/);
  const event = { event: "message", data: "" };
  lines.forEach((line) => {
    if (line.startsWith("event:")) {
      event.event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      event.data += line.slice(5).trim();
    }
  });
  return event;
}

async function runChat(event) {
  event.preventDefault();
  const button = event.submitter;
  const prompt = byId("chat-input").value.trim();
  if (!prompt) {
    return;
  }
  appendMessage("You", prompt, "user-message");
  const output = appendMessage("Carter", "", "");
  setBusy(button, true);
  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": runtime.csrf,
      },
      body: JSON.stringify({ prompt: prompt }),
    });
    if (!response.ok || !response.body) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.error || "stream_request_failed");
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finished = false;
    while (!finished) {
      const chunk = await reader.read();
      finished = chunk.done;
      buffer += decoder.decode(chunk.value || new Uint8Array(), {
        stream: !finished,
      });
      const blocks = buffer.split(/\r?\n\r?\n/);
      buffer = blocks.pop() || "";
      blocks.forEach((block) => {
        const sse = parseSseBlock(block);
        if (!sse.data) {
          return;
        }
        const payload = JSON.parse(sse.data);
        if (sse.event === "token") {
          output.textContent += payload.text;
        }
        if (sse.event === "error") {
          throw new Error(payload.error || "stream_error");
        }
      });
    }
  } catch (error) {
    output.parentElement.classList.add("error-message");
    output.textContent = "Request failed: " + error.message;
  } finally {
    setBusy(button, false);
  }
}

async function runEas(event) {
  event.preventDefault();
  const button = event.submitter;
  setBusy(button, true);
  byId("eas-output").textContent = "Running...";
  try {
    const result = await api("/api/eas/run", {
      method: "POST",
      body: JSON.stringify({
        fixture_id: "synthetic_thermal_enclosure_v1",
        mode: byId("eas-mode").value,
        problem_statement: byId("eas-problem").value,
      }),
    });
    byId("eas-output").textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    byId("eas-output").textContent = "Request failed: " + error.message;
  } finally {
    setBusy(button, false);
  }
}

async function runSis(event) {
  event.preventDefault();
  const button = event.submitter;
  setBusy(button, true);
  byId("sis-output").textContent = "Running...";
  try {
    const result = await api("/api/sis/run", {
      method: "POST",
      body: JSON.stringify({
        fixture_id: "synthetic_inspection_scheduler_v1",
        mode: byId("sis-mode").value,
        problem_statement: byId("sis-problem").value,
        constraints: [
          "Use synthetic inputs only",
          "Require independent validation",
        ],
      }),
    });
    byId("sis-output").textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    byId("sis-output").textContent = "Request failed: " + error.message;
  } finally {
    setBusy(button, false);
  }
}

function renderSensory(data) {
  const state = data.state || data;
  runtime.micActive = Boolean(state.hearing_active);
  runtime.cameraActive = Boolean(state.camera_active);
  if (data.voice) {
    runtime.speaking = Boolean(data.voice.is_speaking);
  }
  const latest = state.latest_interpretation || data.interpretation;
  if (latest && latest.priority) {
    runtime.attention = latest.priority;
  }
  byId("mic-indicator").textContent =
    runtime.micActive ? "Microphone active" : "Microphone off";
  byId("mic-indicator").classList.toggle("is-active", runtime.micActive);
  byId("camera-indicator").textContent =
    runtime.cameraActive ? "Camera local preview active" : "Camera off";
  byId("camera-indicator").classList.toggle("is-active", runtime.cameraActive);
  byId("tts-indicator").textContent = runtime.speaking
    ? "TTS speaking"
    : "TTS idle";
  byId("tts-indicator").classList.toggle("is-active", runtime.speaking);
  byId("toggle-mic").textContent =
    runtime.micActive ? "Stop microphone" : "Start microphone";
  byId("toggle-camera").textContent =
    runtime.cameraActive
      ? "Stop local camera preview"
      : "Start local camera preview";
  byId("attention-state").textContent = runtime.attention;
  byId("sensory-output").textContent = JSON.stringify(data, null, 2);
}

async function refreshSensoryState() {
  const data = await api("/api/csc/state", { method: "GET" });
  renderSensory(data);
}

function mergeFloatChunks(chunks, length) {
  const merged = new Float32Array(length);
  let offset = 0;
  chunks.forEach((chunk) => {
    merged.set(chunk, offset);
    offset += chunk.length;
  });
  return merged;
}

function encodeWav(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeAscii = (offset, value) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };
  writeAscii(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeAscii(8, "WAVE");
  writeAscii(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeAscii(36, "data");
  view.setUint32(40, samples.length * 2, true);
  let offset = 44;
  samples.forEach((sample) => {
    const clamped = Math.max(-1, Math.min(1, sample));
    view.setInt16(
      offset,
      clamped < 0 ? clamped * 32768 : clamped * 32767,
      true
    );
    offset += 2;
  });
  return new Blob([buffer], { type: "audio/wav" });
}

async function postAudioChunk(samples, sampleRate) {
  try {
    const result = await api("/api/csc/audio", {
      method: "POST",
      headers: { "Content-Type": "audio/wav" },
      body: encodeWav(samples, sampleRate),
    });
    renderSensory(result);
  } catch (error) {
    byId("sensory-output").textContent =
      "Audio boundary error: " + error.message;
  }
}

function startAudioProcessor(stream) {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) {
    throw new Error("web_audio_unavailable");
  }
  const context = new AudioContextClass();
  const source = context.createMediaStreamSource(stream);
  const processor = context.createScriptProcessor(4096, 1, 1);
  const mute = context.createGain();
  mute.gain.value = 0;
  let chunks = [];
  let sampleCount = 0;
  const target = context.sampleRate * 5;
  processor.onaudioprocess = (audioEvent) => {
    if (!runtime.micActive) {
      return;
    }
    const data = new Float32Array(
      audioEvent.inputBuffer.getChannelData(0)
    );
    chunks.push(data);
    sampleCount += data.length;
    if (sampleCount >= target) {
      const complete = mergeFloatChunks(chunks, sampleCount);
      chunks = [];
      sampleCount = 0;
      postAudioChunk(complete, context.sampleRate);
    }
  };
  source.connect(processor);
  processor.connect(mute);
  mute.connect(context.destination);
  runtime.audio = { context, source, processor, mute, stream };
}

async function stopAudioCapture() {
  if (!runtime.audio) {
    return;
  }
  runtime.audio.stream.getTracks().forEach((track) => track.stop());
  runtime.audio.processor.disconnect();
  runtime.audio.source.disconnect();
  runtime.audio.mute.disconnect();
  await runtime.audio.context.close();
  runtime.audio = null;
}

function stopCameraCapture() {
  if (runtime.cameraStream) {
    runtime.cameraStream.getTracks().forEach((track) => track.stop());
  }
  runtime.cameraStream = null;
  runtime.cameraActive = false;
  const preview = byId("camera-preview");
  preview.srcObject = null;
  preview.hidden = true;
  byId("camera-indicator").textContent = "Camera off";
  byId("camera-indicator").classList.remove("is-active");
  byId("toggle-camera").textContent = "Start local camera preview";
}

async function toggleMicrophone() {
  const button = byId("toggle-mic");
  setBusy(button, true);
  try {
    if (runtime.micActive) {
      await stopAudioCapture();
      const data = await api("/api/csc/hearing", {
        method: "POST",
        body: JSON.stringify({ active: false }),
      });
      renderSensory(data);
    } else {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false,
      });
      startAudioProcessor(stream);
      const data = await api("/api/csc/hearing", {
        method: "POST",
        body: JSON.stringify({ active: true }),
      });
      renderSensory(data);
    }
  } catch (error) {
    await stopAudioCapture();
    byId("sensory-output").textContent =
      "Microphone boundary error: " + error.message;
  } finally {
    setBusy(button, false);
  }
}

async function toggleCamera() {
  const button = byId("toggle-camera");
  setBusy(button, true);
  const preview = byId("camera-preview");
  try {
    if (runtime.cameraActive) {
      stopCameraCapture();
      const data = await api("/api/csc/camera", {
        method: "POST",
        body: JSON.stringify({ active: false }),
      });
      renderSensory(data);
    } else {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: true,
      });
      runtime.cameraStream = stream;
      preview.srcObject = stream;
      preview.hidden = false;
      const data = await api("/api/csc/camera", {
        method: "POST",
        body: JSON.stringify({ active: true, local_preview_only: true }),
      });
      renderSensory(data);
    }
  } catch (error) {
    stopCameraCapture();
    byId("sensory-output").textContent =
      "Camera boundary error: " + error.message;
  } finally {
    setBusy(button, false);
  }
}

async function addTranscript(event) {
  event.preventDefault();
  const button = event.submitter;
  setBusy(button, true);
  try {
    const data = await api("/api/csc/transcript", {
      method: "POST",
      body: JSON.stringify({
        transcript: byId("transcript-input").value,
        speech_detected: true,
        source: "synthetic_text_fixture",
      }),
    });
    runtime.attention = data.event.attention;
    renderSensory(data);
  } catch (error) {
    byId("sensory-output").textContent = "Request failed: " + error.message;
  } finally {
    setBusy(button, false);
  }
}

function setSpeakingIndicator(active) {
  runtime.speaking = Boolean(active);
  byId("tts-indicator").textContent = active ? "TTS speaking" : "TTS idle";
  byId("tts-indicator").classList.toggle("is-active", Boolean(active));
}

async function markPlayback(active) {
  setSpeakingIndicator(active);
  try {
    await api("/api/csc/playback", {
      method: "POST",
      body: JSON.stringify({ active: Boolean(active) }),
    });
  } catch (error) {
    setSpeakingIndicator(false);
    byId("sensory-output").textContent =
      "Playback state error: " + error.message;
  }
}

async function synthesizeSpeech(event) {
  event.preventDefault();
  const button = event.submitter;
  const audio = byId("tts-audio");
  setBusy(button, true);
  byId("tts-indicator").textContent = "TTS requesting";
  try {
    const response = await fetch("/api/csc/tts", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": runtime.csrf,
      },
      body: JSON.stringify({ text: byId("tts-input").value }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error_code || data.error || "tts_request_failed");
    }
    const blob = await response.blob();
    if (runtime.ttsUrl) {
      URL.revokeObjectURL(runtime.ttsUrl);
    }
    runtime.ttsUrl = URL.createObjectURL(blob);
    audio.src = runtime.ttsUrl;
    audio.hidden = false;
    await audio.play();
  } catch (error) {
    setSpeakingIndicator(false);
    byId("sensory-output").textContent = "TTS boundary error: " + error.message;
  } finally {
    setBusy(button, false);
  }
}

async function interpretBuffer() {
  const button = byId("interpret-buffer");
  setBusy(button, true);
  try {
    const data = await api("/api/csc/interpret", {
      method: "POST",
      body: JSON.stringify({}),
    });
    runtime.attention = data.interpretation.priority || "background";
    renderSensory(data);
  } catch (error) {
    byId("sensory-output").textContent = "Request failed: " + error.message;
  } finally {
    setBusy(button, false);
  }
}

async function clearSensory() {
  const data = await api("/api/csc/clear", {
    method: "POST",
    body: JSON.stringify({}),
  });
  runtime.attention = "background";
  renderSensory(data);
}

async function loadEvidence() {
  const button = byId("load-evidence");
  setBusy(button, true);
  try {
    const data = await api("/api/evidence/manifest", { method: "GET" });
    byId("evidence-output").textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    byId("evidence-output").textContent =
      "Evidence unavailable: " + error.message;
  } finally {
    setBusy(button, false);
  }
}

function drawOrb() {
  const canvas = byId("voice-orb");
  if (!canvas) {
    return;
  }
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const center = width / 2;
  const time = performance.now() / 1000;
  const active = runtime.micActive || runtime.speaking;
  const pulse = active ? 8 + Math.sin(time * 4) * 5 : 2;
  const colors = {
    focused: "#4dc99f",
    peripheral: "#57a9c7",
    ignored: "#d76855",
    background: "#86979f",
  };
  context.clearRect(0, 0, width, width);
  context.fillStyle = "#1f282c";
  context.fillRect(0, 0, width, width);
  context.strokeStyle = colors[runtime.attention] || colors.background;
  context.lineWidth = 2;
  for (let ring = 0; ring < 4; ring += 1) {
    context.globalAlpha = 0.75 - ring * 0.14;
    context.beginPath();
    context.arc(center, center, 58 + ring * 24 + pulse, 0, Math.PI * 2);
    context.stroke();
  }
  context.globalAlpha = 1;
  context.fillStyle = colors[runtime.attention] || colors.background;
  context.beginPath();
  context.arc(center, center, 48 + pulse * 0.5, 0, Math.PI * 2);
  context.fill();
  context.strokeStyle = "#e7eff1";
  context.lineWidth = 2;
  context.beginPath();
  for (let x = -34; x <= 34; x += 2) {
    const y = Math.sin(x * 0.22 + time * (active ? 5 : 1)) * (active ? 9 : 3);
    if (x === -34) {
      context.moveTo(center + x, center + y);
    } else {
      context.lineTo(center + x, center + y);
    }
  }
  context.stroke();
  requestAnimationFrame(drawOrb);
}

function installHandlers() {
  installTabs();
  byId("chat-form").addEventListener("submit", runChat);
  byId("eas-form").addEventListener("submit", runEas);
  byId("sis-form").addEventListener("submit", runSis);
  byId("transcript-form").addEventListener("submit", addTranscript);
  byId("tts-form").addEventListener("submit", synthesizeSpeech);
  byId("toggle-mic").addEventListener("click", toggleMicrophone);
  byId("toggle-camera").addEventListener("click", toggleCamera);
  byId("interpret-buffer").addEventListener("click", interpretBuffer);
  byId("clear-buffer").addEventListener("click", clearSensory);
  byId("load-evidence").addEventListener("click", loadEvidence);
  byId("clear-chat").addEventListener("click", () => {
    byId("chat-output").replaceChildren();
  });
  byId("tts-audio").addEventListener("play", () => markPlayback(true));
  byId("tts-audio").addEventListener("pause", () => markPlayback(false));
  byId("tts-audio").addEventListener("ended", () => markPlayback(false));
}

document.addEventListener("DOMContentLoaded", async () => {
  installHandlers();
  drawOrb();
  try {
    await initializeSession();
  } catch (error) {
    byId("session-status").textContent = "Session unavailable";
    appendMessage("Runtime", error.message, "error-message");
  }
});

window.addEventListener("pagehide", () => {
  stopCameraCapture();
  if (runtime.audio) {
    runtime.audio.stream.getTracks().forEach((track) => track.stop());
  }
  if (runtime.ttsUrl) {
    URL.revokeObjectURL(runtime.ttsUrl);
  }
  if (runtime.csrf) {
    const options = (body) => ({
      method: "POST",
      credentials: "same-origin",
      keepalive: true,
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": runtime.csrf,
      },
      body: JSON.stringify(body),
    });
    fetch("/api/csc/hearing", options({ active: false })).catch(() => {});
    fetch("/api/csc/camera", options({ active: false })).catch(() => {});
    fetch("/api/csc/playback", options({ active: false })).catch(() => {});
  }
});
