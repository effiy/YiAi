/**
 * API 客户端
 */
class APIClient {
    normalizeUrl(baseUrl, path) {
        const normalizedBase = baseUrl.replace(/\/+$/, '');
        const normalizedPath = path.startsWith('/') ? path : '/' + path;
        return `${normalizedBase}${normalizedPath}`;
    }

    async streamRequest(url, payload, callbacks = {}) {
        const baseUrl = document.getElementById('baseUrl').value.trim();
        if (!baseUrl) {
            throw new Error('API服务器地址不能为空');
        }

        const fullUrl = this.normalizeUrl(baseUrl, url);
        let response;

        try {
            response = await fetch(fullUrl, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(payload),
                mode: 'cors',
                credentials: 'omit'
            });

            if (!response.ok) {
                let errorText = '';
                try {
                    errorText = await response.text();
                } catch (e) {
                    errorText = `HTTP ${response.status} ${response.statusText}`;
                }
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
        } catch (error) {
            if (error instanceof TypeError) {
                if (error.message.includes('fetch') || 
                    error.message.includes('Failed to fetch') || 
                    error.message.includes('NetworkError')) {
                    throw new Error(
                        `网络连接失败: 无法连接到服务器 ${fullUrl}。可能的原因：\n1. 服务器地址不正确\n2. 服务器未运行\n3. 网络连接问题\n4. CORS 跨域限制（请检查服务器 CORS 配置）`);
                }
                throw new Error(`请求失败: ${error.message}`);
            }
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(`未知错误: ${String(error)}`);
        }

        if (callbacks.onStart) callbacks.onStart();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const messages = buffer.split('\n\n');
                buffer = messages.pop() || '';

                for (const message of messages) {
                    if (message.startsWith('data: ')) {
                        try {
                            const chunk = JSON.parse(message.substring(6));
                            if (chunk.message?.content && callbacks.onChunk) {
                                callbacks.onChunk(chunk);
                            }
                            if (chunk.type === 'context_info' && callbacks.onChunk) {
                                callbacks.onChunk(chunk);
                            }
                            if (chunk.done === true && callbacks.onComplete) {
                                callbacks.onComplete();
                            }
                            if (chunk.type === 'error' && callbacks.onError) {
                                callbacks.onError(chunk.data);
                            }
                        } catch (e) {
                            console.warn('解析消息失败:', message, e);
                        }
                    }
                }
            }

            if (buffer.trim() && buffer.trim().startsWith('data: ')) {
                try {
                    const chunk = JSON.parse(buffer.trim().substring(6));
                    if (chunk.done === true && callbacks.onComplete) {
                        callbacks.onComplete();
                    }
                } catch (e) {
                    console.warn('解析最后消息失败:', e);
                }
            }
        } catch (error) {
            if (callbacks.onError) {
                callbacks.onError(error.message);
            }
            throw error;
        }
    }

    async request(method, url, payload = null) {
        try {
            const options = {
                method,
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                mode: 'cors',
                credentials: 'omit'
            };

            if (payload && (method === 'POST' || method === 'PUT')) {
                options.body = JSON.stringify(payload);
            }

            const response = await fetch(url, options);

            if (!response.ok) {
                let errorText = '';
                try {
                    errorText = await response.text();
                } catch (e) {
                    errorText = `HTTP ${response.status} ${response.statusText}`;
                }
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            return await response.json();
        } catch (error) {
            if (error instanceof TypeError) {
                if (error.message.includes('fetch') || 
                    error.message.includes('Failed to fetch') || 
                    error.message.includes('NetworkError')) {
                    throw new Error(
                        `网络连接失败: 无法连接到服务器 ${url}。可能的原因：\n1. 服务器地址不正确\n2. 服务器未运行\n3. 网络连接问题\n4. CORS 跨域限制（请检查服务器 CORS 配置）`);
                }
                throw new Error(`请求失败: ${error.message}`);
            }
            if (error instanceof Error) {
                throw error;
            }
            throw new Error(`未知错误: ${String(error)}`);
        }
    }

    async post(url, payload) {
        return this.request('POST', url, payload);
    }

    async get(url) {
        return this.request('GET', url);
    }

    async delete(url) {
        return this.request('DELETE', url);
    }
}

