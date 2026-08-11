import type { LoginRequest } from "../types/auth";
import type { RegisterRequest } from "../types/auth";
import request from "./request";
export function register (
    data:RegisterRequest
){
    return request.post(
        "/api/auth/register",
        data
    )
}

export function login(
    data:LoginRequest
){
    return request.post(
        "/api/auth/login",
        data
    )
}