#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
import urllib.parse
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "dashboard.yml"
OUTPUT_FILE = ROOT / "index.html"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def normalize(data: dict[str, Any]) -> dict[str, Any]:
    categories = data.get("categories")
    if not isinstance(categories, list):
        raise ValueError("Expected top-level 'categories' list in dashboard.yml")

    normalized_categories: list[dict[str, Any]] = []
    total_items = 0

    for category in categories:
        if not isinstance(category, dict):
            raise ValueError("Each category must be a mapping")

        name = str(category.get("name", "")).strip()
        if not name:
            raise ValueError("Each category requires a non-empty 'name'")

        icon = str(category.get("icon") or "lucide:folder").strip()
        items = category.get("items")
        if not isinstance(items, list):
            raise ValueError(f"Category '{name}' requires an 'items' list")

        normalized_items: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"Category '{name}' contains an invalid item")

            item_name = str(item.get("name", "")).strip()
            item_url = str(item.get("url", "")).strip()
            if not item_name or not item_url:
                raise ValueError(f"Each item in '{name}' requires 'name' and 'url'")

            tags = item.get("tags") or []
            if not isinstance(tags, list):
                raise ValueError(f"Item '{item_name}' in '{name}' has invalid 'tags'")

            icon_name = str(item.get("icon") or "lucide:link").strip()
            search_blob = " ".join(
                [
                    name,
                    item_name,
                    item_url,
                    " ".join(str(tag).strip() for tag in tags if str(tag).strip()),
                ]
            ).lower()

            normalized_items.append(
                {
                    "name": item_name,
                    "url": item_url,
                    "icon": icon_name,
                    "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
                    "searchText": search_blob,
                }
            )

        total_items += len(normalized_items)
        normalized_categories.append(
            {
                "name": name,
                "icon": icon,
                "itemCount": len(normalized_items),
                "items": normalized_items,
            }
        )

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "categoryCount": len(normalized_categories),
        "itemCount": total_items,
        "categories": normalized_categories,
    }


def json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def favicon_data_uri() -> str:
    svg = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>
  <defs>
    <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='#0b0f17'/>
      <stop offset='100%' stop-color='#111827'/>
    </linearGradient>
    <linearGradient id='accent' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='#f472b6'/>
      <stop offset='100%' stop-color='#ec4899'/>
    </linearGradient>
  </defs>
  <rect x='4' y='4' width='56' height='56' rx='14' fill='url(#bg)'/>
  <path d='M19 22 L29 32 L19 42' fill='none' stroke='url(#accent)' stroke-width='5' stroke-linecap='round' stroke-linejoin='round'/>
  <rect x='33' y='38' width='14' height='4.5' rx='2.25' fill='url(#accent)'/>
