export interface ModelConfig {
    provider: string;
    base_url?: string | null;
    chat_model: string;
    api_key_masked: string;
    configured: boolean;
}

export interface ModelConfigPayload {
    api_key: string;
    base_url?: string | null;
    chat_model: string;
}
