import Sidebar from "../components/sidebar/Sidebar";
import ChatArea from "../components/chatArea/chatArea";
import KnowledgeBaseDrawer from "../components/knowledgeBase/KnowledgeBaseDrawer";
import ModelConfigModal from "../components/settings/ModelConfigModal";
import type { Conversation } from "../types/conversation";
import { Layout } from "antd";
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getAllConversations } from "../api/chat";
import { getModelConfig } from "../api/settings";
import { getCurrentUser } from "../api/auth";

const { Sider } = Layout;

function ChatPage() {
    const [collapsed, setCollapsed] = useState(true);
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [knowledgeOpen, setKnowledgeOpen] = useState(false);
    const [modelConfigOpen, setModelConfigOpen] = useState(false);
    const [modelConfigured, setModelConfigured] = useState(false);
    const [modelConfigReady, setModelConfigReady] = useState(false);
    const [username, setUsername] = useState(localStorage.getItem("username") || "");
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
    };

    const handleConversationCreated = async (newId: number) => {
        navigate(`/chat/${newId}`);
        await refreshConversations();
    };

    return (
        <Layout style={{ height: "100vh", background: "#18181b", overflow: "hidden" }}>
            <Sider
                width={260}
                collapsed={collapsed}
                collapsedWidth={80}
                style={{
                    background: "#111113",
                    borderRight: "1px solid rgba(255, 255, 255, 0.04)",
                    height: "100vh"
                }}
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
        </Layout>
    );
}

export default ChatPage;
