"""Client-side, typo-tolerant search autocomplete widget for Streamlit.

Perfume Scanner has no product database -- every search triggers a live
scrape across 14 retailer storefronts (see `scraper.py`). Autocomplete
therefore runs entirely in the browser against the small, static
catalog in `data/perfume_catalog.py`. It never calls back into
Streamlit/Python while typing, so it adds *zero* load to the backend
or the scraper, and keystroke response is limited only by the browser.

Why a hand-rolled component instead of a third-party Streamlit
autocomplete package: this keeps the dependency footprint tiny (Fuse.js
is loaded from a CDN, no extra Python packages, no custom frontend
build step) and lets the widget stay a thin layer on top of the
existing `st.form` / `st.text_input` -- the rest of `app.py`'s submit
handling is untouched.

How it talks to the real `st.text_input`:
- `st.components.v1.html` renders our script inside a sandboxed
  iframe with no built-in two-way data binding.
- That iframe is served from the same origin as the main Streamlit
  page, so plain-JS `window.parent.document` access is allowed (no
  CORS/X-Frame issues) -- this is a well-known, safe technique for
  Streamlit custom widgets that don't need a full component build.
- We locate the real input by its accessible label, attach a single
  *debounced* `input` listener directly to it (guarded so repeated
  Streamlit reruns don't double-bind), and render the suggestions
  dropdown as a sibling positioned under it in the parent document.
- Selecting a suggestion sets the input's value using the native
  property setter + a dispatched `input` event (the standard trick to
  notify a React-controlled input of a programmatic change), then
  clicks the form's existing submit button so the rest of the app's
  scrape/compare flow runs completely unchanged.
"""

from __future__ import annotations

import json

import streamlit.components.v1 as components

from perfume_scanner.data.perfume_catalog import PERFUME_CATALOG


