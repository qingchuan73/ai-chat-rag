import request from "./request";
import { API_BASE_URL } from "./config";

const FILE_OPERATION_TIMEOUT = 120000;

export function uploadFile(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return request.post("/api/file/upload", formData, {
        timeout: FILE_OPERATION_TIMEOUT
    });
}

export function getKnowledgeFiles() {
    return request.get("/api/file");
}

export function deleteKnowledgeFile(fileId: number) {
    return request.delete(`/api/file/${fileId}`);
}

export function reindexKnowledgeFile(fileId: number) {
    return request.post(`/api/file/${fileId}/reindex`, {}, {
        timeout: FILE_OPERATION_TIMEOUT
    });
}

export async function getKnowledgeFileBlob(fileId: number) {
    const token = localStorage.getItem("token");
    const response = await fetch(`${API_BASE_URL}/api/file/${fileId}/preview`, {
        headers: {
            Authorization: token ? `Bearer ${token}` : ""
        }
    });

    if (!response.ok) {
        throw new Error(`Preview request failed: ${response.status}`);
    }

    return response.blob();
}
