import { useEffect, useState } from "react";
import { Button, Drawer, Spin, message } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import type { MessageSource } from "../../types/message";
import { getKnowledgeFileBlob } from "../../api/file";
import styles from "../../assets/SourcePreviewDrawer.module.css";


interface SourcePreviewDrawerProps {
    source: MessageSource | null;
    open: boolean;
    onClose: () => void;
}


function SourcePreviewDrawer({ source, open, onClose }: SourcePreviewDrawerProps) {
    const [objectUrl, setObjectUrl] = useState("");
    const [loading, setLoading] = useState(false);

    const isPdf = source?.file_type === "pdf" || source?.filename.toLowerCase().endsWith(".pdf");
    const previewUrl = isPdf && objectUrl
        ? `${objectUrl}#page=${source?.page || 1}`
        : objectUrl;

    useEffect(() => {
        if (!open || !source) {
            return;
        }

        let nextObjectUrl = "";

        const loadFile = async () => {
            setLoading(true);

            try {
                const blob = await getKnowledgeFileBlob(source.file_id);
                nextObjectUrl = URL.createObjectURL(blob);
                setObjectUrl(nextObjectUrl);
            } catch (error) {
                message.error("打开引用文件失败");
            } finally {
                setLoading(false);
            }
        };

        loadFile();

        return () => {
            if (nextObjectUrl) {
                URL.revokeObjectURL(nextObjectUrl);
            }
            setObjectUrl("");
        };
    }, [open, source]);

    const handleDownload = () => {
        if (!objectUrl || !source) {
            return;
        }

        const link = document.createElement("a");
        link.href = objectUrl;
        link.download = source.filename;
        link.click();
    };

    return (
        <Drawer
            className={styles.drawer}
            placement="right"
            size="large"
            open={open}
            onClose={onClose}
            title={source && (
                <div className={styles.title}>
                    <span className={styles.fileName}>{source.filename}</span>
                    <span className={styles.meta}>
                        {source.page ? `第 ${source.page} 页` : "未提供页码"}
                    </span>
                </div>
            )}
            styles={{
                body: {
                    background: "#18181b",
                    padding: 20
                }
            }}
        >
            <div className={styles.body}>
                {loading && <Spin />}

                {!loading && isPdf && previewUrl && (
                    <iframe
                        className={styles.frame}
                        title={source?.filename}
                        src={previewUrl}
                    />
                )}

                {!loading && !isPdf && (
                    <div className={styles.unsupported}>
                        <div>当前浏览器不能直接预览 Word 文档。</div>
                        <Button icon={<DownloadOutlined />} onClick={handleDownload}>
                            下载文件
                        </Button>
                    </div>
                )}
            </div>
        </Drawer>
    );
}

export default SourcePreviewDrawer;
