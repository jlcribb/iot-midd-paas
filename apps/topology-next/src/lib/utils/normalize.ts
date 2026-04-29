export function normalizeMacAddress(macAddress: string | null | undefined): string | null {
  if (!macAddress) {
    return null;
  }
  const normalized = macAddress.trim().toLowerCase();
  return normalized.length > 0 ? normalized : null;
}
