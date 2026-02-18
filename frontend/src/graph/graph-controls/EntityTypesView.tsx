import { useState, useEffect } from 'react';
import { getColorForType, initializeColorsForTypes } from '../../constants';

// Get API base URL - use relative URL for proxy (ngrok) or absolute for direct connection
const getApiBaseUrl = (): string => {
  const runtimeEnv = (import.meta as any).env;
  const apiUrl = runtimeEnv?.VITE_API_URL || runtimeEnv?.VITE_API_BASE_URL;
  if (apiUrl && !apiUrl.includes('localhost') && !apiUrl.includes('127.0.0.1')) {
    return apiUrl;
  }
  // Otherwise use relative URL (works with Vite proxy for ngrok)
  return '';
};

interface EntityTypesViewProps {
  onEntityTypeClick: (entityType: string) => void;
}

/**
 * Format entity type label for display (e.g., "BloodGroup" -> "Blood Group")
 */
function formatEntityTypeLabel(type: string): string {
  // Insert space before capital letters (except the first one)
  return type.replace(/([A-Z])/g, ' $1').trim();
}

export default function EntityTypesView({ onEntityTypeClick }: EntityTypesViewProps) {
  const [entityTypes, setEntityTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchEntityTypes() {
      try {
        setLoading(true);
        const apiBase = getApiBaseUrl();
        const response = await fetch(`${apiBase}/graph/entity-types`);
        if (!response.ok) {
          throw new Error(`Failed to fetch entity types: ${response.statusText}`);
        }
        const data = await response.json();
        const types = data.entity_types || [];
        setEntityTypes(types);
        // Initialize colors for all types
        initializeColorsForTypes(types);
        setError(null);
      } catch (err) {
        console.error('Error fetching entity types:', err);
        setError(err instanceof Error ? err.message : 'Failed to load entity types');
      } finally {
        setLoading(false);
      }
    }

    fetchEntityTypes();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-3 mb-2">
        <strong className="mr-1.5">Entity types</strong>
        <span className="text-sm text-gray-500">Loading...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-3 mb-2">
        <strong className="mr-1.5">Entity types</strong>
        <span className="text-sm text-red-500">Error: {error}</span>
      </div>
    );
  }

  if (entityTypes.length === 0) {
    return (
      <div className="flex items-center gap-3 mb-2">
        <strong className="mr-1.5">Entity types</strong>
        <span className="text-sm text-gray-500">No entity types found</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 sm:gap-3 mb-2 flex-wrap">
      <strong className="mr-1.5 text-sm sm:text-base">Entity types</strong>

      {entityTypes.map((type) => {
        const color = getColorForType(type);
        return (
          <button
            key={type}
            onClick={() => onEntityTypeClick(type)}
            className="flex items-center gap-1.5 cursor-pointer hover:opacity-70 active:opacity-50 transition-opacity focus:outline-none touch-manipulation px-1 py-0.5 sm:px-0 sm:py-0"
            type="button"
          >
            <div
              className="w-3 h-3 sm:w-3.5 sm:h-3.5 rounded-[3px] border border-[#222] shrink-0"
              style={{ background: color }}
            />
            <div className="text-sm sm:text-lg text-[#333]">{formatEntityTypeLabel(type)}</div>
          </button>
        );
      })}
    </div>
  );
}
