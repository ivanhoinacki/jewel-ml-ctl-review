export function getShopperId(): string {
  return document.cookie.match(/jml_sid=([^;]+)/)?.[1] ?? '';
}

export function getShopperEmail(): string | undefined {
  return (window as any).__jml_email;
}
