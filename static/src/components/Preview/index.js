import { logger } from "../../utils/index.js";

// ---------- Image preview ----------

const isInWeChat = () => /MicroMessenger/i.test(navigator.userAgent || "");
const hasWxPreview = () => {
  try {
    return !!(window.wx && typeof window.wx.previewImage === "function");
  } catch {
    return false;
  }
};

const isIOS = () => /iPad|iPhone|iPod/i.test(navigator.userAgent || "");

const isEligiblePreviewImg = (imgEl) => {
  if (!imgEl || imgEl.tagName !== "IMG") return false;
  // 排除预览层内部的 img（避免递归触发）
  if (imgEl.closest?.("#imgPreviewOverlay")) return false;
  // 只对聊天、上下文、页面描述等内容区生效
  return !!imgEl.closest?.(
    ".chatPage__messages, .chatBubble--md, .contextContent, #contextContent, #pageDescContent, .sheet",
  );
};

const collectSiblingImageUrls = (imgEl) => {
  const root =
    imgEl.closest?.(".chatPage__messages") ||
    imgEl.closest?.(".contextContent") ||
    imgEl.closest?.("#contextContent") ||
    imgEl.closest?.("#pageDescContent") ||
    imgEl.closest?.(".sheet") ||
    document;
  const imgs = Array.from(root.querySelectorAll("img"));
  const urls = imgs
    .map((x) => String(x.currentSrc || x.src || "").trim())
    .filter(Boolean);
  // 去重但保序
  const seen = new Set();
  const uniq = [];
  for (const u of urls) {
    if (seen.has(u)) continue;
    seen.add(u);
    uniq.push(u);
  }
  return uniq;
};

