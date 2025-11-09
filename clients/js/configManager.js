/**
 * 配置管理器（本地存储）
 */
class ConfigManager {
    constructor() {
        this.storageKey = 'prompt_client_config';
    }

    saveConfig(config) {
        try {
            const configToSave = {
                baseUrl: config.baseUrl,
                model: config.model,
                userId: config.userId
            };
            localStorage.setItem(this.storageKey, JSON.stringify(configToSave));
        } catch (e) {
            console.warn('保存配置失败:', e);
        }
    }

    loadConfig() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            if (saved) {
                const config = JSON.parse(saved);
                if (config.baseUrl) document.getElementById('baseUrl').value = config.baseUrl;
                if (config.model) document.getElementById('model').value = config.model;
                if (config.userId) document.getElementById('userId').value = config.userId;
            }
        } catch (e) {
            console.warn('加载配置失败:', e);
        }
    }
}

