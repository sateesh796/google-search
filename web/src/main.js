import { Room, RoomEvent, Track } from "livekit-client";
import "./style.css";

const connectButton = document.querySelector("#connectButton");
const disconnectButton = document.querySelector("#disconnectButton");
const muteButton = document.querySelector("#muteButton");
const statusText = document.querySelector("#statusText");
const sessionText = document.querySelector("#sessionText");
const sessionClock = document.querySelector("#sessionClock");
const stageCaption = document.querySelector("#stageCaption");
const voiceStage = document.querySelector("#voiceStage");
const micIndicator = document.querySelector("#micIndicator");
const micText = document.querySelector("#micText");
const outputIndicator = document.querySelector("#outputIndicator");
const outputText = document.querySelector("#outputText");
const roomLabel = document.querySelector("#roomLabel");
const waveform = document.querySelector("#waveform");
const messageForm = document.querySelector("#messageForm");
const messageInput = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const messages = document.querySelector("#messages");
const messageCount = document.querySelector("#messageCount");

for (let index = 0; index < 37; index += 1) {
  const bar = document.createElement("span");
  bar.style.setProperty("--bar-index", index);
  waveform.append(bar);
}

let room;
let microphoneEnabled = false;
let startedAt;
let clockTimer;
const audioElements = new Set();
let displayedMessageCount = 0;

function appendMessage(sender, text, isUser = false) {
  if (!text.trim()) return;
  messages.querySelector(".empty-messages")?.remove();

  const message = document.createElement("article");
  message.className = `message${isUser ? " message-user" : ""}`;
  const label = document.createElement("p");
  label.className = "message-sender";
  label.textContent = sender;
  const body = document.createElement("p");
  body.className = "message-body";
  body.textContent = text;
  message.append(label, body);
  messages.append(message);
  messages.scrollTop = messages.scrollHeight;
  displayedMessageCount += 1;
  messageCount.textContent = `${displayedMessageCount} ${displayedMessageCount === 1 ? "message" : "messages"}`;
}

function setStatus(message, state = "idle") {
  statusText.textContent = message;
  voiceStage.dataset.state = state;
}

function updateClock() {
  if (!startedAt) return;
  const elapsed = Math.floor((Date.now() - startedAt) / 1000);
  const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const seconds = String(elapsed % 60).padStart(2, "0");
  sessionClock.textContent = `${minutes}:${seconds}`;
}

function setConnected(connected) {
  connectButton.disabled = connected;
  disconnectButton.disabled = !connected;
  muteButton.disabled = !connected;
  messageInput.disabled = !connected;
  sendButton.disabled = !connected;
  sessionText.textContent = connected ? "Connected" : "Ready";
  micText.textContent = connected && microphoneEnabled ? "ON" : "OFF";
  micIndicator.classList.toggle("is-on", connected && microphoneEnabled);
  roomLabel.textContent = connected ? "Private room" : "No room connected";
  if (connected) {
    startedAt = Date.now();
    sessionClock.textContent = "00:00";
    clockTimer = window.setInterval(updateClock, 1000);
  } else {
    startedAt = undefined;
    window.clearInterval(clockTimer);
    sessionClock.textContent = "00:00";
    microphoneEnabled = false;
    muteButton.textContent = "Mute microphone";
  }
}

function removeAudioTracks() {
  for (const element of audioElements) {
    element.pause();
    element.srcObject = null;
    element.remove();
  }
  audioElements.clear();
  outputIndicator.classList.remove("is-on");
  outputText.textContent = "READY";
}

async function disconnect() {
  if (room) {
    await room.disconnect();
    room = undefined;
  }
  removeAudioTracks();
  setConnected(false);
  setStatus("Offline");
  stageCaption.textContent = "VOICE CHANNEL IDLE";
}

