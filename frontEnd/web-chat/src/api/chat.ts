import request from "./request";
import { API_BASE_URL } from "./config";
import type { MessageSource, standardM } from "../types/message";


export function getStart() {
    return request.get("/");
}


export function getMessages(conversationId: number) {
    return request.get(`/api/conversation/${conversationId}/messages`);
}


export function getAllConversations() {
    return request.get("/api/conversation");
}


export async function createConversation() {
    const data: any = await request.post("/api/conversation");

    localStorage.setItem("conversation_id", data.id);
    return data;
}


export async function sendMessage(
    message: standardM,
    onChunk: (chunk: { content?: string; sources?: MessageSource[] }) => void
) {
    const token = localStorage.getItem("token");

    const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token ? `Bearer ${token}` : ""
        },
        body: JSON.stringify(message)
    });

    if (!res.ok) {
        throw new Error(`Chat request failed: ${res.status}`);
    }

    if (!res.body) {
        throw new Error("No response body");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) {
            break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith("data:")) {
                const contentJson = trimmedLine.substring(5).trim();

                if (contentJson) {
                    try {
                        const parsedText = JSON.parse(contentJson);
                        onChunk(parsedText);
                    } catch (e) {
                        console.error("解析 SSE 数据失败:", e, contentJson);
                    }
                }
            }
        }
    }
}
