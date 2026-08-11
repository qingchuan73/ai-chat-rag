import { CloseOutlined, FileTextOutlined } from "@ant-design/icons";
import styles from "../../assets/ChatInput.module.css";


interface AttachmentChipProps {
    name: string;
    onRemove: () => void;
}


function AttachmentChip({ name, onRemove }: AttachmentChipProps) {
    return (
        <div className={styles.attachmentChip}>
            <FileTextOutlined className={styles.attachmentIcon} />
            <span className={styles.attachmentName} title={name}>
                {name}
            </span>
            <button type="button" className={styles.attachmentRemove} onClick={onRemove} title="移除附件">
                <CloseOutlined />
            </button>
        </div>
    );
}

export default AttachmentChip;
