import request from "./request";


export function uploadAttachment(file: File) {
    const formData = new FormData();
    formData.append("file", file);

    return request.post("/attachment/upload", formData, {
        headers: {
            "Content-Type": "multipart/form-data"
        }
    });
}
