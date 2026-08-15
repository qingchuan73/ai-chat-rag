import { useEffect, useState } from "react";
import { Button, Form, Input, Modal, Space, Tag, message } from "antd";
import { LogoutOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import {
    deleteModelConfigById,
    getModelConfig,
    getModelConfigs,
    saveModelConfig,
    setDefaultModelConfig,
    updateModelConfig
} from "../../api/settings";
import type { ModelConfig } from "../../types/modelConfig";
import styles from "../../assets/ModelConfigModal.module.css";

interface ModelConfigModalProps {
    open: boolean;
    onClose: () => void;
}

function ModelConfigModal({ open, onClose }: ModelConfigModalProps) {
    const [form] = Form.useForm();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [config, setConfig] = useState<ModelConfig | null>(null);
    const [configs, setConfigs] = useState<ModelConfig[]>([]);
    const [editingConfig, setEditingConfig] = useState<ModelConfig | null>(null);
    const [activePanel, setActivePanel] = useState<"settings" | "models">("settings");

    const loadConfig = async () => {
        setLoading(true);

        try {
            const [currentResult, listResult] = await Promise.all([
                getModelConfig(),
                getModelConfigs()
            ]) as any[];
            const nextConfig = currentResult?.data || currentResult;
            const listPayload = listResult?.data || listResult;
            const nextConfigs = listPayload?.configs || [];

            setConfig(nextConfig);
            setConfigs(nextConfigs);
        } catch (error) {
            message.error("获取模型配置失败");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (open) {
            form.resetFields();
            setEditingConfig(null);
            loadConfig();
        }
    }, [open]);

    const handleSelectModel = async (item: ModelConfig) => {
        if (!item.is_default) {
            await handleSetDefault(item.id);
        }
    };

    const handleEditModel = (item: ModelConfig) => {
        setEditingConfig(item);
        form.setFieldsValue({
            name: item.name || item.chat_model,
            base_url: item.base_url || "",
            chat_model: item.chat_model,
            image_model: item.image_model || "",
            api_key: ""
        });
        setActivePanel("settings");
    };

    const handleSave = async () => {
        const values = await form.validateFields();
        setLoading(true);

        try {
            const payload = {
                api_key: values.api_key,
                name: values.name || values.chat_model,
                base_url: values.base_url || null,
                chat_model: values.chat_model,
                image_model: values.image_model || null
            };
            const result = editingConfig?.id
                ? await updateModelConfig(editingConfig.id, payload) as any
                : await saveModelConfig(payload) as any;
            setConfig(result?.data || result);
            form.resetFields();
            setEditingConfig(null);
            message.success(editingConfig?.id ? "模型配置已更新" : "模型配置已添加");
            await loadConfig();
        } catch (error) {
            message.error("保存模型配置失败");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id?: number | null) => {
        if (!id) {
            return;
        }

        setLoading(true);

        try {
            await deleteModelConfigById(id);
            message.success("模型配置已删除");
            await loadConfig();
        } catch (error) {
            message.error("删除模型配置失败");
        } finally {
            setLoading(false);
        }
    };

    const handleSetDefault = async (id?: number | null) => {
        if (!id) {
            return;
        }

        setLoading(true);

        try {
            await setDefaultModelConfig(id);
            message.success("已切换当前使用模型");
            await loadConfig();
        } catch (error) {
            message.error("切换模型失败");
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("conversation_id");
        message.success("已退出登录");
        onClose();
        navigate("/login", { replace: true });
    };

    return (
        <Modal
            className={styles.modal}
            rootClassName={styles.modalRoot}
            wrapClassName={styles.modalWrap}
            title={
                <div className={styles.modalTitleBar}>
                    <button
                        type="button"
                        className={`${styles.modalTitleButton} ${activePanel === "settings" ? styles.modalTitleButtonActive : ""}`}
                        onClick={() => setActivePanel("settings")}
                    >
                        系统设置
                    </button>
                    <span className={styles.modalTitleDivider}>/</span>
                    <button
                        type="button"
                        className={`${styles.modalTitleButton} ${activePanel === "models" ? styles.modalTitleButtonActive : ""}`}
                        onClick={() => setActivePanel("models")}
                    >
                        模型管理
                    </button>
                </div>
            }
            open={open}
            onCancel={onClose}
            maskClosable={false}
            centered
            styles={{
                root: {
                    color: "#e4e4e7"
                },
                header: {
                    background: "#18181b",
                    borderBottom: "1px solid rgba(255, 255, 255, 0.06)"
                },
                body: {
                    background: "#18181b"
                },
                footer: {
                    background: "#18181b",
                    borderTop: "1px solid rgba(255, 255, 255, 0.06)"
                }
            }}
            footer={
                activePanel === "settings" ? (
                    <Space>
                        <Button type="primary" onClick={handleSave} loading={loading}>
                            保存配置
                        </Button>
                    </Space>
                ) : null
            }
        >
            <div className={styles.panelStage}>
                <div className={`${styles.panelPane} ${activePanel === "settings" ? styles.panelPaneActive : ""}`}>
                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <h3 className={styles.sectionTitle}>{editingConfig ? "编辑模型" : "添加模型"}</h3>
                            {config?.configured && (
                                <span className={styles.status}>当前：{config.name || config.chat_model}</span>
                            )}
                        </div>

                        <p className={styles.hint}>
                            当前仅支持 OpenAI 兼容协议。可添加模型，也可在模型管理页面双击模型进入编辑。
                        </p>

                        <Form
                            form={form}
                            layout="vertical"
                        >
                            <Form.Item
                                label="配置名称"
                                name="name"
                                rules={[{ required: true, message: "请输入配置名称" }]}
                            >
                                <Input placeholder="例如：OpenAI 主力模型" />
                            </Form.Item>

                            <Form.Item
                                label="API Key"
                                name="api_key"
                                rules={[{ required: true, message: "请输入 API Key" }]}
                            >
                                <Input.Password placeholder="sk-..." autoComplete="off" />
                            </Form.Item>

                            <Form.Item label="Base URL" name="base_url">
                                <Input placeholder="https://api.openai.com/v1 或兼容服务地址" />
                            </Form.Item>

                            <Form.Item
                                label="Chat Model"
                                name="chat_model"
                                rules={[{ required: true, message: "请输入模型名称" }]}
                            >
                                <Input placeholder="例如：gpt-4o-mini、deepseek-chat、qwen-plus" />
                            </Form.Item>

                            <Form.Item label="生图模型（可选）" name="image_model">
                                <Input placeholder="例如：gpt-image-1、dall-e-3 或服务商的图片模型" />
                            </Form.Item>

                        </Form>

                        {config?.configured && (
                            <div className={styles.currentHint}>
                                {editingConfig
                                    ? "保存后会保留原来的当前使用状态。"
                                    : "添加后不会自动切换；需要到模型管理页面点击模型进行切换。"}
                            </div>
                        )}
                    </section>

                    <section className={styles.dangerSection}>
                        <div>
                            <h3 className={styles.sectionTitle}>账号</h3>
                            <p className={styles.hint}>退出后会清除本地登录状态，需要重新登录才能继续使用。</p>
                        </div>

                        <Button className={styles.logoutButton} danger icon={<LogoutOutlined />} onClick={handleLogout}>
                            退出登录
                        </Button>
                    </section>
                </div>

                <div className={`${styles.panelPane} ${activePanel === "models" ? styles.panelPaneActive : ""}`}>
                    <section className={styles.section}>
                        <div className={styles.sectionHeader}>
                            <h3 className={styles.sectionTitle}>模型管理</h3>
                            {config?.configured && (
                                <span className={styles.status}>当前：{config.name || config.chat_model}</span>
                            )}
                        </div>

                        <p className={styles.hint}>
                            单击切换当前使用模型，双击进入编辑。
                        </p>

                        <div className={styles.modelList}>
                            {configs.map(item => (
                                <div
                                    key={item.id}
                                    role="button"
                                    tabIndex={activePanel === "models" ? 0 : -1}
                                    className={`${styles.modelListItem} ${item.is_default ? styles.modelListItemActive : ""}`}
                                    onClick={() => handleSelectModel(item)}
                                    onDoubleClick={(event) => {
                                        event.stopPropagation();
                                        handleEditModel(item);
                                    }}
                                    onKeyDown={(event) => {
                                        if (event.key === "Enter" || event.key === " ") {
                                            event.preventDefault();
                                            handleSelectModel(item);
                                        }
                                    }}
                                >
                                    <div className={styles.modelInfo}>
                                        <div className={styles.modelName}>
                                            {item.name || item.chat_model}
                                            {item.is_default && <Tag color="blue">使用中</Tag>}
                                        </div>
                                        <div className={styles.modelMeta}>
                                            {item.chat_model} · {item.api_key_masked}
                                        </div>
                                        {item.image_model && (
                                            <div className={styles.modelMeta}>生图：{item.image_model}</div>
                                        )}
                                    </div>
                                    <Button
                                        size="small"
                                        danger
                                        disabled={configs.length <= 1}
                                        onClick={(event) => {
                                            event.stopPropagation();
                                            handleDelete(item.id);
                                        }}
                                    >
                                        删除
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </section>
                </div>
            </div>
        </Modal>
    );
}

export default ModelConfigModal;
