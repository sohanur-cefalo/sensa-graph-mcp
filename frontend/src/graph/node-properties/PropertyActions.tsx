import React from 'react';

type PropertyActionsProps = {
  onSave: () => void;
  onCancel: () => void;
  isSaving: boolean;
};

export function PropertyActions({
  onSave,
  onCancel,
  isSaving,
}: PropertyActionsProps): React.JSX.Element {
  return (
    <div className="flex gap-2 pt-2">
      <button
        onClick={onSave}
        disabled={isSaving}
        className="flex-1 px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-slate-400 transition-colors text-xs font-medium"
      >
        {isSaving ? 'Saving...' : 'Save'}
      </button>
      <button
        onClick={onCancel}
        disabled={isSaving}
        className="flex-1 px-3 py-2 bg-slate-200 text-slate-700 rounded hover:bg-slate-300 disabled:bg-slate-100 transition-colors text-xs font-medium"
      >
        Cancel
      </button>
    </div>
  );
}
