import type { LoginRequest } from "../types/auth";
import type { RegisterRequest } from "../types/auth";
import request from "./request";
export function register (
    data:RegisterRequest
){
    return request.post(
        "/auth/register",
        data
    )
}

export function login(
    data:LoginRequest
){
    return request.post(
        "/auth/login",
        data
    )
}

export function getCurrentUser() {
    return request.get("/auth/me");
}