connectButton.addEventListener("click", async () => {
  connectButton.disabled = true;
  setStatus("Connecting", "connecting");
  stageCaption.textContent = "ESTABLISHING VOICE CHANNEL";

  try {
    const response = await fetch("/api/session", { method: "POST" });
    const session = await response.json();
    if (!response.ok) {
      throw new Error(session.detail || "Could not create a LiveKit session.");
    }

    room = new Room({ adaptiveStream: true, dynacast: true });
    const activeRoom = room;

    activeRoom.on(RoomEvent.TrackSubscribed, (track, _publication, participant) => {
      if (track.kind !== Track.Kind.Audio) return;

      const audio = track.attach();
      audio.autoplay = true;
      audio.playsInline = true;
      audio.className = "remote-audio";
      document.body.append(audio);
      audioElements.add(audio);
      outputIndicator.classList.add("is-on");
      outputText.textContent = "CONNECTED";
      setStatus(`${participant.identity} connected`, "connected");
      audio.play().catch(() => {
        setStatus("Click the page to allow voice playback", "connected");
      });
    });

    activeRoom.registerTextStreamHandler("lk.transcription", async (reader, participantInfo) => {
      try {
        const text = await reader.readAll();
        const isUser = participantInfo.identity === activeRoom.localParticipant.identity;
        appendMessage(isUser ? "You" : "Assistant", text, isUser);
      } catch {
        setStatus("A transcript could not be loaded", "connected");
      }
    });

    activeRoom.on(RoomEvent.TrackUnsubscribed, (track) => {
      track.detach().forEach((element) => {
        audioElements.delete(element);
        element.remove();
      });
      if (audioElements.size === 0) {
        outputIndicator.classList.remove("is-on");
        outputText.textContent = "READY";
        setStatus("Connected", "connected");
      }
    });

    activeRoom.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
      const assistantSpeaking = speakers.some((participant) => !participant.isLocal);
      if (assistantSpeaking) {
        setStatus("Assistant speaking", "speaking");
        stageCaption.textContent = "ASSISTANT SPEAKING";
      } else if (activeRoom.state === "connected") {
        setStatus("Listening", "connected");
        stageCaption.textContent = "VOICE CHANNEL ACTIVE";
      }
    });

    activeRoom.on(RoomEvent.Disconnected, () => {
      if (room === activeRoom) {
        room = undefined;
        removeAudioTracks();
        setConnected(false);
        setStatus("Disconnected");
        stageCaption.textContent = "VOICE CHANNEL IDLE";
      }
    });

    await activeRoom.connect(session.server_url, session.participant_token);
    setConnected(true);
    roomLabel.textContent = session.room_name;
    try {
      await activeRoom.localParticipant.setMicrophoneEnabled(true);
      microphoneEnabled = true;
      setStatus("Listening", "connected");
      stageCaption.textContent = "VOICE CHANNEL ACTIVE";
      micText.textContent = "ON";
      micIndicator.classList.add("is-on");
      muteButton.textContent = "Mute microphone";
    } catch {
      microphoneEnabled = false;
      micText.textContent = "UNAVAILABLE";
      micIndicator.classList.remove("is-on");
      setStatus("Connected; type a reply", "connected");
      sessionText.textContent = "Connected without microphone";
      stageCaption.textContent = "TYPE A MESSAGE TO REPLY";
      messageInput.focus();
    }
  } catch (error) {
    await disconnect();
    const message = error instanceof Error ? error.message : "Unable to connect.";
    setStatus(message, "error");
    sessionText.textContent = "Connection failed";
    stageCaption.textContent = "CHECK CONNECTION AND MICROPHONE";
  } finally {
    connectButton.disabled = Boolean(room);
  }
});

muteButton.addEventListener("click", async () => {
  if (!room) return;
  try {
    microphoneEnabled = !microphoneEnabled;
    await room.localParticipant.setMicrophoneEnabled(microphoneEnabled);
    micText.textContent = microphoneEnabled ? "ON" : "MUTED";
    micIndicator.classList.toggle("is-on", microphoneEnabled);
    muteButton.textContent = microphoneEnabled ? "Mute microphone" : "Unmute microphone";
  } catch (error) {
    microphoneEnabled = !microphoneEnabled;
    const message = error instanceof Error ? error.message : "Could not change microphone.";
    setStatus(message, "error");
  }
});

disconnectButton.addEventListener("click", disconnect);

messageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = messageInput.value.trim();
  if (!room || !text) return;

  sendButton.disabled = true;
  try {
    await room.localParticipant.sendText(text, { topic: "lk.chat" });
    appendMessage("You", text, true);
    messageInput.value = "";
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not send the message.";
    setStatus(message, "error");
  } finally {
    sendButton.disabled = !room;
  }
});