def render_search_autocomplete(
    input_label: str,
    limit: int = 8,
    debounce_ms: int = 150,
) -> None:
    """Wires up a debounced, typo-tolerant autocomplete dropdown.

    Args:
        input_label: The `label` passed to the target `st.text_input`
            (used to locate its rendered `aria-label` in the DOM).
        limit: Max number of suggestions to show at once.
        debounce_ms: Idle time (ms) after the last keystroke before the
            catalog is re-searched, so we don't re-filter on every
            single keypress.
    """
    catalog_json = json.dumps(PERFUME_CATALOG)
    label_json = json.dumps(input_label)

    component_html = f"""
    <script src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js"></script>
    <script>
    (function () {{
        const CATALOG = {catalog_json};
        const INPUT_LABEL = {label_json};
        const DEBOUNCE_MS = {debounce_ms};
        const MAX_RESULTS = {limit};

        function debounce(fn, delay) {{
            let timer = null;
            return function (...args) {{
                clearTimeout(timer);
                timer = setTimeout(() => fn.apply(this, args), delay);
            }};
        }}

        // Standard trick to update a React-controlled input from outside
        // React: the native setter bypasses React's own value tracking,
        // and the dispatched 'input' event lets React pick up the change.
        function setNativeValue(el, value) {{
            const setter = Object.getOwnPropertyDescriptor(
                Object.getPrototypeOf(el), "value"
            ).set;
            setter.call(el, value);
            el.dispatchEvent(new Event("input", {{ bubbles: true }}));
        }}

        // A single, shared resize/scroll listener is bound to
        // `window.parent` once per page load (not once per Streamlit
        // rerun). Every `init()` run just updates which `positionDropdown`
        // closure the shared listener delegates to, instead of attaching
        // a brand-new listener each time -- otherwise every rerun would
        // leak another closure onto the long-lived parent window.
        function ensurePositionListenerBound() {{
            const parent = window.parent;
            if (!parent.__pfAutocompletePosition) {{
                parent.__pfAutocompletePosition = {{ current: null }};
            }}
            if (!parent.__pfAutocompletePositionListenerBound) {{
                parent.__pfAutocompletePositionListenerBound = true;
                const reposition = () => {{
                    if (typeof parent.__pfAutocompletePosition.current === "function") {{
                        parent.__pfAutocompletePosition.current();
                    }}
                }};
                parent.addEventListener("resize", reposition);
                parent.addEventListener("scroll", reposition, true);
            }}
        }}

        let fuseLoadAttempts = 0;
        const MAX_FUSE_LOAD_ATTEMPTS = 30; // ~3s of polling at 100ms

        function init() {{
            // Fuse.js loads asynchronously from the CDN <script> tag above.
            // If it hasn't finished (slow network) or never will (CDN
            // blocked/offline), poll briefly then give up silently -- the
            // real text input and form submit button keep working exactly
            // as before, the user just won't see suggestions.
            if (typeof Fuse === "undefined") {{
                fuseLoadAttempts += 1;
                if (fuseLoadAttempts <= MAX_FUSE_LOAD_ATTEMPTS) {{
                    setTimeout(init, 100);
                }}
                return;
            }}

            const parentDoc = window.parent.document;
            const input = parentDoc.querySelector(
                `input[aria-label="${{INPUT_LABEL}}"]`
            );
            if (!input) {{
                setTimeout(init, 100);
                return;
            }}
            // Guard against re-binding on every Streamlit rerun (the
            // parent document persists across reruns; only this iframe
            // is recreated).
            if (input.dataset.pfAutocompleteBound === "true") {{
                return;
            }}
            input.dataset.pfAutocompleteBound = "true";
            input.setAttribute("autocomplete", "off");

            const fuse = new Fuse(CATALOG, {{
                includeScore: true,
                threshold: 0.4,
                ignoreLocation: true,
                minMatchCharLength: 1,
            }});

            // Reuse the dropdown from a prior rerun if one is still
            // attached to the parent document instead of appending a new
            // one every time -- otherwise hidden, orphaned dropdown
            // elements would accumulate in `body` across reruns.
            let dropdown = parentDoc.getElementById("pf-autocomplete-dropdown");
            if (!dropdown) {{
                dropdown = parentDoc.createElement("div");
                dropdown.id = "pf-autocomplete-dropdown";
                parentDoc.body.appendChild(dropdown);
            }}
            Object.assign(dropdown.style, {{
                position: "absolute",
                zIndex: 9999,
                background: "#121216",
                border: "1px solid rgba(255, 26, 64, 0.35)",
                borderRadius: "10px",
                boxShadow: "0 10px 30px rgba(0, 0, 0, 0.55)",
                marginTop: "6px",
                overflowY: "auto",
                maxHeight: "260px",
                display: "none",
            }});

            function positionDropdown() {{
                const rect = input.getBoundingClientRect();
                dropdown.style.left = `${{rect.left + window.parent.scrollX}}px`;
                dropdown.style.top = `${{rect.bottom + window.parent.scrollY}}px`;
                dropdown.style.width = `${{rect.width}}px`;
            }}

            function hideDropdown() {{
                dropdown.style.display = "none";
                dropdown.innerHTML = "";
            }}

            function submitForm() {{
                const submitBtn = parentDoc.querySelector(
                    '[data-testid="stFormSubmitButton"] button'
                );
                if (submitBtn) {{
                    setTimeout(() => submitBtn.click(), 80);
                }}
            }}

            function selectSuggestion(name) {{
                setNativeValue(input, name);
                hideDropdown();
                input.focus();
                submitForm();
            }}

            // The catalog is only a small hint list, not an exhaustive
            // product database (see data/perfume_catalog.py) -- it must
            // never gate what a user is allowed to search for. When
            // nothing matches (e.g. "Ajmal Shiro", which isn't in the
            // catalog yet), show a clear "search anyway" affordance
            // instead of silently hiding the dropdown, so it's obvious
            // free-text search still works exactly as before.
            function selectFreeTextSearch() {{
                hideDropdown();
                input.focus();
                submitForm();
            }}

            function renderNoMatchFallback(query) {{
                positionDropdown();
                dropdown.innerHTML = "";
                const fallback = parentDoc.createElement("div");
                fallback.textContent = `Search for "${{query}}"`;
                Object.assign(fallback.style, {{
                    padding: "10px 14px",
                    cursor: "pointer",
                    color: "#b0b3c2",
                    fontStyle: "italic",
                    fontSize: "0.88rem",
                }});
                fallback.addEventListener("mouseenter", () => {{
                    fallback.style.background = "rgba(255, 26, 64, 0.18)";
                }});
                fallback.addEventListener("mouseleave", () => {{
                    fallback.style.background = "transparent";
                }});
                fallback.addEventListener("mousedown", (evt) => {{
                    evt.preventDefault();
                    selectFreeTextSearch();
                }});
                dropdown.appendChild(fallback);
                dropdown.style.display = "block";
            }}

            function renderResults(query, names) {{
                if (!names.length) {{
                    renderNoMatchFallback(query);
                    return;
                }}
                positionDropdown();
                dropdown.innerHTML = "";
                names.forEach((name) => {{
                    const item = parentDoc.createElement("div");
                    item.textContent = name;
                    Object.assign(item.style, {{
                        padding: "10px 14px",
                        cursor: "pointer",
                        color: "#ffffff",
                        fontSize: "0.92rem",
                        borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                    }});
                    item.addEventListener("mouseenter", () => {{
                        item.style.background = "rgba(255, 26, 64, 0.18)";
                    }});
                    item.addEventListener("mouseleave", () => {{
                        item.style.background = "transparent";
                    }});
                    // 'mousedown' (not 'click') fires before the input's
                    // blur handler hides the dropdown.
                    item.addEventListener("mousedown", (evt) => {{
                        evt.preventDefault();
                        selectSuggestion(name);
                    }});
                    dropdown.appendChild(item);
                }});
                dropdown.style.display = "block";
            }}

            const runSearch = debounce(function () {{
                const query = input.value.trim();
                if (!query) {{
                    hideDropdown();
                    return;
                }}
                const results = fuse
                    .search(query, {{ limit: MAX_RESULTS }})
                    .map((r) => r.item);
                renderResults(query, results);
            }}, DEBOUNCE_MS);

            input.addEventListener("input", runSearch);
            input.addEventListener("blur", () => setTimeout(hideDropdown, 150));
            ensurePositionListenerBound();
            window.parent.__pfAutocompletePosition.current = positionDropdown;
        }}

        init();
    }})();
    </script>
    """

    components.html(component_html, height=0)
