import { io } from "socket.io-client";

export function connectWebSocket() {
  const socket = io("http://localhost:3000", {
    transports: ["websocket"],
  });

  socket.on("connect", () => {
    console.log("[INFO] WebSocket connecté");
  });

  socket.on("disconnect", () => {
    console.log("[INFO] WebSocket déconnecté");
  });

  return socket;
}