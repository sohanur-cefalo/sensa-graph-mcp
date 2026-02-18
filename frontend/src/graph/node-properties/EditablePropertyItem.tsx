import React from 'react';
import { RestoreIcon } from '../../icons/RestoreIcon';
import { DeleteIcon } from '../../icons/DeleteIcon';

export enum PropertyField {
  KEY = 'key',
  VALUE = 'value',
}

export type EditableProperty = {
  key: string;
  value: any;
  isNew?: boolean;
  isDeleted?: boolean;
  originalKey?: string;
};

type EditablePropertyItemProps = {
  property: EditableProperty;
  index: number;
  onPropertyChange: (
    index: number,
    field: PropertyField,
    newValue: string
  ) => void;
  onDelete: (index: number) => void;
  onUndelete: (index: number) => void;
};

export function EditablePropertyItem({
  property,
  index,
  onPropertyChange,
  onDelete,
  onUndelete,
}: EditablePropertyItemProps): React.JSX.Element {
  return (
    <div
      className={`border border-slate-200 rounded p-2 ${
        property.isDeleted ? 'bg-red-50 opacity-60' : 'bg-slate-50'
      }`}
    >
      <div className="flex items-start justify-between mb-1">
        <input
          type="text"
          value={property.key}
          onChange={(e) =>
            onPropertyChange(index, PropertyField.KEY, e.target.value)
          }
          placeholder="Property key"
          disabled={property.isDeleted}
          className="flex-1 px-2 py-1 text-xs border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-slate-100"
        />
        {property.isDeleted ? (
          <button
            onClick={() => onUndelete(index)}
            className="ml-2 text-green-600 hover:text-green-800"
            title="Restore"
          >
            <RestoreIcon />
          </button>
        ) : (
          <button
            onClick={() => onDelete(index)}
            className="ml-2 text-red-600 hover:text-red-800"
            title="Delete"
          >
            <DeleteIcon />
          </button>
        )}
      </div>
      <textarea
        value={property.value}
        onChange={(e) =>
          onPropertyChange(index, PropertyField.VALUE, e.target.value)
        }
        placeholder="Property value"
        disabled={property.isDeleted}
        rows={2}
        className="w-full px-2 py-1 text-xs border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-slate-100 font-mono"
      />
    </div>
  );
}
