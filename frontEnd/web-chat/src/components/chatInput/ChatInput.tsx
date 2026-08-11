import { useMemo, useState } from "react";
import { Input, Button, message as antdMessage, Spin } from "antd";
import { SendOutlined, PaperClipOutlined, LoadingOutlined } from "@ant-design/icons";
import styles from "../../assets/ChatInput.module.css";
import { uploadFile } from "../../api/file";
import AttachmentChip from "./AttachmentChip";
import type { AttachmentItem } from "../../types/message";

const { TextArea } = Input;

const ALLOWED_EXTENSIONS = new Set([
    "txt",
    "md",
    "markdown",
    "csv",
    "tsv",
    "log",
    "json",
    "yaml",
    "yml",
    "xml",
    "pdf",
    "doc",
    "docx",
    "rtf",
    "html",
    "htm",
    "rst"
]);


interface ChatInputProps {
    onSend: (content: string, attachments: AttachmentItem[]) => void;
}


function ChatInput({ onSend }: ChatInputProps) {
    const [content, setContent] = useState("");
    const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
    const [uploadingFiles, setUploadingFiles] = useState<string[]>([]);
    const [isDragging, setIsDragging] = useState(false);

    const hasAttachments = attachments.length > 0;
    const isUploading = uploadingFiles.length > 0;

    const normalizedAttachments = useMemo(
        () => attachments.map((item) => item.displayName).join(", "),
        [attachments]
    );

    const send = () => {
        if (isUploading) {
            antdMessage.info("文件还在上传，请稍等");
            return;
        }

        if (!content.trim() && attachments.length === 0) {
            return;
        }

        onSend(content, attachments);
        setContent("");
        setAttachments([]);
    };

    const isAllowedFile = (file: File) => {
        const ext = file.name.split(".").pop()?.toLowerCase() || "";
        return ALLOWED_EXTENSIONS.has(ext);
    };

    const isDuplicateInInput = (file: File) => {
        return attachments.some(item => item.originalName === file.name)
            || uploadingFiles.includes(file.name);
    };

    const handleDroppedFile = async (file: File) => {
        if (!isAllowedFile(file)) {
            antdMessage.warning("只允许上传常见文本、PDF、Word 等文档");
            return;
        }

        if (isDuplicateInInput(file)) {
            antdMessage.warning(`文件已在输入框中：${file.name}`);
            return;
        }

        setUploadingFiles(prev => [...prev, file.name]);

        try {
            const result: any = await uploadFile(file);
            setAttachments(prev => [
                ...prev,
                {
                    id: `${result.id}-${Date.now()}`,
                    fileId: result.id,
                    displayName: result.original_filename || file.name,
                    originalName: result.original_filename || file.name,
                    fileType: result.file_type || file.type || "unknown",
                    size: result.size ?? file.size
                }
            ]);
            antdMessage.success(`已添加文件：${file.name}`);
        } catch (error: any) {
            const status = error?.response?.status;
            if (status === 409) {
                antdMessage.warning(`知识库中已存在：${file.name}`);
            } else {
                antdMessage.error("文件上传失败");
            }
        } finally {
            setUploadingFiles(prev => prev.filter(name => name !== file.name));
        }
    };

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = Array.from(e.dataTransfer.files || []);
        for (const file of files) {
            await handleDroppedFile(file);
        }
    };

    const handlePickFiles = async (files: FileList | null) => {
        if (!files) {
            return;
        }

        for (const file of Array.from(files)) {
            await handleDroppedFile(file);
        }
    };

    return (
        <div className={styles.container}>
            <div
                className={`${styles.inputBox} ${isDragging ? styles.dragging : ""}`}
                onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
            >
                {(hasAttachments || isUploading) && (
                    <div className={styles.attachmentRow} title={normalizedAttachments}>
                        {attachments.map((item) => (
                            <AttachmentChip
                                key={item.id}
                                name={item.displayName}
                                onRemove={() => {
                                    setAttachments(prev => prev.filter(a => a.id !== item.id));
                                }}
                            />
                        ))}

                        {uploadingFiles.map((name) => (
                            <div key={name} className={styles.uploadingChip}>
                                <Spin size="small" indicator={<LoadingOutlined spin />} />
                                <span className={styles.attachmentName} title={name}>
                                    正在上传 {name}
                                </span>
                            </div>
                        ))}
                    </div>
                )}

                <div className={styles.inputRow}>
                    <TextArea
                        className={styles.textarea}
                        placeholder="有问题，尽管问"
                        autoSize={{
                            minRows: 1,
                            maxRows: 5
                        }}
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        onDrop={handleDrop}
                        onPressEnter={(e) => {
                            if (!e.shiftKey) {
                                e.preventDefault();
                                send();
                            }
                        }}
                    />

                    <div className={styles.actionGroup}>
                        <label className={styles.attachBtn} title="添加文件">
                            <PaperClipOutlined />
                            <input
                                type="file"
                                multiple
                                accept=".txt,.md,.markdown,.csv,.tsv,.log,.json,.yaml,.yml,.xml,.pdf,.doc,.docx,.rtf,.html,.htm,.rst"
                                className={styles.fileInput}
                                onChange={(e) => {
                                    handlePickFiles(e.target.files);
                                    e.currentTarget.value = "";
                                }}
                            />
                        </label>
                        <Button
                            className={styles.sendBtn}
                            type="primary"
                            shape="circle"
                            icon={<SendOutlined />}
                            onClick={send}
                            disabled={isUploading}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ChatInput;
