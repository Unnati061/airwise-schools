export function className(id: string) { return id.replace(/^(\d+)-([a-z])$/i, (_, year, letter) => `Class ${year}${letter.toUpperCase()}`); }
export function roomName(id: string | null | undefined) {
  if (!id) return 'No room';
  const names: Record<string, string> = { field: 'Sports field', 'field-annex': 'Annex field', 'movement-hall': 'Movement hall', 'movement-studio': 'Movement studio', 'reserve-studio': 'Reserve studio' };
  return names[id] || (id.startsWith('room-') ? `${className(id.slice(5))} classroom` : id.replaceAll('-', ' '));
}
export function activityName(label: string) { return label.replace(/^Synthetic\s+/i, '').replace('Approved classroom movement', 'Indoor movement'); }
export function activityRef(id: string) { const [section, period] = id.split(':'); return `${className(section)}${period ? ` · ${period.replace('Mon-', 'Period ')}` : ''}`; }
