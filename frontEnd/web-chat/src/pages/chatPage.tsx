import Sidebar from "../components/sidebar/Sidebar";
import ChatArea from "../components/chatArea/chatArea";
import KnowledgeBaseDrawer from "../components/knowledgeBase/KnowledgeBaseDrawer";
import ModelConfigModal from "../components/settings/ModelConfigModal";
import type { Conversation } from "../types/conversation";
import { Button, Drawer, Layout } from "antd";
import { DatabaseOutlined, MenuOutlined, PlusOutlined, SettingOutlined } from "@ant-design/icons";
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getAllConversations } from "../api/chat";
import { getModelConfig } from "../api/settings";
import { getCurrentUser } from "../api/auth";
import styles from "../assets/ChatPage.module.css";

const { Sider } = Layout;

function ChatPage() {
    const [collapsed, setCollapsed] = useState(true);
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [knowledgeOpen, setKnowledgeOpen] = useState(false);
    const [modelConfigOpen, setModelConfigOpen] = useState(false);
    const [modelConfigured, setModelConfigured] = useState(false);
    const [modelConfigReady, setModelConfigReady] = useState(false);
    const [username, setUsername] = useState(localStorage.getItem("username") || "");
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const navigate = useNavigate();
    const { conversationId } = useParams<{ conversationId: string }>();
    const activeConversationId = conversationId ? Number(conversationId) : null;

    useEffect(() => {
        const initConversation = async () => {
            await refreshConversations();
            await refreshModelConfig();
            await refreshCurrentUser();
        };

        initConversation();
    }, [conversationId]);

    useEffect(() => {
        const mediaQuery = window.matchMedia("(max-width: 720px)");
        const updateIsMobile = () => setIsMobile(mediaQuery.matches);

        updateIsMobile();
        mediaQuery.addEventListener("change", updateIsMobile);
        return () => mediaQuery.removeEventListener("change", updateIsMobile);
    }, []);

    const refreshCurrentUser = async () => {
        try {
            const res = await getCurrentUser() as any;
            const currentUser = res?.data || res;
            if (currentUser?.username) {
                setUsername(currentUser.username);
                localStorage.setItem("username", currentUser.username);
            }
        } catch (error) {
            setUsername(localStorage.getItem("username") || "");
        }
    };

    const refreshModelConfig = async () => {
        setModelConfigReady(false);
        try {
            const res = await getModelConfig() as any;
            const config = res?.data || res;
            setModelConfigured(Boolean(config?.configured));
        } catch (error) {
            setModelConfigured(false);
        } finally {
            setModelConfigReady(true);
        }
    };

    const switchConversation = (id: number) => {
        navigate(`/chat/${id}`);
        setMobileMenuOpen(false);
    };

    const refreshConversations = async () => {
        try {
            const resConversations = await getAllConversations() as any;
            const list = resConversations?.data?.conversations || resConversations?.conversations || [];
            setConversations(list);
        } catch (error) {
            console.error("刷新会话列表失败:", error);
        }
    };

    const handleCreateConversation = () => {
        navigate("/chat");
        setMobileMenuOpen(false);
    };

    const handleConversationCreated = async (newId: number) => {
        navigate(`/chat/${newId}`);
        await refreshConversations();
    };

    return (
        <Layout className={styles.page}>
            <div className={styles.mobileTopBar}>
                <Button
                    type="text"
                    shape="circle"
                    icon={<MenuOutlined />}
                    onClick={() => setMobileMenuOpen(true)}
                    aria-label="打开菜单"
                />
                <div className={styles.mobileTitle}>自定义AI助手</div>
                <div className={styles.mobileActions}>
                    <Button
                        type="text"
                        shape="circle"
                        icon={<DatabaseOutlined />}
                        onClick={() => setKnowledgeOpen(true)}
                        aria-label="知识库"
                    />
                    <Button
                        type="text"
                        shape="circle"
                        icon={<SettingOutlined />}
                        onClick={() => setModelConfigOpen(true)}
                        aria-label="系统设置"
                    />
                    <Button
                        type="text"
                        shape="circle"
                        icon={<PlusOutlined />}
                        onClick={handleCreateConversation}
                        aria-label="新建对话"
                    />
                </div>
            </div>

            {!isMobile && (
                <Sider
                    width={260}
                    collapsed={collapsed}
                    collapsedWidth={80}
                    className={styles.sider}
                >
                    <Sidebar
                        collapsed={collapsed}
                        conversations={conversations}
                        onToggle={() => setCollapsed(!collapsed)}
                        onOpenKnowledgeBase={() => setKnowledgeOpen(true)}
                        onOpenModelConfig={() => setModelConfigOpen(true)}
                        handleCreateConversation={handleCreateConversation}
                        handleSwitchConversation={switchConversation}
                    />
                </Sider>
            )}

            <ChatArea
                conversationId={activeConversationId}
                onConversationCreated={handleConversationCreated}
                onRefreshConversations={refreshConversations}
                username={username}
                modelConfigured={modelConfigured}
                modelConfigReady={modelConfigReady}
                onOpenModelConfig={() => setModelConfigOpen(true)}
            />

            <KnowledgeBaseDrawer
                open={knowledgeOpen}
                onClose={() => setKnowledgeOpen(false)}
            />

            <ModelConfigModal
                open={modelConfigOpen}
                onClose={() => {
                    setModelConfigOpen(false);
                    refreshModelConfig();
                }}
            />

            <Drawer
                open={mobileMenuOpen}
                onClose={() => setMobileMenuOpen(false)}
                placement="left"
                width="min(86vw, 320px)"
                closable={false}
                className={styles.mobileDrawer}
                styles={{
                    body: { padding: 0 },
                    content: { background: "#111113" }
                }}
            >
                <Sidebar
                    collapsed={false}
                    mobile
                    conversations={conversations}
                    onToggle={() => undefined}
                    onOpenKnowledgeBase={() => {
                        setMobileMenuOpen(false);
                        setKnowledgeOpen(true);
                    }}
                    onOpenModelConfig={() => {
                        setMobileMenuOpen(false);
                        setModelConfigOpen(true);
                    }}
                    handleCreateConversation={handleCreateConversation}
                    handleSwitchConversation={switchConversation}
                />
            </Drawer>
        </Layout>
    );
}

export default ChatPage;
