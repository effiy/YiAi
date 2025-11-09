/**
 * 图片管理器 - 支持 Qwen3-VL 格式
 * Qwen3-VL 支持的图片格式：
 * - HTTP/HTTPS URL: "https://example.com/image.jpg"
 * - Base64 Data URL: "data:image/jpeg;base64,..."
 * - 本地文件路径（服务器端）
 */
class ImageManager {
    constructor() {
        this.images = []; // 存储图片 URL（支持 base64 data URL 或 HTTP URL）
    }

    selectImages() {
        document.getElementById('imageUpload').click();
    }

    handleFileSelect(event) {
        const files = event.target.files;
        if (!files) return;

        Array.from(files).forEach(file => {
            if (!file.type.startsWith('image/')) {
                alert('请选择图片文件！');
                return;
            }

            // 将图片转换为 base64 data URL（Qwen3-VL 支持的格式）
            const reader = new FileReader();
            reader.onload = (e) => {
                // e.target.result 是 base64 data URL，格式如：data:image/jpeg;base64,/9j/4AAQ...
                // 这个格式可以直接用于 Qwen3-VL
                this.images.push(e.target.result);
                this.updatePreview();
            };
            reader.readAsDataURL(file);
        });
    }

    /**
     * 添加图片 URL（支持直接输入 HTTP URL）
     * @param {string} url - 图片 URL（HTTP URL 或 base64 data URL）
     */
    addImageUrl(url) {
        if (url && (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:'))) {
            this.images.push(url);
            this.updatePreview();
        } else {
            alert('请输入有效的图片 URL（HTTP/HTTPS 或 base64 data URL）');
        }
    }

    /**
     * 通过弹窗输入图片 URL
     */
    addImageFromUrl() {
        const url = prompt('请输入图片 URL（支持 HTTP/HTTPS URL 或 Base64 Data URL）：');
        if (url && url.trim()) {
            this.addImageUrl(url.trim());
        }
    }

    removeImage(index) {
        this.images.splice(index, 1);
        this.updatePreview();
    }

    clearImages() {
        this.images = [];
        this.updatePreview();
        document.getElementById('imageUpload').value = '';
    }

    updatePreview() {
        const preview = document.getElementById('imagePreview');
        preview.innerHTML = '';

        this.images.forEach((img, index) => {
            const div = document.createElement('div');
            div.className = 'image-preview-item';
            div.innerHTML = `
                <img src="${img}" alt="预览 ${index + 1}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'150\' height=\'150\'%3E%3Ctext x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dy=\'.3em\'%3E图片加载失败%3C/text%3E%3C/svg%3E'">
                <button class="image-remove-btn" onclick="app.imageManager.removeImage(${index})" title="删除">×</button>
            `;
            preview.appendChild(div);
        });
    }

    /**
     * 获取图片列表（Qwen3-VL 格式）
     * @returns {string[]} 图片 URL 数组
     */
    getImages() {
        return this.images;
    }
}

