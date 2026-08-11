import { useEffect, useState } from "react";
import { Button, Drawer, Empty, Popconfirm, Space, Table, Tag, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { DeleteOutlined, ReloadOutlined } from "@ant-design/icons";
import { deleteKnowledgeFile, getKnowledgeFiles, reindexKnowledgeFile } from "../../api/file";
import type { KnowledgeFile } from "../../types/knowledgeFile";
import styles from "../../assets/KnowledgeBaseDrawer.module.css";


interface KnowledgeBaseDrawerProps {
    open: boolean;
    onClose: () => void;
}


function formatSize(size: number) {
    if (size < 1024) {
        return `${size} B`;
    }

    if (size < 1024 * 1024) {
        return `${(size / 1024).toFixed(1)} KB`;
    }

    return `${(size / 1024 / 1024).toFixed(1)} MB`;
}


function KnowledgeBaseDrawer({ open, onClose }: KnowledgeBaseDrawerProps) {
    const [files, setFiles] = useState<KnowledgeFile[]>([]);
    const [loading, setLoading] = useState(false);
    const [reindexingId, setReindexingId] = useState<number | null>(null);

    const fetchFiles = async () => {
        setLoading(true);

        try {
            const res = await getKnowledgeFiles() as any;
            setFiles(res?.data?.files || res?.files || []);
        } catch (error) {
            message.error("获取知识库文件失败");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (open) {
            fetchFiles();
        }
    }, [open]);

    const handleDelete = async (fileId: number) => {
        try {
            await deleteKnowledgeFile(fileId);
            message.success("文件已删除");
            await fetchFiles();
        } catch (error) {
            message.error("删除失败");
        }
    };

    const handleReindex = async (fileId: number) => {
        setReindexingId(fileId);

        try {
            await reindexKnowledgeFile(fileId);
            message.success("重新索引完成");
            await fetchFiles();
        } catch (error) {
            message.error("重新索引失败");
        } finally {
            setReindexingId(null);
        }
    };

    const columns: ColumnsType<KnowledgeFile> = [
        {
            title: "文件",
            dataIndex: "original_filename",
            key: "original_filename",
            render: (_, record) => (
                <div>
                    <div className={styles.fileName}>{record.original_filename}</div>
                    <div className={styles.meta}>
                        {record.file_type.toUpperCase()} · {formatSize(record.size)}
                    </div>
                </div>
            )
        },
        {
            title: "索引状态",
            dataIndex: "status",
            key: "status",
            width: 110,
            render: (status: string) => (
                <Tag color={status === "indexed" ? "green" : "red"}>
                    {status === "indexed" ? "已索引" : "文件缺失"}
                </Tag>
            )
        },
        {
            title: "操作",
            key: "action",
            width: 150,
            render: (_, record) => (
                <Space size={6}>
                    <Button
                        size="small"
                        icon={<ReloadOutlined />}
                        loading={reindexingId === record.id}
                        onClick={() => handleReindex(record.id)}
                    />
                    <Popconfirm
                        title="删除文件"
                        description="会同时删除对应向量索引。"
                        okText="删除"
                        cancelText="取消"
                        onConfirm={() => handleDelete(record.id)}
                    >
                        <Button size="small" danger icon={<DeleteOutlined />} />
                    </Popconfirm>
                </Space>
            )
        }
    ];

    return (
        <Drawer
            title={null}
            placement="right"
            size="large"
            open={open}
            onClose={onClose}
            className={styles.drawer}
            styles={{
                body: {
                    background: "#18181b",
                    padding: 24
                },
                header: {
                    background: "#18181b",
                    borderBottom: "1px solid rgba(255,255,255,0.06)"
                }
            }}
        >
            <div className={styles.header}>
                <h2 className={styles.title}>知识库文件</h2>
                <p className={styles.subtitle}>
                    管理已上传文档，查看索引状态，必要时重新构建向量索引。
                </p>
            </div>

            <Table
                className={styles.table}
                rowKey="id"
                loading={loading}
                columns={columns}
                dataSource={files}
                pagination={false}
                locale={{
                    emptyText: <Empty description={<span className={styles.emptyHint}>还没有上传文件</span>} />
                }}
            />
        </Drawer>
    );
}

export default KnowledgeBaseDrawer;
