// Default color palette for entity types
const COLOR_PALETTE = [
  '#FF6B6B', '#4ECDC4', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
  '#FFB347', '#87CEEB', '#DDA0DD', '#F0E68C', '#FF69B4', '#20B2AA', '#FF6347',
  '#9370DB', '#3CB371', '#FFA500', '#00CED1', '#FF1493', '#32CD32', '#1E90FF'
];

// Cache for generated colors
let TYPE_COLOR_MAP: Record<string, string> = {};

/**
 * Generate a color for an entity type based on its name hash.
 * This ensures consistent colors for the same type.
 */
function generateColorForType(type: string): string {
  if (TYPE_COLOR_MAP[type]) {
    return TYPE_COLOR_MAP[type];
  }
  
  // Simple hash function to get consistent color for same type
  let hash = 0;
  for (let i = 0; i < type.length; i++) {
    hash = type.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  const colorIndex = Math.abs(hash) % COLOR_PALETTE.length;
  const color = COLOR_PALETTE[colorIndex];
  TYPE_COLOR_MAP[type] = color;
  
  return color;
}

/**
 * Initialize colors for a list of entity types.
 * This should be called when entity types are fetched from the API.
 */
export function initializeColorsForTypes(types: string[]): void {
  types.forEach(type => {
    if (!TYPE_COLOR_MAP[type]) {
      generateColorForType(type);
    }
  });
}

export function getColorForType(type: string): string {
  return TYPE_COLOR_MAP[type] || generateColorForType(type);
}

// Export for backward compatibility
export { TYPE_COLOR_MAP };

export const CHAT_MIN_WIDTH = 220;
export const CHAT_MAX_WIDTH = 1200;
export const CHAT_DEFAULT_WIDTH = 360;

export const ZOOM_STEP = 1.25;
export const MIN_ZOOM = 0.2;
export const MAX_ZOOM = 4.0;

export const DEFAULT_FETCH_LIMIT = 50;
