export interface KnowledgeFile {
    id: number;
    original_filename: string;
    storage_filename: string;
    file_type: string;
    created_at: string;
    size: number;
    status: "indexed" | "missing" | string;
}
