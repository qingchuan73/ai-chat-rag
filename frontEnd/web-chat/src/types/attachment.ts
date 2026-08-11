export interface AttachmentItem {
    id: string;
    fileId: number;
    displayName: string;
    originalName: string;
    fileType: string;
    size: number;
}

export interface ChatRequestPayload {
    content: string;
    attachments: AttachmentItem[];
}
