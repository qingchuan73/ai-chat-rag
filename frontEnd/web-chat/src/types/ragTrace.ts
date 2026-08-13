import type { MessageSource } from "./message";

export interface RagTrace {
    id: number;
    conversation_id: number;
    question: string;
    rewritten_query?: string | null;
    question_type?: string | null;
    used_knowledge: boolean;
    expanded_queries: string[];
    retrieved_count: number;
    selected_sources: MessageSource[];
    prediction?: {
        level: "good" | "medium" | "weak" | "normal" | string;
        reason: string;
    };
    created_at: string;
}
