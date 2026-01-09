/**
 * 列表组件基类
 * 封装虚拟列表初始化、空状态处理和数据更新逻辑
 */

import { VirtualList } from "../VirtualList/index.js";

export class BaseList {
  /**
   * @param {Object} options
   * @param {HTMLElement} options.container - 列表容器元素
   * @param {HTMLElement} [options.emptyState] - 空状态容器元素
   * @param {number} [options.itemHeight] - 列表项预估高度
   * @param {number} [options.minItemsForVirtual] - 启用虚拟滚动的最小条目数
   */
  constructor({ container, emptyState, itemHeight = 80, minItemsForVirtual = 60 }) {
    this.container = container;
    this.emptyState = emptyState;
    this.minItemsForVirtual = minItemsForVirtual;

    this.virtualList = new VirtualList({
      container: this.container,
      itemHeight: itemHeight,
      overscan: 10,
      renderItem: this._renderItem.bind(this),
    });
  }

  /**
   * 渲染单个列表项（子类必须实现）
   * @param {Object} item 
   * @returns {string} HTML 字符串
   * @protected
   */
  _renderItem(item) {
    throw new Error("_renderItem must be implemented by subclass");
  }

  /**
   * 更新列表数据
   * @param {Array} items - 数据列表
   * @param {boolean} [loading] - 是否加载中
   * @param {string} [error] - 错误信息
   */
  update(items, loading = false, error = null) {
    if (loading) {
      this._handleLoading();
      return;
    }

    this._updateEmptyState(items.length === 0, error);

    if (items.length >= this.minItemsForVirtual) {
      if (!this.virtualList.enabled) {
        this.virtualList.mount();
      }
      this.virtualList.setItems(items);
    } else {
      if (this.virtualList.enabled) {
        this.virtualList.unmount();
      }
      this.container.innerHTML = items.map((item) => this._renderItem(item)).join("");
    }
  }

  /**
   * 处理加载状态
   * @protected
   */
  _handleLoading() {
    this.virtualList.unmount();
    this.container.innerHTML = "";

    if (this.emptyState) {
      this.emptyState.hidden = false;
      const title = this.emptyState.querySelector(".empty__title");
      const desc = this.emptyState.querySelector(".empty__desc");
      if (title) title.textContent = "加载中…";
      if (desc) desc.textContent = "正在获取数据";
    }
  }

  /**
   * 更新空状态/错误状态显示
   * @param {boolean} isEmpty 
   * @param {string} [error] 
   * @protected
   */
  _updateEmptyState(isEmpty, error) {
    if (!this.emptyState) return;

    this.emptyState.hidden = !isEmpty;
    if (isEmpty) {
      const title = this.emptyState.querySelector(".empty__title");
      const desc = this.emptyState.querySelector(".empty__desc");
      if (title) title.textContent = error ? "加载失败" : "暂无数据";
      if (desc) desc.textContent = error ? error : "没有找到匹配的记录";
    }
  }
}