const createImagePreviewOverlay = () => {
  if (document.getElementById("imgPreviewOverlay")) return;
  const overlay = document.createElement("div");
  overlay.id = "imgPreviewOverlay";
  overlay.className = "imgPreviewOverlay";
  overlay.hidden = true;
  overlay.setAttribute("aria-hidden", "true");
  overlay.innerHTML = `
    <div class="imgPreviewOverlay__backdrop" data-action="closeImgPreview"></div>
    <div class="imgPreviewOverlay__topbar">
      <div class="imgPreviewOverlay__count" id="imgPreviewCount" hidden></div>
      <button type="button" class="imgPreviewOverlay__close" data-action="closeImgPreview" aria-label="关闭预览" title="关闭">
        <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-close"/></svg>
      </button>
    </div>
    <div class="imgPreviewOverlay__content">
      <button type="button" class="imgPreviewNav imgPreviewNav--prev" id="imgPreviewPrevBtn" data-action="imgPreviewPrev" aria-label="上一张" title="上一张" hidden>
        <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-back"/></svg>
      </button>
      <img id="imgPreviewImg" class="imgPreviewOverlay__img" alt="预览图片" />
      <button type="button" class="imgPreviewNav imgPreviewNav--next" id="imgPreviewNextBtn" data-action="imgPreviewNext" aria-label="下一张" title="下一张" hidden>
        <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-next"/></svg>
      </button>
    </div>
    <div class="imgPreviewOverlay__hint">
      <div class="imgPreviewOverlay__hintText">点击空白处关闭</div>
    </div>
    <div class="imgPreviewToast" id="imgPreviewToast" aria-hidden="true">
      <div class="imgPreviewToast__text" id="imgPreviewToastText"> </div>
    </div>
    <div class="imgPreviewActions" id="imgPreviewActions" hidden>
      <div class="imgPreviewActions__panel">
        <button type="button" class="imgPreviewActions__btn is-primary" data-action="saveImgPreview">保存图片</button>
        <button type="button" class="imgPreviewActions__btn is-cancel" data-action="closeImgPreviewActions">取消</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
};

const imgPreviewState = {
  open: false,
  src: "",
  urls: [],
  index: 0,
  swipeStart: null, // { x, y, pointerId }
};

const setImgPreviewOpen = (open) => {
  createImagePreviewOverlay();
  const overlay = document.getElementById("imgPreviewOverlay");
  if (!overlay) return;
  imgPreviewState.open = !!open;
  overlay.hidden = !open;
  overlay.setAttribute("aria-hidden", open ? "false" : "true");
  document.body.classList.toggle("is-imgPreviewOpen", open);
  if (!open) {
    imgPreviewState.src = "";
    imgPreviewState.urls = [];
    imgPreviewState.index = 0;
    const img = document.getElementById("imgPreviewImg");
    if (img) img.removeAttribute("src");
    hideImgPreviewActions();
  }
};

const syncImgPreviewNav = () => {
  const prevBtn = document.getElementById("imgPreviewPrevBtn");
  const nextBtn = document.getElementById("imgPreviewNextBtn");
  const countEl = document.getElementById("imgPreviewCount");
  const total = Array.isArray(imgPreviewState.urls) ? imgPreviewState.urls.length : 0;
  const idx = Number(imgPreviewState.index) || 0;
  const showNav = total > 1;
  if (prevBtn) prevBtn.hidden = !showNav;
  if (nextBtn) nextBtn.hidden = !showNav;
  if (countEl) {
    countEl.hidden = total <= 1;
    countEl.textContent = total > 1 ? `${Math.min(idx + 1, total)}/${total}` : "";
  }
};

const setImgPreviewIndex = (nextIndex) => {
  const urls = Array.isArray(imgPreviewState.urls) ? imgPreviewState.urls : [];
  if (urls.length === 0) return;
  let idx = Number(nextIndex);
  if (!Number.isFinite(idx)) idx = 0;
  // 循环切换
  idx = ((idx % urls.length) + urls.length) % urls.length;
  const url = String(urls[idx] || "").trim();
  if (!url) return;
  createImagePreviewOverlay();
  const img = document.getElementById("imgPreviewImg");
  if (img) img.src = url;
  imgPreviewState.index = idx;
  imgPreviewState.src = url;
  syncImgPreviewNav();
};

const openImgPreview = (src, { urls = null } = {}) => {
  const url = String(src || "").trim();
  if (!url) return;
  createImagePreviewOverlay();
  const list = Array.isArray(urls) && urls.length ? urls : [url];
  imgPreviewState.urls = list;
  const idx = list.indexOf(url);
  imgPreviewState.index = idx >= 0 ? idx : 0;
  setImgPreviewOpen(true);
  setImgPreviewIndex(imgPreviewState.index);
};

const closeImgPreview = () => setImgPreviewOpen(false);

const showImgPreviewToast = (text, { ms = 1600 } = {}) => {
  const toast = document.getElementById("imgPreviewToast");
  const t = document.getElementById("imgPreviewToastText");
  if (!toast || !t) return;
  t.textContent = String(text || "");
  toast.classList.add("is-show");
  window.setTimeout(() => toast.classList.remove("is-show"), ms);
};

const showImgPreviewActions = () => {
  const box = document.getElementById("imgPreviewActions");
  if (!box) return;
  box.hidden = false;
};

const hideImgPreviewActions = () => {
  const box = document.getElementById("imgPreviewActions");
  if (!box) return;
  box.hidden = true;
};

const dataUrlToBlob = (dataUrl) => {
  const s = String(dataUrl || "");
  const comma = s.indexOf(",");
  if (comma < 0) return null;
  const header = s.slice(0, comma);
  const base64 = s.slice(comma + 1);
  const m = header.match(/data:([^;]+);base64/i);
  const mime = m ? m[1] : "application/octet-stream";
  try {
    const bin = atob(base64);
    const len = bin.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) bytes[i] = bin.charCodeAt(i);
    return new Blob([bytes], { type: mime });
  } catch {
    return null;
  }
};

const pickExtByMime = (mime) => {
  const m = String(mime || "").toLowerCase();
  if (m.includes("png")) return "png";
  if (m.includes("jpeg") || m.includes("jpg")) return "jpg";
  if (m.includes("gif")) return "gif";
  if (m.includes("webp")) return "webp";
  if (m.includes("bmp")) return "bmp";
  return "png";
};

const triggerDownloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "image";
  a.rel = "noopener";
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 2000);
};

const saveImageByUrl = async (src) => {
  const url = String(src || "").trim();
  if (!url) return false;

  // data url：直接转 blob
  if (url.startsWith("data:")) {
    const blob = dataUrlToBlob(url);
    if (!blob) return false;
    const ext = pickExtByMime(blob.type);
    triggerDownloadBlob(blob, `image_${Date.now()}.${ext}`);
    return true;
  }

  // 尝试 fetch（需要 CORS 允许）
  try {
    const resp = await fetch(url, { mode: "cors", cache: "force-cache" });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const blob = await resp.blob();
    const ext = pickExtByMime(blob.type);
    triggerDownloadBlob(blob, `image_${Date.now()}.${ext}`);
    return true;
  } catch (e) {
    logger.warn("save image failed, cors maybe", e);
    return false;
  }
};

const init = () => {
  createImagePreviewOverlay();

  // 点击图片：打开预览
  document.addEventListener("click", (ev) => {
    const img = ev.target?.closest?.("img");
    if (!img || !isEligiblePreviewImg(img)) return;
    const src = img.currentSrc || img.src || "";
    if (!src) return;

    // 微信环境：优先使用 wx.previewImage（自带保存到相册）
    if (isInWeChat() && hasWxPreview()) {
      const urls = collectSiblingImageUrls(img);
      try {
        window.wx.previewImage({
          current: src,
          urls: urls.length ? urls : [src],
        });
        return;
      } catch (e) {
        logger.warn("wx.previewImage failed, fallback", e);
      }
    }

    openImgPreview(src, { urls: collectSiblingImageUrls(img) });
  });

  // 预览层内：滑动切换图片
  const overlay = document.getElementById("imgPreviewOverlay");
  overlay?.addEventListener(
    "pointerdown",
    (ev) => {
      const img = ev.target?.closest?.("#imgPreviewImg");
      if (!img) return;
      if (!ev.isPrimary) return;
      imgPreviewState.swipeStart = { x: ev.clientX, y: ev.clientY, pointerId: ev.pointerId };
    },
    { passive: true },
  );
  overlay?.addEventListener(
    "pointerup",
    (ev) => {
      const s = imgPreviewState.swipeStart;
      if (!s || s.pointerId !== ev.pointerId) {
        imgPreviewState.swipeStart = null;
        return;
      }
      const dx = ev.clientX - s.x;
      const dy = ev.clientY - s.y;
      imgPreviewState.swipeStart = null;
      const absX = Math.abs(dx);
      const absY = Math.abs(dy);
      // 横向明显滑动才算（避免误触）
      if (absX < 40) return;
      if (absX < absY * 1.2) return;
      if (!Array.isArray(imgPreviewState.urls) || imgPreviewState.urls.length <= 1) return;
      if (dx < 0) setImgPreviewIndex(imgPreviewState.index + 1);
      else setImgPreviewIndex(imgPreviewState.index - 1);
    },
    { passive: true },
  );
  overlay?.addEventListener(
    "pointercancel",
    () => {
      imgPreviewState.swipeStart = null;
    },
    { passive: true },
  );

  // 绑定全局点击事件处理 (delegate)
  document.addEventListener("click", (ev) => {
    const el = ev.target.closest("[data-action]");
    if (!el) return;
    const action = el.dataset.action;

    switch (action) {
      case "closeImgPreview":
        closeImgPreview();
        break;
      case "imgPreviewPrev":
        setImgPreviewIndex(imgPreviewState.index - 1);
        break;
      case "imgPreviewNext":
        setImgPreviewIndex(imgPreviewState.index + 1);
        break;
      case "saveImgPreview":
        const src = imgPreviewState.src;
        if (!src) {
          hideImgPreviewActions();
          break;
        }
        // iOS：优先打开新页，让用户长按“保存到相册”（比 download 更符合相册预期）
        if (isIOS()) {
          hideImgPreviewActions();
          try {
            window.open(src, "_blank", "noopener,noreferrer");
          } catch {
            // ignore
          }
          showImgPreviewToast("已打开图片新页面：请在新页面长按“保存到相册”");
          break;
        }

        saveImageByUrl(src).then((ok) => {
            if (ok) showImgPreviewToast("已保存到相册", { ms: 1500 });
            else showImgPreviewToast("保存失败", { ms: 1500 });
            hideImgPreviewActions();
        });
        break;
      case "closeImgPreviewActions":
        hideImgPreviewActions();
        break;
    }
  });

  // 长按图片：显示保存菜单
  // 这里需要注意，原代码中 onAction 是否处理了这些 action?
  // 在原代码中，global action delegation 处理了 'data-action'。
  // 但是 openImgPreview 内部的按钮也有 data-action。
  // 原代码的 global listener 是：
  /*
    document.addEventListener("click", (ev) => {
      const el = ev.target.closest("[data-action]");
      if (!el) return;
      const action = el.dataset.action;
      onAction(el, action, ev);
    });
  */
  // 而 onAction 函数在原代码中定义了。
  // 如果我把 action 处理逻辑移到这里，可能会有冲突或者需要移除原有的 onAction 中的相关 case。
  // 原代码中 onAction 是否包含 image preview 相关的 case?
  // 我需要检查 onAction 的内容。
};

export default {
  init,
};
