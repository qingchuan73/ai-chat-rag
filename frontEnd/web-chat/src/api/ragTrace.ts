import request from "./request";

export function getRagTraces(limit = 10) {
    return request.get(`/rag-trace?limit=${limit}`);
}
