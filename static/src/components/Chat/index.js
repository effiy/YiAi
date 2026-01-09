import { escapeHtml } from "../../utils/index.js";
import { normalizeRole, normalizeText } from "../../utils/msg.js";
import { renderMarkdown, renderMermaidIn } from "../../utils/markdown.js";

/**
 * 聊天组件：负责消息渲染与消息内操作的事件委托
 */
export class Chat {
  /**
   * @param {HTMLElement} container - 聊天内容容器
   * @param {Object} [callbacks] - 回调函数
   * @param {Function} [callbacks.onMoveUp]
   * @param {Function} [callbacks.onMoveDown]
   * @param {Function} [callbacks.onDelete]
   * @param {Function} [callbacks.onSendPrompt]
   * @param {Function} [callbacks.onCopy]
   */
  constructor(container, callbacks = {}) {
    this.container = container;
    this.callbacks = {
      onMoveUp: null,
      onMoveDown: null,
      onDelete: null,
      onSendPrompt: null,
      onCopy: null,
      ...callbacks,
    };
    
    this._scrollTimeout = null;
    this._scrollRAF = null;
    this._lastScrollHeight = 0;

    // 绑定事件处理器
    this._handleClick = this._handleClick.bind(this);
    this._bindEvents();
  }

  /**
   * 渲染会话
   * @param {Object} session - 会话对象 { messages: [] ... }
   * @param {boolean} [isNews=false] - 是否新闻聊天（不显示欢迎信息）
   */
  render(session, isNews = false) {
    if (!session) {
      this._renderEmpty(isNews);
      return;
    }
    
    const msgs = this._getMessages(session, isNews);
    
    if (msgs.length === 0) {
      if (isNews) {
        this._renderEmptyNews();
      } else {
        const welcomeHtml = this._createWelcomeMessageHtml(session);
        this.container.innerHTML = this._createBotMessageHtml(welcomeHtml, true);
      }
    } else {
      let html = '';
      
      // 对于普通会话，在顶部添加欢迎信息
      if (!isNews) {
        const welcomeHtml = this._createWelcomeMessageHtml(session);
        html += this._createBotMessageHtml(welcomeHtml, true);
      }
      
      html += msgs.map((m, idx) => this._renderMessage(m, idx, msgs.length)).join("");
      this.container.innerHTML = html;
    }
    
    // 滚动到底并延迟渲染 Mermaid
    this.scrollToBottom();
    setTimeout(() => {
      renderMermaidIn(this.container);
      this.scrollToBottom();
    }, 0);
  }

  /**
   * 向列表追加一条消息
   * @param {Object} message - 消息对象
   * @param {number} idx - 消息索引
   * @param {number} totalCount - 总消息数
   */
  append(message, idx, totalCount) {
    // 1. 移除空状态
    const emptyState = this.container.querySelector('.empty');
    if (emptyState) {
      emptyState.remove();
    }

    // 2. 更新上一条消息的"下移"按钮状态
    if (idx > 0) {
      const prevMsg = this.container.querySelector(`.chatMsg[data-message-index="${idx - 1}"]`);
      if (prevMsg) {
         const moveDownBtn = prevMsg.querySelector('[data-action="move-down"]');
         if (moveDownBtn) moveDownBtn.disabled = false;
      }
    }

    // 3. 渲染并追加新消息
    const html = this._renderMessage(message, idx, totalCount);
    this.container.insertAdjacentHTML('beforeend', html);

    // 4. 滚动到底部
    this.scrollToBottom(true);
    
    // 5. 渲染 Mermaid
    setTimeout(() => {
      renderMermaidIn(this.container);
      this.scrollToBottom();
    }, 0);
  }

  /**
   * 滚动到底部（含性能优化）
   * @param {boolean} [smooth=false] - 是否平滑滚动
   * @param {boolean} [force=false] - 是否强制滚动
   */
  scrollToBottom(smooth = false, force = false) {
    if (!this.container) return;
    
    if (!force && !this._isNearBottom(100)) {
      return;
    }
    
    if (this._scrollTimeout) {
      clearTimeout(this._scrollTimeout);
      this._scrollTimeout = null;
    }
    if (this._scrollRAF) {
      cancelAnimationFrame(this._scrollRAF);
      this._scrollRAF = null;
    }
    
    const doScroll = () => {
      if (!this.container) return;
      const targetScrollTop = this.container.scrollHeight;
      if (targetScrollTop === this._lastScrollHeight && this.container.scrollTop === this._lastScrollHeight) {
        return;
      }
      this._lastScrollHeight = targetScrollTop;
      this.container.scrollTop = targetScrollTop;
    };

    if (smooth) {
      const currentScrollTop = this.container.scrollTop;
      const targetScrollTop = this.container.scrollHeight;
      if (Math.abs(currentScrollTop - targetScrollTop) < 10) {
        return;
      }
      const originalBehavior = this.container.style.scrollBehavior;
      this.container.style.scrollBehavior = 'smooth';
      this.container.scrollTop = targetScrollTop;
      setTimeout(() => {
        if (this.container) {
          this.container.style.scrollBehavior = originalBehavior || '';
        }
      }, 500);
    } else {
      this._scrollRAF = requestAnimationFrame(() => {
        doScroll();
        this._scrollRAF = requestAnimationFrame(() => {
          doScroll();
          this._scrollRAF = null;
        });
      });
    }
  }

