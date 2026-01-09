/**
 * 新闻列表组件
 * 负责渲染新闻与来源于新闻的会话项
 */

import { escapeHtml, dateUtil } from "../../utils/index.js";
import { config } from "../../config.js?v=2";
import { BaseList } from "../BaseList/index.js";

export class NewsList extends BaseList {
  /**
   * @param {Object} options
   * @param {HTMLElement} options.container
   * @param {HTMLElement} options.emptyState
   */
  constructor({ container, emptyState }) {
    super({
      container,
      emptyState,
      itemHeight: 92, // Approximation from CSS contain-intrinsic-size
      minItemsForVirtual: Number(config.ui.newsVlistMinItems) || 60,
    });
  }

  /**
   * @override
   * @protected
   */
  _updateEmptyState(isEmpty, error) {
    if (!this.emptyState) return;

    this.emptyState.hidden = !isEmpty;
    if (isEmpty) {
      const title = this.emptyState.querySelector(".empty__title");
      const desc = this.emptyState.querySelector(".empty__desc");
      if (title) title.textContent = error ? "加载失败" : "暂无匹配新闻";
      if (desc) desc.textContent = error ? error : "试试清空搜索或调整筛选条件";
    }
  }

  /**
   * @override
   * @protected
   */
  _renderItem(item) {
    // Session item (converted from news)
    if (item.fromNews) {
      return this._renderSessionItem(item);
    }
    // Regular news item
    return this._renderNewsItem(item);
  }

  _renderSessionItem(item) {
    const mutedCls = item.muted ? " is-muted" : "";
    const displayTitle = (item.pageTitle && item.pageTitle.trim()) || item.title || "未命名会话";
    const displayDesc = (item.pageDescription && item.pageDescription.trim()) || item.preview || "—";
    
    const rawTags = Array.isArray(item.tags) ? item.tags : (item.tags ? [item.tags] : []);
    const normTags = rawTags.map((t) => String(t || "").trim()).filter(Boolean);
    const displayTags = normTags.length ? normTags : ["无标签"];
    
    const tagBadges = displayTags
      .slice(0, 4)
      .map((t, idx) => {
        const colorCls = `is-sessionTag-${idx % 4}`;
        return `<span class="badge ${colorCls}">${escapeHtml(t)}</span>`;
      })
      .join("");

    // Message count badge
    const messageBadge = item.messageCount > 0
      ? `<span class="badge">消息 ${escapeHtml(String(item.messageCount))}</span>`
      : `<span class="badge">暂无消息</span>`;

    // Date formatting
    const ts = item.lastAccessTime || item.lastActiveAt || item.updatedAt;
    let displayDate = "—";
    if (ts) {
      const d = new Date(ts);
      if (!isNaN(d.getTime())) {
        displayDate = dateUtil.formatYMD(d);
      }
    }

    // Session icon
    const sessionIcon = '<span style="color: #666; margin-right: 4px;" title="来自新闻">📰</span>';
    const displayTitleWithIcon = sessionIcon + escapeHtml(displayTitle);

    return `
      <article class="newsItem newsItem--session${mutedCls}" data-key="${escapeHtml(item.key || item.id || "")}" data-news-key="${escapeHtml(item.newsKey || "")}">
        <div class="item__mid">
          <div class="item__row1">
            <div class="item__title"><span>${displayTitleWithIcon}</span></div>
            <div class="item__meta">
              ${messageBadge}
            </div>
          </div>
          <div class="item__row2">
            <div class="item__preview">${escapeHtml(displayDesc)}</div>
          </div>
          <div class="item__row2" style="margin-top:6px">
            <div class="item__tags">${tagBadges}</div>
            <div class="item__meta">
              <span class="time">${escapeHtml(displayDate)}</span>
            </div>
          </div>
        </div>
      </article>
    `;
  }

  _renderNewsItem(item) {
    const filteredTags = (item.tags || []).filter((t) => t !== "网文");
    const tagBadges = filteredTags
      .slice(0, 4)
      .map((t) => `<span class="badge is-green">${escapeHtml(t)}</span>`)
      .join("");

    // Date formatting
    let displayDate = "—";
    if (item.createdTime || item.published) {
      const ts = item.createdTime || item.published;
      const d = new Date(ts);
      if (!isNaN(d.getTime())) {
        displayDate = dateUtil.formatYMD(d);
      }
    }

    const linkPart = item.link
      ? `<a class="newsTitleLink" href="${escapeHtml(item.link)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a>`
      : `<span class="newsTitleLink">${escapeHtml(item.title)}</span>`;

    return `
      <article class="newsItem" data-key="${escapeHtml(item.key || "")}">
          <div class="item__mid">
            <div class="item__row1">
              <div class="item__title"><span>${linkPart}</span></div>
              <div class="item__meta">
                <span class="time">${escapeHtml(displayDate)}</span>
              </div>
            </div>
          ${item.description ? `<div class="item__row2">
            <div class="item__preview">${escapeHtml(item.description)}</div>
          </div>` : ""}
          <div class="item__row2" style="margin-top:${item.description ? '6px' : '0'}">
            <div class="item__tags">${tagBadges}</div>
            <div class="item__meta"></div>
          </div>
        </div>
      </article>
    `;
  }
}
