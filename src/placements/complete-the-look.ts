const STYLE_ID = 'jml-ctl-styles';
const FETCH_TIMEOUT_MS = 500;
const API_BASE = 'https://recs.jewelml.io';

const STYLES = `
  .jml-ctl {
    display: flex;
    gap: 12px;
    overflow-x: auto;
    scrollbar-width: thin;
  }
  .jml-ctl__item {
    flex: 0 0 160px;
  }
  .jml-ctl__item img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
  }
  .jml-ctl__item h3 {
    font-size: 14px;
    font-weight: 600;
    margin: 8px 0 4px;
  }
  .jml-ctl__item p {
    font-size: 13px;
    color: #666;
  }
`;

interface CatalogItem {
  sku: string;
  title: string;
  url: string;
  image: { url: string; alt: string };
  price: { amount: number | null; currency: string };
  brand: string;
}

export interface CompleteTheLookHandle {
  refresh(sku: string): Promise<void>;
}

function ensureStyles(): void {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = STYLES;
  document.head.appendChild(style);
}

function safeHttpUrl(raw: string): string | null {
  try {
    const url = new URL(raw, window.location.href);
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : null;
  } catch {
    return null;
  }
}

function formatPrice(price: CatalogItem['price']): string {
  if (price.amount === null) return '';
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency: price.currency }).format(price.amount);
  } catch {
    return `${price.amount} ${price.currency}`;
  }
}

function renderItem(item: CatalogItem): HTMLElement | null {
  const href = safeHttpUrl(item.url);
  const src = safeHttpUrl(item.image.url);
  if (!href || !src) return null;

  const link = document.createElement('a');
  link.className = 'jml-ctl__item';
  link.href = href;
  link.dataset.sku = item.sku;

  const img = document.createElement('img');
  img.src = src;
  img.alt = item.image.alt;

  const title = document.createElement('h3');
  title.textContent = item.title;

  const meta = document.createElement('p');
  const price = formatPrice(item.price);
  meta.textContent = price ? `${item.brand} · ${price}` : item.brand;

  link.append(img, title, meta);
  return link;
}

async function fetchItems(integrationId: string, sku: string): Promise<CatalogItem[]> {
  const endpoint = `${API_BASE}/v1/${encodeURIComponent(integrationId)}/complete-the-look?sku=${encodeURIComponent(sku)}`;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(endpoint, { signal: controller.signal, credentials: 'omit' });
    if (!res.ok) return [];
    const body: { items?: CatalogItem[] } = await res.json();
    return Array.isArray(body.items) ? body.items : [];
  } finally {
    window.clearTimeout(timer);
  }
}

async function render(container: HTMLElement, integrationId: string, sku: string): Promise<void> {
  let items: CatalogItem[];
  try {
    items = await fetchItems(integrationId, sku);
  } catch (err) {
    console.warn('[jewel] complete-the-look skipped', { integrationId, sku, reason: (err as Error).name });
    return;
  }

  const nodes = items.map(renderItem).filter((n): n is HTMLElement => n !== null);
  container.classList.add('jml-ctl');
  container.replaceChildren(...nodes);
}

export function mountCompleteTheLook(
  container: HTMLElement,
  integrationId: string,
  sku: string,
): CompleteTheLookHandle {
  ensureStyles();
  void render(container, integrationId, sku);
  return {
    refresh: (nextSku: string) => render(container, integrationId, nextSku),
  };
}