  _bindEvents() {
    this.container.addEventListener('click', this._handleClick);
  }

  async _handleClick(e) {
    const target = e.target;
    
    // 复制
    const copyBtn = target.closest('[data-action="copy"]');
    if (copyBtn) {
      e.stopPropagation();
      await this._handleCopy(copyBtn);
      return;
    }
    
    // 上移
    const moveUpBtn = target.closest('[data-action="move-up"]');
    if (moveUpBtn && !moveUpBtn.disabled) {
      e.stopPropagation();
      const idx = this._getMessageIndex(moveUpBtn);
      if (idx !== -1 && this.callbacks.onMoveUp) {
        this.callbacks.onMoveUp(idx);
      }
      return;
    }
    
    // 下移
    const moveDownBtn = target.closest('[data-action="move-down"]');
    if (moveDownBtn && !moveDownBtn.disabled) {
      e.stopPropagation();
      const idx = this._getMessageIndex(moveDownBtn);
      if (idx !== -1 && this.callbacks.onMoveDown) {
        this.callbacks.onMoveDown(idx);
      }
      return;
    }
    
    // 发送到 AI
    const sendPromptBtn = target.closest('[data-action="send-prompt"]');
    if (sendPromptBtn) {
      e.stopPropagation();
      const idx = this._getMessageIndex(sendPromptBtn);
      if (idx !== -1 && this.callbacks.onSendPrompt) {
        this.callbacks.onSendPrompt(idx, sendPromptBtn);
      }
      return;
    }
    
    // 删除
    const deleteBtn = target.closest('[data-action="delete"]');
    if (deleteBtn) {
      e.stopPropagation();
      e.preventDefault();
      if (deleteBtn.disabled || deleteBtn.dataset.deleting === 'true') {
        return;
      }
      const idx = this._getMessageIndex(deleteBtn);
      if (idx !== -1 && this.callbacks.onDelete) {
        this.callbacks.onDelete(idx, deleteBtn);
      }
      return;
    }
  }

  _getMessageIndex(el) {
    const msgDiv = el.closest('.chatMsg');
    if (!msgDiv) return -1;
    return parseInt(msgDiv.getAttribute('data-message-index') || '-1');
  }

