"""Generic form extraction and filling on a Playwright page or frame.

`extract()` tags every form control with `data-ll-id` and returns a field list:
  {id, label, type, required, options, selector, option_selectors?}
Types: text | email | tel | url | number | textarea | select | radio | checkbox | checkbox_group | combobox | file
"""
import re

EXTRACT_JS = r"""
(root) => {
  const scope = root ? document.querySelector(root) : document;
  if (!scope) return [];
  const clean = (t) => (t || '').replace(/\s+/g, ' ').trim();
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
  };
  const textOf = (id) => { const e = id && document.getElementById(id); return e ? clean(e.innerText) : ''; };
  const labelFor = (el) => {
    if (el.id) {
      const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (l && clean(l.innerText)) return clean(l.innerText);
    }
    const anc = el.closest('label');
    if (anc && clean(anc.innerText)) return clean(anc.innerText);
    if (el.getAttribute('aria-labelledby')) {
      const t = el.getAttribute('aria-labelledby').split(' ').map(textOf).join(' ');
      if (clean(t)) return clean(t);
    }
    if (el.getAttribute('aria-label')) return clean(el.getAttribute('aria-label'));
    const fs = el.closest('fieldset');
    if (fs) { const lg = fs.querySelector('legend'); if (lg && clean(lg.innerText)) return clean(lg.innerText); }
    const wrap = el.closest('.field, .application-question, [class*="question"], [class*="field"], [class*="Field"], li, .form-group');
    if (wrap) {
      const l = wrap.querySelector('label, legend, .label, [class*="label"], [class*="Label"]');
      if (l && clean(l.innerText)) return clean(l.innerText);
    }
    return clean(el.getAttribute('placeholder') || el.getAttribute('name') || '');
  };
  const groupLabel = (el) => {
    const fs = el.closest('fieldset');
    if (fs) { const lg = fs.querySelector('legend'); if (lg && clean(lg.innerText)) return clean(lg.innerText); }
    const group = el.closest('[role="radiogroup"], [role="group"]');
    if (group) {
      const by = group.getAttribute('aria-labelledby');
      if (by && clean(textOf(by))) return clean(textOf(by));
      if (group.getAttribute('aria-label')) return clean(group.getAttribute('aria-label'));
    }
    const wrap = el.closest('.field, .application-question, [class*="question"], [class*="field"], [class*="Field"], li, .form-group');
    if (wrap) {
      const l = wrap.querySelector('label:not(:has(input)), legend, .label, [class*="label"]:not(:has(input))');
      if (l && clean(l.innerText)) return clean(l.innerText);
    }
    return el.name || '';
  };
  const isRequired = (el, label) =>
    el.required || el.getAttribute('aria-required') === 'true' || /\*\s*$|\*/.test(label || '');

  let n = parseInt(document.body.getAttribute('data-ll-next') || '0');
  const tag = (el) => {
    if (!el.hasAttribute('data-ll-id')) el.setAttribute('data-ll-id', String(n++));
    return `[data-ll-id="${el.getAttribute('data-ll-id')}"]`;
  };

  const fields = [];
  const groups = {};
  const controls = scope.querySelectorAll('input, select, textarea');
  for (const el of controls) {
    const type = (el.getAttribute('type') || el.tagName).toLowerCase();
    if (['hidden', 'submit', 'button', 'reset', 'image', 'search'].includes(type)) continue;
    if (el.disabled || el.readOnly && type !== 'file') continue;
    if (type !== 'file' && type !== 'radio' && type !== 'checkbox' && !visible(el)) continue;
    if (el.closest('[aria-hidden="true"]') && type !== 'file') continue;

    if (type === 'radio' || type === 'checkbox') {
      const name = el.name || el.id;
      const key = `${type}:${name}`;
      const optLabel = labelFor(el);
      const sameName = name ? document.querySelectorAll(`input[type="${type}"][name="${CSS.escape(name)}"]`).length : 1;
      if (type === 'checkbox' && sameName <= 1) {
        fields.push({ id: tag(el), label: optLabel, type: 'checkbox', required: isRequired(el, optLabel), options: [], selector: tag(el) });
        continue;
      }
      if (!groups[key]) {
        const label = groupLabel(el);
        groups[key] = { id: tag(el), label, type: type === 'radio' ? 'radio' : 'checkbox_group',
                        required: isRequired(el, label), options: [], option_selectors: {}, selector: tag(el) };
        fields.push(groups[key]);
      }
      groups[key].options.push(optLabel || el.value);
      groups[key].option_selectors[optLabel || el.value] = tag(el);
      if (el.required) groups[key].required = true;
      continue;
    }

    const label = labelFor(el);
    let ftype = el.tagName === 'SELECT' ? 'select' : el.tagName === 'TEXTAREA' ? 'textarea' : type;
    if (el.getAttribute('role') === 'combobox' && el.tagName === 'INPUT') ftype = 'combobox';
    if (!['text', 'email', 'tel', 'url', 'number', 'textarea', 'select', 'combobox', 'file', 'date'].includes(ftype)) ftype = 'text';
    const field = { id: tag(el), label, type: ftype, required: isRequired(el, label), options: [], selector: tag(el) };
    if (ftype === 'select') field.options = [...el.options].map(o => clean(o.textContent)).filter(Boolean);
    if (ftype === 'file') field.accept_resume = /pdf|doc/.test(el.getAttribute('accept') || '');
    fields.push(field);
  }
  document.body.setAttribute('data-ll-next', String(n));
  return fields;
}
"""

