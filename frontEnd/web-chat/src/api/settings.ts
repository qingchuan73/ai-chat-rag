import request from "./request";
import type { ModelConfigPayload } from "../types/modelConfig";


export function getModelConfig() {
    return request.get("/api/settings/model");
}


export function saveModelConfig(data: ModelConfigPayload) {
    return request.post("/api/settings/model", data);
}


export function deleteModelConfig() {
    return request.delete("/api/settings/model");
}