  async _handleCopy(btn) {
    const msgDiv = btn.closest('.chatMsg');
    if (!msgDiv) return;
    const bubble = msgDiv.querySelector('.chatBubble--md') || msgDiv.querySelector('.chatBubble');
    if (!bubble) return;
    
    let messageContent = bubble.textContent || bubble.innerText || '';
    
    // 优先取 DOM 文本，若为空且提供 onCopy 回调则委托处理
    if (!messageContent.trim()) {
      if (this.callbacks.onCopy) {
        this.callbacks.onCopy(this._getMessageIndex(btn), btn);
        return;
      }
    }
    
    if (!messageContent.trim()) {
      console.warn('Empty message content');
      return;
    }
    
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(messageContent.trim());
        this._showCopySuccess(btn);
      } else {
        // Fallback
        const textArea = document.createElement('textarea');
        textArea.value = messageContent.trim();
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        this._showCopySuccess(btn);
      }
    } catch (error) {
      console.error('Copy failed:', error);
    }
  }

  _showCopySuccess(btn) {
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '✓';
    btn.classList.add('is-copied');
    setTimeout(() => {
      btn.innerHTML = originalHTML;
      btn.classList.remove('is-copied');
    }, 1000);
  }

  _isNearBottom(threshold = 50) {
    if (!this.container) return true;
    const { scrollTop, scrollHeight, clientHeight } = this.container;
    return scrollHeight - scrollTop - clientHeight <= threshold;
  }

  _getMessages(session, isNews) {
    return Array.isArray(session.messages) ? session.messages.filter(m => m != null) : [];
  }

  _createBotMessageHtml(content, isWelcome = false) {
    const attrs = isWelcome ? 'data-welcome-message="true"' : '';
    return `
      <div class="chatMsg chatMsg--bot" ${attrs}>
        <div class="chatMsgContentRow">
          <div class="chatAvatar" aria-hidden="true">AI</div>
          <div class="chatBubbleWrap">
            <div class="chatBubble chatBubble--md">${content}</div>
          </div>
        </div>
      </div>
    `;
  }

  _renderMessage(m, idx, totalCount) {
    if (!m || typeof m !== 'object') return '';
    
    const role = normalizeRole(m);
    const text = normalizeText(m);
    const isMe = role === "user";
    const cls = isMe ? "chatMsg chatMsg--me" : "chatMsg chatMsg--bot";
    const avatar = isMe ? "我" : "AI";
    const imageDataUrl = m.imageDataUrl || m.image || "";

    let contentHtml = "";
    if (imageDataUrl) {
      contentHtml += `<div class="chatImage">
        <img class="chatImage__img" src="${escapeHtml(imageDataUrl)}" alt="图片" />
      </div>`;
    }
    if (text) {
      contentHtml += `
        <div class="chatBubbleWrap">
          <div class="chatBubble chatBubble--md">${renderMarkdown(text)}</div>
        </div>
      `;
    }
    if (!imageDataUrl && !text) {
      contentHtml = `<div class="chatBubble">…</div>`;
    }

    const timeStr = this._formatTime(m.ts || m.timestamp || Date.now());

    const actionsHtml = `
      <div class="chatMsgTimeActions" data-message-index="${idx}">
        <div class="chatMsgTime">${timeStr}</div>
        <div class="chatMsgActions">
          <button class="chatMsgActionBtn chatMsgActionBtn--sort" data-action="move-up" title="上移" ${idx === 0 ? 'disabled' : ''}>⬆️</button>
          <button class="chatMsgActionBtn chatMsgActionBtn--sort" data-action="move-down" title="下移" ${idx === totalCount - 1 ? 'disabled' : ''}>⬇️</button>
          <button class="chatMsgActionBtn" data-action="copy" title="复制">📋</button>
          ${isMe ? `<button class="chatMsgActionBtn chatMsgActionBtn--prompt" data-action="send-prompt" title="发送到 AI" data-message-index="${idx}">
            <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-send"/></svg>
          </button>` : ''}
          <button class="chatMsgActionBtn chatMsgActionBtn--delete" data-action="delete" title="删除" data-message-index="${idx}">
            <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-trash"/></svg>
          </button>
        </div>
      </div>
    `;

    return `
      <div class="${cls}" data-message-index="${idx}">
        <div class="chatMsgContentRow">
          ${isMe ? "" : `<div class="chatAvatar" aria-hidden="true">${avatar}</div>`}
          ${contentHtml}
          ${isMe ? `<div class="chatAvatar" aria-hidden="true">${avatar}</div>` : ""}
        </div>
        ${actionsHtml}
      </div>
    `;
  }

  _renderEmpty(isNews) {
    if (isNews) {
      this.container.innerHTML = `<div class="empty" style="background:transparent;box-shadow:none">
        <div class="empty__icon">📰</div>
        <div class="empty__title">找不到该新闻</div>
        <div class="empty__desc">请返回新闻列表重试</div>
      </div>`;
    } else {
      this.container.innerHTML = `<div class="empty" style="background:transparent;box-shadow:none">
        <div class="empty__icon">💬</div>
        <div class="empty__title">找不到该会话</div>
        <div class="empty__desc">请返回会话列表重试</div>
      </div>`;
    }
  }

  _renderEmptyNews() {
    this.container.innerHTML = `<div class="empty" style="background:transparent;box-shadow:none">
      <div class="empty__icon">🗨️</div>
      <div class="empty__title">暂无消息</div>
      <div class="empty__desc">发送一条消息开始聊天</div>
    </div>`;
  }

  _formatTime(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const msgDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (msgDate.getTime() === today.getTime()) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (msgDate.getTime() === yesterday.getTime()) {
      return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else {
      const month = date.getMonth() + 1;
      const day = date.getDate();
      const time = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
      return `${month}月${day}日 ${time}`;
    }
  }

  _createWelcomeMessageHtml(session) {
    const pageUrl = session.url || "";
    const pageDescription = (session.pageDescription && session.pageDescription.trim()) || '';

    let welcomeHtml = `
      <div class="welcomeMessage">
        <div class="welcomeSection">
          <div class="welcomeLabel">🔗 网址</div>
          <a class="welcomeLink" href="${escapeHtml(pageUrl)}" target="_blank" title="${escapeHtml(pageUrl)}">
            ${escapeHtml(pageUrl)}
          </a>
        </div>
    `;

    if (pageDescription && pageDescription.trim().length > 0) {
      welcomeHtml += `
        <div class="welcomeSection">
          <div class="welcomeLabel">📝 页面描述</div>
          <div class="welcomeDesc">
            ${renderMarkdown(pageDescription)}
          </div>
        </div>
      `;
    }

    welcomeHtml += `</div>`;
    return welcomeHtml;
  }
}
