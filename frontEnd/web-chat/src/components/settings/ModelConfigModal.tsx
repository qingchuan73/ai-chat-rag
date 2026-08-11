import { useEffect, useState } from "react";
import { Button, Form, Input, Modal, Space, message } from "antd";
import { LogoutOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { deleteModelConfig, getModelConfig, saveModelConfig } from "../../api/settings";
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

    const loadConfig = async () => {
        setLoading(true);

        try {
            const result = await getModelConfig() as any;
            const nextConfig = result?.data || result;
            setConfig(nextConfig);
            form.setFieldsValue({
                base_url: nextConfig?.base_url || "",
                chat_model: nextConfig?.chat_model || "gpt-4o-mini",
                api_key: ""
            });
        } catch (error) {
            message.error("获取模型配置失败");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (open) {
            loadConfig();
        }
    }, [open]);

    const handleSave = async () => {
        const values = await form.validateFields();
        setLoading(true);

        try {
            const result = await saveModelConfig({
                api_key: values.api_key,
                base_url: values.base_url || null,
                chat_model: values.chat_model
            }) as any;
            setConfig(result?.data || result);
            form.setFieldValue("api_key", "");
            message.success("模型配置已保存");
            onClose();
        } catch (error) {
            message.error("保存模型配置失败");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        setLoading(true);

        try {
            await deleteModelConfig();
            setConfig(null);
            form.resetFields();
            form.setFieldValue("chat_model", "gpt-4o-mini");
            message.success("模型配置已删除");
        } catch (error) {
            message.error("删除模型配置失败");
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
            title="系统设置"
            open={open}
            onCancel={onClose}
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
                <Space>
                    <Button className={styles.defaultButton} onClick={onClose}>
                        取消
                    </Button>
                    <Button type="primary" onClick={handleSave} loading={loading}>
                        保存配置
                    </Button>
                </Space>
            }
        >
            <section className={styles.section}>
                <div className={styles.sectionHeader}>
                    <h3 className={styles.sectionTitle}>模型配置</h3>
                    {config?.configured && (
                        <span className={styles.status}>已配置：{config.api_key_masked}</span>
                    )}
                </div>

                <p className={styles.hint}>
                    当前仅支持 OpenAI 兼容协议。配置后，聊天、标题、摘要、查询重写和 RAG Router 都会使用你的 API Key。
                </p>

                <Form
                    form={form}
                    layout="vertical"
                    initialValues={{
                        chat_model: "gpt-4o-mini"
                    }}
                >
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
                        <Input placeholder="gpt-4o-mini" />
                    </Form.Item>
                </Form>

                {config?.configured && (
                    <Button className={styles.secondaryDanger} danger onClick={handleDelete} loading={loading}>
                        删除模型配置
                    </Button>
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
        </Modal>
    );
}

export default ModelConfigModal;
