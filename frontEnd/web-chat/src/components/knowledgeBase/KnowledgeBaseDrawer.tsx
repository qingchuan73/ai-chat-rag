import { useEffect, useState } from "react";
import { Button, Drawer, Empty, Popconfirm, Space, Table, Tag, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { DeleteOutlined, ReloadOutlined } from "@ant-design/icons";
import { deleteKnowledgeFile, getKnowledgeFiles, reindexKnowledgeFile } from "../../api/file";
import { getRagTraces } from "../../api/ragTrace";
import type { KnowledgeFile } from "../../types/knowledgeFile";
import type { RagTrace } from "../../types/ragTrace";
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

function getPredictionColor(level?: string) {
    if (level === "good") {
        return "green";
    }

    if (level === "medium") {
        return "orange";
    }

    if (level === "weak") {
        return "red";
    }

    return "default";
}


function KnowledgeBaseDrawer({ open, onClose }: KnowledgeBaseDrawerProps) {
    const [files, setFiles] = useState<KnowledgeFile[]>([]);
    const [traces, setTraces] = useState<RagTrace[]>([]);
    const [loading, setLoading] = useState(false);
    const [traceLoading, setTraceLoading] = useState(false);
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

    const fetchTraces = async () => {
        setTraceLoading(true);

        try {
            const res = await getRagTraces(8) as any;
            setTraces(res?.data?.traces || res?.traces || []);
        } catch (error) {
            message.error("获取 RAG 监控失败");
        } finally {
            setTraceLoading(false);
        }
    };

    useEffect(() => {
        if (open) {
            fetchFiles();
            fetchTraces();
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

            <div className={styles.monitorHeader}>
                <div>
                    <h3 className={styles.monitorTitle}>RAG 监控</h3>
                    <p className={styles.subtitle}>查看最近几次知识库路由、查询改写和召回来源。</p>
                </div>
                <Button size="small" icon={<ReloadOutlined />} onClick={fetchTraces} />
            </div>

            <div className={styles.traceList}>
                {traceLoading && <div className={styles.traceEmpty}>加载中...</div>}
                {!traceLoading && traces.length === 0 && (
                    <div className={styles.traceEmpty}>暂无 RAG 记录</div>
                )}
                {!traceLoading && traces.map(trace => (
                    <div className={styles.traceItem} key={trace.id}>
                        <div className={styles.traceTop}>
                            <span className={styles.traceQuestion}>{trace.question}</span>
                            <Tag color={trace.used_knowledge ? "blue" : "default"}>
                                {trace.used_knowledge ? "命中知识库" : "普通对话"}
                            </Tag>
                            <Tag color={getPredictionColor(trace.prediction?.level)}>
                                {trace.prediction?.level || "normal"}
                            </Tag>
                        </div>
                        <div className={styles.traceMeta}>
                            {trace.question_type || "lookup"} · 召回 {trace.retrieved_count || 0} 条
                        </div>
                        {trace.rewritten_query && (
                            <div className={styles.traceQuery}>改写：{trace.rewritten_query}</div>
                        )}
                        {trace.selected_sources?.length > 0 && (
                            <div className={styles.traceSources}>
                                {trace.selected_sources.slice(0, 4).map((source, index) => (
                                    <span key={`${source.filename}-${source.page || source.chunk_index}-${index}`}>
                                        {source.filename}
                                        {source.page ? ` P${source.page}` : ` chunk ${source.chunk_index}`}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </Drawer>
    );
}

export default KnowledgeBaseDrawer;
