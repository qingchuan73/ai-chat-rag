import request from "./request";
import type { ModelConfigPayload } from "../types/modelConfig";


export function getModelConfig() {
    return request.get("/settings/model");
}


export function getModelConfigs() {
    return request.get("/settings/models");
}


export function saveModelConfig(data: ModelConfigPayload) {
    return request.post("/settings/model", data);
}


export function updateModelConfig(id: number, data: ModelConfigPayload) {
    return request.put(`/settings/model/${id}`, data);
}


export function setDefaultModelConfig(id: number) {
    return request.post(`/settings/model/${id}/default`);
}


export function deleteModelConfig() {
    return request.delete("/settings/model");
}


export function deleteModelConfigById(id: number) {
    return request.delete(`/settings/model/${id}`);
}
