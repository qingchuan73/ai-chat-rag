import request from "./request";
import type { ModelConfigPayload } from "../types/modelConfig";


export function getModelConfig() {
    return request.get("/settings/model");
}


export function saveModelConfig(data: ModelConfigPayload) {
    return request.post("/settings/model", data);
}


export function deleteModelConfig() {
    return request.delete("/settings/model");
}
