import {
    DatabaseOutlined,
    MessageOutlined,
    PlusOutlined,
    SettingOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    QuestionCircleOutlined
} from "@ant-design/icons";
import styles from "../../assets/Sidebar.module.css";
import type { Conversation } from "../../types/conversation";


interface SidebarProps {
    collapsed: boolean;
    conversations: Conversation[];
    onToggle: () => void;
    onOpenKnowledgeBase: () => void;
    onOpenModelConfig: () => void;
    handleCreateConversation: () => void;
    handleSwitchConversation: (id: number) => void;
}


function Sidebar({
    collapsed,
    onToggle,
    onOpenKnowledgeBase,
    onOpenModelConfig,
    handleCreateConversation,
    conversations,
    handleSwitchConversation,
}: SidebarProps) {
    const normalHistory = [...conversations].sort((a, b) => b.id - a.id);
    const displayHistory = collapsed ? normalHistory.slice(0, 5) : normalHistory;

    return (
        <div className={`${styles.container} ${collapsed ? styles.collapsed : ""}`}>
            <div className={styles.header}>
                <span className={styles.logoText}>DeepSeek GPT</span>
                <button className={styles.toggleBtn} onClick={onToggle}>
                    {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                </button>
            </div>

            <div className={styles.actionArea}>
                <button className={styles.newChatBtn} title="新建对话" onClick={handleCreateConversation}>
                    <PlusOutlined className={styles.actionIcon} />
                    <span className={styles.btnText}>新建对话</span>
                </button>
            </div>

            <div className={styles.menuList}>
                <div className={styles.sectionTitle}>历史记录</div>
                <div className={styles.menuItemsWrapper}>
                    {displayHistory.map((item) => (
                        <div
                            key={item.id}
                            className={styles.menuItem}
                            title={item.title}
                            onClick={() => handleSwitchConversation(item.id)}
                        >
                            <MessageOutlined className={styles.menuIcon} />
                            <span className={styles.menuText}>{item.title}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className={styles.footer}>
                <div className={styles.menuItem} title="帮助与反馈">
                    <QuestionCircleOutlined className={styles.menuIcon} />
                    <span className={styles.menuText}>帮助与反馈</span>
                </div>

                <div className={styles.menuItem} title="知识库" onClick={onOpenKnowledgeBase}>
                    <DatabaseOutlined className={styles.menuIcon} />
                    <span className={styles.menuText}>知识库</span>
                </div>

                <div className={styles.menuItem} title="系统设置" onClick={onOpenModelConfig}>
                    <SettingOutlined className={styles.menuIcon} />
                    <span className={styles.menuText}>系统设置</span>
                </div>
            </div>
        </div>
    );
}

export default Sidebar;