ERRORS_JS = r"""
(root) => [...(root ? (document.querySelector(root) || document) : document).querySelectorAll('[role="alert"], .error, .field-error, [class*="error"]:not(input), [aria-invalid="true"]')]
  .filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map(e => (e.innerText || e.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim())
  .filter(t => t && t.length < 200)
  .slice(0, 10)
"""


def _clean_label(label: str) -> str:
    return (label or "").strip().rstrip("*").strip() or "(unlabelled field)"


async def extract(frame, root: str | None = None) -> list[dict]:
    """`root`: CSS selector limiting extraction to one container (e.g. a modal dialog)."""
    fields = await frame.evaluate(EXTRACT_JS, root)
    for f in fields:
        f["label"] = _clean_label(f["label"])
        f["id"] = re.search(r'"(\d+)"', f["selector"]).group(1)
    for f in fields:
        if f["type"] == "combobox":
            f["options"] = await combobox_options(frame, f["selector"])
    return fields


async def combobox_options(frame, selector: str) -> list[str]:
    """Open a custom (react-select style) dropdown, read its options, close it again."""
    try:
        el = frame.locator(selector)
        await el.click(timeout=3000)
        await frame.wait_for_timeout(300)
        options = await frame.locator('[role="option"]').all_inner_texts()
        await el.press("Escape")
        return [o.strip() for o in options if o.strip()][:100]
    except Exception:
        return []


async def form_errors(frame, root: str | None = None) -> list[str]:
    try:
        return await frame.evaluate(ERRORS_JS, root)
    except Exception:
        return []


READ_JS = r"""
(el) => {
  if (el.type === 'file') return el.files && el.files.length ? el.files[0].name : '';
  if (el.type === 'checkbox' || el.type === 'radio') return el.checked;
  if (el.tagName === 'SELECT') { const o = el.selectedOptions[0]; return o && o.value !== '' ? o.textContent.trim() : ''; }
  if (el.getAttribute('role') === 'combobox') {
    let node = el;
    for (let i = 0; i < 6 && node; i++) {
      node = node.parentElement;
      const chosen = node && node.querySelector('[class*="singleValue"], [class*="single-value"]');
      if (chosen) return chosen.textContent.trim();
    }
  }
  return el.value || '';
}
"""


async def _read(frame, selector: str):
    loc = frame.locator(selector).first
    if not await loc.count():
        return None  # element gone (e.g. an earlier step of a multi-step form)
    return await loc.evaluate(READ_JS, timeout=3000)


async def read_value(frame, field: dict):
    """Current value of a field as the page sees it (option label for choice fields); None if it's gone."""
    try:
        if field["type"] in ("radio", "checkbox_group"):
            chosen, present = [], False
            for opt, sel in (field.get("option_selectors") or {}).items():
                state = await _read(frame, sel)
                present = present or state is not None
                if state:
                    chosen.append(opt)
            if not present:
                return None
            return chosen[0] if field["type"] == "radio" and chosen else (chosen or "")
        return await _read(frame, field["selector"])
    except Exception:
        return None


async def fill_field(frame, field: dict, files: dict[str, str]) -> bool:
    """Write field['value'] into the page. Returns False when the control rejected it."""
    value = field.get("value")
    if value in (None, "", []):
        return True
    loc = frame.locator(field["selector"]).first
    ftype = field["type"]
    try:
        if ftype == "file":
            path = files.get(str(value))
            if not path:
                return False
            await loc.set_input_files(path, timeout=10000)
        elif ftype == "select":
            try:
                await loc.select_option(label=str(value), timeout=5000)
            except Exception:
                await loc.select_option(value=str(value), timeout=5000)
        elif ftype == "radio":
            sel = field.get("option_selectors", {}).get(str(value))
            if not sel:
                return False
            await frame.locator(sel).first.check(force=True, timeout=5000)
        elif ftype == "checkbox_group":
            for v in value if isinstance(value, list) else [value]:
                sel = field.get("option_selectors", {}).get(str(v))
                if sel:
                    await frame.locator(sel).first.check(force=True, timeout=5000)
        elif ftype == "checkbox":
            if value is True or str(value).lower() in ("yes", "true"):
                await loc.check(force=True, timeout=5000)
        elif ftype == "combobox":
            await loc.click(timeout=5000)
            await loc.fill(str(value), timeout=5000)
            await frame.wait_for_timeout(400)
            option = frame.locator('[role="option"]', has_text=str(value)).first
            if await option.count():
                await option.click(timeout=5000)
            else:
                await loc.press("Enter")
        else:
            await loc.fill(str(value), timeout=5000)
        return True
    except Exception as err:
        print(f"apply: could not fill {field['label']!r}: {err}")
        return False
