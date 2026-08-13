import { useCallback, useEffect, useRef, useState } from "react";
import { Anchor, Layout, message as antdMessage } from "antd";
import MessageList from "../messageList/MessageList";
import ChatInput from "../chatInput/ChatInput";
import SourcePreviewDrawer from "../sourcePreview/SourcePreviewDrawer";
import { createConversation, getMessages, sendMessage } from "../../api/chat";
import type { AttachmentItem, Message, MessageSource } from "../../types/message";

const { Content } = Layout;

interface ChatAreaProps {
    conversationId: number | null;
    onConversationCreated: (newId: number) => void;
    onRefreshConversations: () => void;
    username: string;
    modelConfigured: boolean;
    modelConfigReady: boolean;
    onOpenModelConfig: () => void;
}

function ChatArea({
    conversationId,
    onConversationCreated,
    onRefreshConversations,
    username,
    modelConfigured,
    modelConfigReady,
    onOpenModelConfig
}: ChatAreaProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [showAnchor, setShowAnchor] = useState(true);
    const [previewSource, setPreviewSource] = useState<MessageSource | null>(null);
    const isCreatingRef = useRef(false);

    useEffect(() => {
        const fetchMessages = async () => {
            if (!conversationId) {
                setMessages([]);
                return;
            }

            if (isCreatingRef.current) {
                return;
            }

            try {
                const res = await getMessages(conversationId) as any;
                const msgList = res?.data?.messages || res?.messages || [];
                setMessages(msgList);
            } catch (error) {
                console.error("获取聊天记录失败:", error);
            }
        };

        fetchMessages();
    }, [conversationId]);

    const handleSend = useCallback(async (content: string, attachments: AttachmentItem[]) => {
        let activeId = conversationId;
        const isNewChat = !activeId;

        if (!activeId) {
            try {
                isCreatingRef.current = true;
                const newConv = await createConversation();
                if (newConv && newConv.id) {
                    activeId = newConv.id;
                    onConversationCreated(activeId as number);
                } else {
                    isCreatingRef.current = false;
                    throw new Error("未能获取新会话 ID");
                }
            } catch (error) {
                isCreatingRef.current = false;
                antdMessage.error("创建对话失败，请重试");
                return;
            }
        }

        const userMessage: Message = {
            role: "user",
            content,
            attachments
        };
        setMessages(prev => [...prev, userMessage, { role: "assistant", content: "", isLoading: true }]);

        const requestMessages = {
            conversation_id: activeId as number,
            content,
            attachments
        };

        try {
            let receivedFirstChunk = false;
            await sendMessage(requestMessages, (chunk: { content?: string; sources?: MessageSource[] }) => {
                if (chunk.sources) {
                    setMessages(prev => {
                        const updated = [...prev];
                        const lastIndex = updated.length - 1;
                        updated[lastIndex] = {
                            ...updated[lastIndex],
                            sources: chunk.sources
                        };
                        return updated;
                    });
                    return;
                }

                if (!receivedFirstChunk) {
                    receivedFirstChunk = true;
                    setMessages(prev => {
                        const updated = [...prev];
                        const lastIndex = updated.length - 1;
                        updated[lastIndex] = {
                            ...updated[lastIndex],
                            isLoading: false
                        };
                        return updated;
                    });
                }

                setMessages(prev => {
                    const updated = [...prev];
                    const lastIndex = updated.length - 1;
                    updated[lastIndex] = {
                        ...updated[lastIndex],
                        content: updated[lastIndex].content + (chunk.content || "")
                    };
                    return updated;
                });
            });

            if (isNewChat) {
                onRefreshConversations();
            }
        } catch (error) {
            setMessages(prev => {
                const updated = [...prev];
                const lastIndex = updated.length - 1;
                if (updated[lastIndex]?.role === "assistant") {
                    updated[lastIndex] = {
                        ...updated[lastIndex],
                        isLoading: false
                    };
                }
                return updated;
            });
            antdMessage.error("发送失败，请重试");
        } finally {
            isCreatingRef.current = false;
        }
    }, [conversationId, onConversationCreated, onRefreshConversations]);

    const anchorItems = messages
        .map((msg, i) => {
            if (msg.role === "user") {
                const shortTitle = msg.content.length > 12 ? `${msg.content.slice(0, 12)}...` : msg.content;
                return {
                    key: `msg-${i}`,
                    href: `#msg-${i}`,
                    title: `Q:${shortTitle || "附件"}`
                };
            }
            return null;
        })
        .filter((item): item is NonNullable<typeof item> => item != null);

    const getScrollContainer = useCallback(
        () => document.getElementById("chat-scroll-container")!,
        []
    );

    useEffect(() => {
        const updateAnchorVisibility = () => {
            setShowAnchor(window.innerWidth >= 1360);
        };

        updateAnchorVisibility();
        window.addEventListener("resize", updateAnchorVisibility);
        return () => window.removeEventListener("resize", updateAnchorVisibility);
    }, []);

    const isEmptyChat = messages.length === 0;
    const modelDisabled = modelConfigReady && !modelConfigured;
    const disabledReason = modelDisabled ? "请先在设置中配置模型 API Key 后再开始对话" : undefined;

    return (
        <Layout style={{ height: "100%", width: "100%", background: "#18181b" }}>
            {showAnchor && anchorItems.length > 0 && (
                <div className="custom-anchor-wrapper" style={{
                    position: "fixed",
                    right: "24px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    zIndex: 100,
                    maxHeight: "60vh",
                    overflowY: "auto"
                }}>
                    <Anchor
                        targetOffset={60}
                        getContainer={getScrollContainer}
                        items={anchorItems}
                        affix={false}
                        style={{ background: "transparent" }}
                    />
                </div>
            )}
            <Content style={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                width: "100%",
                maxWidth: "880px",
                background: "#18181b",
                padding: "0 16px",
                margin: "0 auto"
            }}>
                {isEmptyChat ? (
                    <div className="empty-chat-shell">
                        <div className="empty-chat-center">
                            <h1 className="empty-chat-title">{username || "你好"}，我们开始吧</h1>
                            <div className="empty-chat-input">
                                <ChatInput
                                    onSend={handleSend}
                                    disabled={modelDisabled}
                                    disabledReason={disabledReason}
                                    placeholder={modelDisabled ? "请先配置模型" : "问点什么，或者拖入文件"}
                                />
                            </div>
                            {modelDisabled && (
                                <button className="empty-chat-config-btn" onClick={onOpenModelConfig}>
                                    去配置模型
                                </button>
                            )}
                        </div>
                    </div>
                ) : (
                    <>
                        <div style={{ flex: 1, overflow: "hidden", width: "100%", background: "#18181b" }}>
                            <MessageList
                                messages={messages}
                                onOpenSource={setPreviewSource}
                            />
                        </div>
                        <div style={{
                            background: "#18181b",
                            padding: "16px 0 24px 0",
                            width: "100%",
                            borderTop: "1px solid rgba(255, 255, 255, 0.02)",
                            display: "flex",
                            justifyContent: "center"
                        }}>
                            <div style={{ width: "100%", maxWidth: "880px", padding: "0 24px", boxSizing: "border-box" }}>
                                <ChatInput
                                    onSend={handleSend}
                                    disabled={modelDisabled}
                                    disabledReason={disabledReason}
                                    placeholder={modelDisabled ? "请先配置模型" : "有问题，尽管问"}
                                />
                            </div>
                        </div>
                    </>
                )}
            </Content>

            <SourcePreviewDrawer
                open={!!previewSource}
                source={previewSource}
                onClose={() => setPreviewSource(null)}
            />
        </Layout>
    );
}

export default ChatArea;
