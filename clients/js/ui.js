/**
 * UI 管理器
 */
class UI {
    showStatus(type, message) {
        const status = document.getElementById('status');
        status.className = `status ${type} show`;
        status.textContent = message;

        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                if (status.textContent === message) {
                    this.hideStatus();
                }
            }, 5000);
        }
    }

    hideStatus() {
        const status = document.getElementById('status');
        status.classList.remove('show');
    }

    showContextInfo(contextInfo) {
        // 上下文信息功能已移除
        const contextDiv = document.getElementById('contextInfo');
        contextDiv.classList.remove('show');
    }

    toggleContextDetails() {
        const detailsDiv = document.getElementById('contextDetails');
        const toggle = document.getElementById('contextToggle');
        detailsDiv.classList.toggle('show');
        toggle.textContent = detailsDiv.classList.contains('show') ? 
            '▲ 收起详情' : '▼ 展开详情';
    }

    hideContextInfo() {
        const contextDiv = document.getElementById('contextInfo');
        const detailsDiv = document.getElementById('contextDetails');
        const summaryDiv = document.getElementById('contextSummary');
        contextDiv.classList.remove('show');
        detailsDiv.innerHTML = '';
        summaryDiv.innerHTML = '';
        detailsDiv.classList.remove('show');
        document.getElementById('contextToggle').textContent = '▼ 展开详情';
    }

    setStreamButtonState(isLoading) {
        const btn = document.getElementById('btnStream');
        btn.disabled = isLoading;
        btn.innerHTML = isLoading 
            ? '<span class="spinner"></span> 正在处理...'
            : '🚀 流式调用 <span style="font-size: 12px; opacity: 0.8; margin-left: 8px;">(Ctrl+Enter)</span>';
    }

    clearOutput() {
        document.getElementById('output').textContent = '等待调用...';
        this.hideStatus();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

