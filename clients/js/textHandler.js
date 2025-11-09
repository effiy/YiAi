/**
 * 文本处理器 - 处理文本输入和验证
 */
class TextHandler {
    constructor() {
        this.textFields = {
            fromSystem: 'fromSystem',
            fromUser: 'fromUser',
            model: 'model',
            userId: 'userId',
            conversationId: 'conversationId',
            baseUrl: 'baseUrl'
        };
    }

    /**
     * 获取输入值
     * @param {string} id - 输入元素 ID
     * @returns {string} 输入值
     */
    getInputValue(id) {
        const element = document.getElementById(id);
        return element ? element.value.trim() : '';
    }

    /**
     * 获取所有文本配置
     * @returns {Object} 配置对象
     */
    getTextConfig() {
        return {
            baseUrl: this.getInputValue(this.textFields.baseUrl),
            model: this.getInputValue(this.textFields.model),
            fromSystem: this.getInputValue(this.textFields.fromSystem),
            fromUser: this.getInputValue(this.textFields.fromUser),
            userId: this.getInputValue(this.textFields.userId),
            conversationId: this.getInputValue(this.textFields.conversationId)
        };
    }

    /**
     * 验证文本配置
     * @param {Object} config - 配置对象
     * @returns {boolean} 是否有效
     */
    validateTextConfig(config) {
        if (!config.fromSystem || !config.fromUser) {
            return { valid: false, message: '系统提示词和用户提示词不能为空！' };
        }

        if (!config.baseUrl) {
            return { valid: false, message: 'API 服务器地址不能为空！' };
        }

        return { valid: true };
    }

    /**
     * 清空文本输入
     */
    clearTextInputs() {
        document.getElementById(this.textFields.fromSystem).value = '';
        document.getElementById(this.textFields.fromUser).value = '';
        document.getElementById(this.textFields.conversationId).value = '';
    }

    /**
     * 设置文本输入值
     * @param {string} field - 字段名
     * @param {string} value - 值
     */
    setInputValue(field, value) {
        const element = document.getElementById(this.textFields[field]);
        if (element) {
            element.value = value;
        }
    }
}

