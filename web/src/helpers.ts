import type { UpdateMessage } from "./types";

export const PRESENTATION_DELAY_MS = 2500;
export const ACTION_PACING_MS = 140;

export const sleep = (milliseconds: number) =>
  new Promise((resolve) => window.setTimeout(resolve, milliseconds));

export const friendlyLabel = (value: string) =>
  value
    .replace(/_v0$/, "")
    .replace(/_poc$/, "")
    .replaceAll("_", " ")
    .replace(/\bppe\b/i, "PPE")
    .replace(/^./, (letter) => letter.toUpperCase());

export const receiveJson = (socket: WebSocket) =>
  new Promise<UpdateMessage>((resolve, reject) => {
    const handleMessage = (event: MessageEvent<string>) => {
      cleanup();
      resolve(JSON.parse(event.data) as UpdateMessage);
    };
    const handleError = () => {
      cleanup();
      reject(new Error("The browser lost its connection to the local backend."));
    };
    const cleanup = () => {
      socket.removeEventListener("message", handleMessage);
      socket.removeEventListener("error", handleError);
    };
    socket.addEventListener("message", handleMessage);
    socket.addEventListener("error", handleError);
  });

export const openSocket = (sessionId: string) =>
  new Promise<WebSocket>((resolve, reject) => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/sessions/${sessionId}`);
    socket.addEventListener("open", () => resolve(socket), { once: true });
    socket.addEventListener(
      "error",
      () => reject(new Error("Start the local FastAPI backend, then try again.")),
      { once: true },
    );
  });
