export interface ModelConfig {
    id?: number | null;
    name?: string | null;
    provider: string;
    base_url?: string | null;
    chat_model: string;
    image_model?: string | null;
    api_key_masked: string;
    configured: boolean;
    is_default?: boolean;
}

export interface ModelConfigPayload {
    api_key: string;
    name?: string | null;
    base_url?: string | null;
    chat_model: string;
    image_model?: string | null;
}
