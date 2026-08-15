import { useEffect, useRef } from "react";
import type { AttachmentItem, GeneratedImage, Message, MessageSource } from "../../types/message";
import MarkdownRender from "./MarkDownRender";
import styles from "../../assets/MessageList.module.css";
import { CopyOutlined, FileTextOutlined } from "@ant-design/icons";
import { message as antdMessage, Spin, Tag } from "antd";
import { API_BASE_URL } from "../../api/config";


interface MessageListProps {
    messages: Message[];
    onOpenSource: (source: MessageSource) => void;
}


interface MessageItemProps {
    index: number;
    content: string;
    role: string;
    isLoading?: boolean;
    loadingType?: "text" | "image";
    image?: GeneratedImage;
    sources?: MessageSource[];
    attachments?: AttachmentItem[];
    onOpenSource: (source: MessageSource) => void;
}



function ImageGeneratingLoader() {
    return (
        <div className={styles.imageGenerating}>
            <div className={styles.imageGeneratingFrame}>
                <div className={styles.imageGeneratingSweep} />
                <div className={styles.imageGeneratingSparkles}>
                    <span />
                    <span />
                    <span />
                </div>
            </div>
            <div className={styles.imageGeneratingText}>正在生成图片...</div>
        </div>
    );
}


function GeneratedImageView({ image }: { image: GeneratedImage }) {
    const imageUrl = image.url.startsWith("/api/")
        ? `${API_BASE_URL}${image.url.slice(4)}`
        : image.url;

    return (
        <figure className={styles.generatedImageCard}>
            <img src={imageUrl} alt={image.prompt || "生成图片"} className={styles.generatedImage} />
            {image.prompt && <figcaption>{image.prompt}</figcaption>}
        </figure>
    );
}


function formatSource(source: MessageSource) {
    if (source.page) {
        return `${source.filename} - 第 ${source.page} 页`;
    }

    if (typeof source.chunk_index === "number") {
        return `${source.filename} - 片段 ${source.chunk_index}`;
    }

    return source.filename;
}


function getUniqueSources(sources?: MessageSource[]) {
    if (!sources?.length) {
        return [];
    }

    const seen = new Set<string>();
    const uniqueSources: MessageSource[] = [];

    for (const source of sources) {
        const key = source.page
            ? `${source.filename}-${source.page}`
            : `${source.filename}-${source.chunk_index}`;

        if (seen.has(key)) {
            continue;
        }

        seen.add(key);
        uniqueSources.push(source);
    }

    return uniqueSources;
}


function UserAttachmentList({ attachments }: { attachments?: AttachmentItem[] }) {
    if (!attachments?.length) {
        return null;
    }

    return (
        <div className={styles.userAttachmentList}>
            {attachments.map((attachment) => (
                <div key={attachment.id || attachment.fileId} className={styles.userAttachmentChip}>
                    <FileTextOutlined className={styles.userAttachmentIcon} />
                    <span className={styles.userAttachmentName} title={attachment.displayName}>
                        {attachment.displayName}
                    </span>
                </div>
            ))}
        </div>
    );
}


function MessageItem({
    index,
    content,
    role,
    isLoading,
    loadingType,
    image,
    sources,
    attachments,
    onOpenSource
}: MessageItemProps) {
    const isUser = role === "user";
    const displaySources = getUniqueSources(sources);

    const copyText = async (text: string) => {
        if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(text);
            return;
        }

        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        textarea.style.top = "0";
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();

        try {
            document.execCommand("copy");
        } finally {
            document.body.removeChild(textarea);
        }
    };

    const handleCopy = () => {
        copyText(content).then(() => {
            antdMessage.success("已复制到剪贴板");
        }).catch(() => {
            antdMessage.error("复制失败");
        });
    };

    return (
        <div
            id={`msg-${index}`}
            className={`${styles.messageRow} ${isUser ? styles.userRow : styles.assistantRow}`}
        >
            {isUser ? (
                <div className={styles.userBubbleContainer}>
                    <div className={styles.userBubble}>
                        <UserAttachmentList attachments={attachments} />
                        {content ? <p className={styles.userText}>{content}</p> : null}
                    </div>

                    <div className={styles.userActions}>
                        <button onClick={handleCopy} title="复制"><CopyOutlined /></button>
                    </div>
                </div>
            ) : (
                <div className={styles.assistantContent}>
                    <div className={styles.markdownWrapper}>
                        {isLoading && loadingType === "image" ? (
                            <ImageGeneratingLoader />
                        ) : image ? (
                            <GeneratedImageView image={image} />
                        ) : isLoading && !content ? (
                            <Spin size="small" />
                        ) : (
                            <MarkdownRender content={content} />
                        )}
                    </div>
                    {!!displaySources.length && (
                        <div className={styles.sourceList}>
                            <div className={styles.sourceTitle}>引用来源</div>
                            {displaySources.map((source, sourceIndex) => (
                                <Tag
                                    key={`${source.filename}-${source.page || source.chunk_index}-${sourceIndex}`}
                                    className={styles.sourceTag}
                                    onClick={() => onOpenSource(source)}
                                >
                                    {formatSource(source)}
                                </Tag>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}


function MessageList({ messages, onOpenSource }: MessageListProps) {
    const containerRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const container = containerRef.current;
        if (!container) {
            return;
        }

        requestAnimationFrame(() => {
            container.scrollTop = container.scrollHeight;
        });
    }, [messages]);

    return (
        <div id="chat-scroll-container" ref={containerRef} className={styles.container}>
            <div className={styles.listInner}>
                {messages.map((message, index) => (
                    <MessageItem
                        key={index}
                        index={index}
                        content={message.content}
                        role={message.role}
                        isLoading={message.isLoading}
                        loadingType={message.loadingType}
                        image={message.image}
                        sources={message.sources}
                        attachments={message.attachments}
                        onOpenSource={onOpenSource}
                    />
                ))}
            </div>
        </div>
    );
}

export default MessageList;
