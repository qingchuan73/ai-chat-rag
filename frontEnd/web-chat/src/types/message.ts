export interface Message {
    role:'user'|'assistant',    
    content:string,
    isLoading?: boolean,
    sources?: MessageSource[],
    attachments?: AttachmentItem[]
}

export interface MessageSource {
    file_id: number;
    filename: string;
    file_type?: string | null;
    chunk_index?: number;
    page?: number | null;
    similarity?: number;
}

export interface AttachmentItem {
    id: string;
    fileId: number;
    displayName: string;
    originalName: string;
    fileType: string;
    size: number;
}

export interface standardM {
    conversation_id:number
    content:string
    attachments?: AttachmentItem[]
}
