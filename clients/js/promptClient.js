/**
 * AI 对话客户端应用 - 增强版
 */
class PromptClient {
    constructor() {
        this.isStreaming = false;
        this.currentConversationId = null;
        this.currentContextInfo = null;
        this.imageManager = new ImageManager();
        this.textHandler = new TextHandler();
        this.apiClient = new APIClient();
        this.ui = new UI();
        this.configManager = new ConfigManager();
        this.init();
    }

    init() {
        this.bindImageUpload();
        this.configManager.loadConfig();
        this.bindKeyboardShortcuts();
        this.checkServiceStatus();
    }

    bindImageUpload() {
        const imageUpload = document.getElementById('imageUpload');
        imageUpload.addEventListener('change', (e) => {
            this.imageManager.handleFileSelect(e);
        });
    }

    bindKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                if (!this.isStreaming) {
                    this.streamPrompt();
                }
            }
        });
    }

    toggleCollapsible(panelId) {
        const panel = document.getElementById(panelId);
        panel.classList.toggle('open');
        const content = panel.querySelector('.collapsible-content');
        content.classList.toggle('show');
    }

    toggleContextDetails() {
        this.ui.toggleContextDetails();
    }

    async checkServiceStatus() {
        const baseUrl = this.textHandler.getInputValue('baseUrl');
        const statusContainer = document.getElementById('serviceStatus');

        if (!baseUrl) {
            statusContainer.innerHTML = 
                `<span class="status-badge unavailable">⚠️ 请先输入API服务器地址</span>`;
            return;
        }

        statusContainer.innerHTML = 
            '<span class="status-badge checking"><span class="spinner"></span> 检查中...</span>';

        const normalizedBaseUrl = baseUrl.replace(/\/+$/, '');
        const statusUrl = `${normalizedBaseUrl}/prompt/status`;

        try {
            console.log('正在连接服务器:', statusUrl);
            const startTime = Date.now();
            const data = await this.apiClient.get(statusUrl);
            const duration = Date.now() - startTime;

            console.log('连接成功，耗时:', duration, 'ms');
            statusContainer.innerHTML = 
                '<span class="status-badge available">✅ 服务正常</span>';
        } catch (error) {
            console.error('检查服务状态失败:', error);
            const errorMessage = this.parseErrorMessage(error);
            statusContainer.innerHTML = this.buildErrorStatusHTML(errorMessage, statusUrl);
            this.ui.showStatus('error', `❌ ${errorMessage.message}`);
        }
    }

    parseErrorMessage(error) {
        let message = '无法连接服务器';
        let details = '';

        if (error?.message) {
            const errorMsg = error.message;
            if (errorMsg.includes('网络连接失败')) {
                message = '网络连接失败';
                const reasonsMatch = errorMsg.match(/可能的原因：([\s\S]+)/);
                if (reasonsMatch) {
                    details = reasonsMatch[1].trim();
                }
            } else if (errorMsg.includes('Failed to fetch') || 
                       errorMsg.includes('NetworkError') || 
                       errorMsg.includes('fetch')) {
                message = '网络连接失败';
                details = '1. 请检查服务器地址是否正确\n2. 请确认服务器正在运行\n3. 检查网络连接\n4. 如果使用 HTTPS，请确认证书有效\n5. 检查浏览器控制台是否有 CORS 错误';
            } else if (errorMsg.includes('CORS') || errorMsg.includes('cors')) {
                message = 'CORS跨域错误';
                details = '浏览器阻止了跨域请求。请检查服务器的 CORS 配置，确保允许来自当前域的请求。';
            } else if (errorMsg.includes('HTTP')) {
                const httpMatch = errorMsg.match(/HTTP (\d+)/);
                if (httpMatch) {
                    const statusCode = httpMatch[1];
                    if (statusCode === '404') {
                        message = '接口不存在 (404)';
                        details = `服务器返回 404 错误，请检查接口路径是否正确`;
                    } else if (statusCode === '401' || statusCode === '403') {
                        message = `认证失败 (${statusCode})`;
                        details = '服务器拒绝了请求，可能需要认证信息或权限不足。';
                    } else if (statusCode >= 500) {
                        message = `服务器错误 (${statusCode})`;
                        details = '服务器内部错误，请稍后重试或联系管理员。';
                    } else {
                        message = `服务器返回错误 (${statusCode})`;
                        details = errorMsg;
                    }
                } else {
                    message = `服务器返回错误: ${errorMsg}`;
                }
            } else {
                message = `连接失败: ${errorMsg}`;
            }
        }

        return { message, details };
    }

    buildErrorStatusHTML(errorMessage, statusUrl) {
        let html = `<span class="status-badge unavailable">❌ ${errorMessage.message}</span>`;
        if (errorMessage.details) {
            html += `<div style="margin-top: 8px; padding: 8px; background: #fff3cd; border-radius: var(--radius); font-size: 12px; white-space: pre-line; max-width: 600px;">${this.ui.escapeHtml(errorMessage.details)}</div>`;
        }
        html += `<div style="margin-top: 8px; padding: 8px; background: #e3f2fd; border-radius: var(--radius); font-size: 11px; color: #1976d2;">
            💡 提示: 打开浏览器控制台 (F12) 查看详细的错误信息和网络请求
        </div>`;
        return html;
    }

    async streamPrompt() {
        if (this.isStreaming) {
            this.ui.showStatus('info', '正在处理请求中，请稍候...');
            return;
        }

        const config = this.getFormConfig();
        const validation = this.textHandler.validateTextConfig(config);
        if (!validation.valid) {
            this.ui.showStatus('error', validation.message);
            return;
        }

        this.isStreaming = true;
        this.ui.setStreamButtonState(true);
        this.ui.clearOutput();
        this.ui.hideContextInfo();
        this.ui.showStatus('info', '正在连接服务器...');

        try {
            const payload = this.buildPayload(config);
            await this.apiClient.streamRequest('/prompt', payload, {
                onChunk: (chunk) => this.handleStreamChunk(chunk),
                onComplete: () => {
                    this.ui.showStatus('success', '✅ 完成！');
                },
                onError: (error) => {
                    this.ui.showStatus('error', `❌ 错误: ${error}`);
                }
            });
        } catch (error) {
            console.error('请求失败:', error);
            this.ui.showStatus('error', `❌ 请求失败: ${error.message}`);
        } finally {
            this.isStreaming = false;
            this.ui.setStreamButtonState(false);
        }
    }

    getFormConfig() {
        const textConfig = this.textHandler.getTextConfig();
        const config = {
            ...textConfig,
            images: this.imageManager.getImages()
        };

        this.configManager.saveConfig(config);
        return config;
    }

    buildPayload(config) {
        const payload = {
            fromSystem: config.fromSystem,
            fromUser: config.fromUser
        };

        if (config.model) payload.model = config.model;
        if (config.userId) payload.user_id = config.userId;
        if (config.conversationId) payload.conversation_id = config.conversationId;
        if (config.images.length > 0) payload.images = config.images;

        return payload;
    }

    handleStreamChunk(chunk) {
        const output = document.getElementById('output');

        if (chunk.message?.content) {
            output.textContent += chunk.message.content;
            output.scrollTop = output.scrollHeight;
        }

        if (chunk.type === 'context_info') {
            this.currentContextInfo = chunk.data;
            this.ui.showContextInfo(chunk.data);
        }

        if (chunk.done === true) {
            this.ui.showStatus('success', '✅ 完成！');
        }
    }

    clearOutput() {
        this.ui.clearOutput();
        this.imageManager.clearImages();
        this.ui.hideContextInfo();
    }
}