</svg>"""
    return "data:image/svg+xml," + urllib.parse.quote(svg)


def build_html(data: dict[str, Any]) -> str:
    title = "Dashboard"
    payload = json_for_script(data)
    favicon = favicon_data_uri()
    generated_dt = datetime.fromisoformat(data["generatedAt"])
    display_dt = generated_dt.astimezone(ZoneInfo("Europe/Amsterdam"))
    generated_at = escape(data["generatedAt"])
    generated_time = escape(display_dt.strftime("%H:%M"))
    generated_date = escape(display_dt.strftime("%d-%m-%Y"))

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="icon" href="{favicon}" type="image/svg+xml">
    <meta name="description" content="Bookmark dashboard generated from YAML.">
    <script>
      tailwind.config = {{
        theme: {{
          extend: {{
            fontFamily: {{
              sans: ['\"Inter\"', 'Avenir Next', 'Segoe UI', 'ui-sans-serif', 'system-ui', 'sans-serif']
            }},
            colors: {{
              slate: {{
                950: '#090c12'
              }}
            }}
          }}
        }}
      }};
    </script>
    <script defer src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script defer src="https://code.iconify.design/3/3.1.1/iconify.min.js"></script>
    <style>
      :root {{
        color-scheme: dark;
      }}
      body {{
        background:
          radial-gradient(circle at top, rgba(45, 212, 191, 0.08), transparent 28%),
          radial-gradient(circle at 85% 0%, rgba(168, 85, 247, 0.10), transparent 24%),
          linear-gradient(180deg, #0b0f17 0%, #090d14 100%);
      }}
      .surface {{
        background: rgba(12, 18, 28, 0.34);
        border: 1px solid rgba(139, 92, 246, 0.12);
        box-shadow: inset 0 1px 0 rgba(45, 212, 191, 0.03);
      }}
      .surface-soft {{
        background: transparent;
        border: 0;
      }}
      .tag-chip {{
        background: rgba(31, 41, 55, 0.55);
        border: 1px solid rgba(139, 92, 246, 0.16);
      }}
      .section-grid {{
        display: grid;
        gap: 1.25rem;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr));
        align-items: start;
      }}
      .bookmark-list {{
        display: grid;
        gap: 0.35rem;
      }}
      [x-cloak] {{
        display: none !important;
      }}
    </style>
  </head>
  <body class="min-h-screen text-slate-100 antialiased">
    <script id="dashboard-data" type="application/json">{payload}</script>
    <main
      x-data="dashboardApp()"
      x-init="init()"
      class="mx-auto min-h-screen w-full px-4 py-8 sm:px-6 lg:px-8"
    >
      <header class="mx-auto max-w-3xl text-center">
        <h1 class="text-2xl font-semibold tracking-tight text-white sm:text-3xl">Dashboard</h1>
        <div class="mt-2 flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs text-slate-400">
          <span><span class="text-cyan-300" x-text="totalItemCount"></span> bookmarks</span>
          <span><span class="text-fuchsia-300" x-text="categoryCount"></span> categories</span>
          <template x-if="query">
            <span><span class="text-violet-300" x-text="visibleItemCount"></span> shown</span>
          </template>
        </div>
      </header>

      <section class="mx-auto mt-8 max-w-2xl">
        <label class="flex items-center gap-3 border-b border-slate-800 px-4 py-3 transition focus-within:border-fuchsia-500/70">
          <span class="iconify text-lg text-fuchsia-400/80" data-icon="lucide:search"></span>
          <input
            x-ref="search"
            x-model="query"
            type="search"
            placeholder="Search"
            class="w-full border-0 bg-transparent text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-0 sm:text-base"
            autocomplete="off"
            spellcheck="false"
          >
          <kbd class="hidden rounded-md border border-violet-500/20 bg-slate-900/80 px-2 py-1 text-xs text-slate-500 sm:block">/</kbd>
        </label>
      </section>

      <section class="mx-auto mt-12 max-w-[1500px]" x-show="visibleItemCount > 0" x-cloak>
        <div class="section-grid">
          <template x-for="category in filteredCategories" :key="category.name">
            <section class="surface rounded-2xl px-5 py-4">
              <div class="mb-4 flex items-center justify-between gap-3 border-b border-violet-500/10 pb-3">
                <div class="flex min-w-0 items-center gap-3">
                  <span class="iconify shrink-0 text-base text-fuchsia-400/80" :data-icon="category.icon"></span>
                  <h2 class="truncate text-sm font-medium text-slate-200" x-text="category.name"></h2>
                </div>
                <span class="text-[11px] text-slate-600" x-text="category.items.length"></span>
              </div>
              <div class="bookmark-list">
                <template x-for="item in category.items" :key="item.url">
                  <a
                    :href="item.url"
                    target="_blank"
                    rel="noreferrer noopener"
                    class="group flex items-start gap-4 rounded-xl px-3 py-3 transition hover:bg-fuchsia-500/[0.05]"
                  >
                    <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-slate-900/85 text-cyan-300/80 transition group-hover:text-cyan-200">
                      <span class="iconify text-xl" :data-icon="item.icon"></span>
                    </div>
                    <div class="min-w-0 flex-1">
                      <div class="flex items-center gap-2">
                        <h3 class="truncate text-sm font-medium text-white" x-text="item.name"></h3>
                        <span class="iconify shrink-0 text-slate-700 transition group-hover:text-fuchsia-300" data-icon="lucide:arrow-up-right"></span>
                      </div>
                      <p class="mt-1 max-w-[34ch] truncate text-xs text-slate-500" x-text="item.url"></p>
                      <div class="mt-2 flex flex-wrap gap-2" x-show="item.tags.length">
                        <template x-for="tag in item.tags" :key="tag">
                          <span class="tag-chip inline-block rounded px-1.5 py-0.5 text-[9px] uppercase tracking-wide text-slate-300" x-text="tag"></span>
                        </template>
                      </div>
                    </div>
                  </a>
                </template>
              </div>
            </section>
          </template>
        </div>
      </section>

      <section
        x-show="visibleItemCount === 0"
        x-cloak
        class="mx-auto mt-14 max-w-2xl text-center"
      >
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-slate-900/80 text-slate-500">
          <span class="iconify text-2xl" data-icon="lucide:search-x"></span>
        </div>
        <h2 class="mt-4 text-lg font-medium text-white">No matches</h2>
        <p class="mt-2 text-sm text-slate-500">Try another search term.</p>
      </section>

      <footer class="mt-10 text-center text-[10px] text-slate-500">
        <time datetime="{generated_at}">Dashboard: {generated_time} {generated_date}</time>
      </footer>
    </main>

    <script>
      function dashboardApp() {{
        const data = JSON.parse(document.getElementById('dashboard-data').textContent);
        return {{
          query: '',
          categories: data.categories,
          totalItemCount: data.itemCount,
          categoryCount: data.categoryCount,
          init() {{
            window.addEventListener('keydown', (event) => {{
              const target = event.target;
              const typingInField = target && (
                target.tagName === 'INPUT' ||
                target.tagName === 'TEXTAREA' ||
                target.isContentEditable
              );

              if (event.key === '/' && !typingInField) {{
                event.preventDefault();
                this.$refs.search.focus();
                this.$refs.search.select();
              }}

              if (event.key === 'Enter' && this.visibleItemCount > 0 && !event.metaKey && !event.ctrlKey) {{
                if (typingInField || target === document.body) {{
                  event.preventDefault();
                  this.openFirstVisible();
                }}
              }}
            }});
          }},
          get normalizedQuery() {{
            return this.query.trim().toLowerCase();
          }},
          get filteredCategories() {{
            const query = this.normalizedQuery;
            return this.categories
              .map((category) => {{
                const items = !query
                  ? category.items
                  : category.items.filter((item) => item.searchText.includes(query));
                return {{
                  ...category,
                  items,
                }};
              }})
              .filter((category) => category.items.length > 0);
          }},
          get visibleItemCount() {{
            return this.filteredCategories.reduce((count, category) => count + category.items.length, 0);
          }},
          openFirstVisible() {{
            const first = this.filteredCategories[0] && this.filteredCategories[0].items[0];
            if (first) {{
              window.open(first.url, '_blank', 'noopener,noreferrer');
            }}
          }}
        }};
      }}
    </script>
  </body>
</html>
"""


def main() -> int:
    data = normalize(load_yaml(SOURCE))
    OUTPUT_FILE.write_text(build_html(data), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
