import React from 'react';
import type { GraphResultNode, NodeWithColor } from '../../types';
import { CrossButton } from '../../icons/CrossButton';
import { PlusIcon } from '../../icons/PlusIcon';
import { PropertyItem } from './PropertyItem';
import { EditablePropertyItem } from './EditablePropertyItem';
import { PropertyActions } from './PropertyActions';
import { AlertMessage, AlertType } from './AlertMessage';
import { useNodeProperties } from '../../hooks/useNodeProperties';

interface NodePropertiesPanelProps {
  selectedNode: NodeWithColor;
  onClose: () => void;
  onNodeUpdate: (updatedNode: GraphResultNode) => void;
}

export default function NodePropertiesPanel({
  selectedNode,
  onClose,
  onNodeUpdate,
}: NodePropertiesPanelProps): React.JSX.Element {
  const {
    isEditing,
    editableProperties,
    isSaving,
    error,
    successMessage,
    handleEditToggle,
    handlePropertyChange,
    handleAddProperty,
    handleDeleteProperty,
    handleUndeleteProperty,
    handleSave,
    handleCancel,
  } = useNodeProperties({ selectedNode, onNodeUpdate });

  return (
    <div className="w-72 min-h-0 mt-2 transition-all duration-300">
      <div className="h-full border border-[#e9f0f5] rounded-lg p-3 bg-white shadow-sm relative">
        <div className="flex items-center justify-between mb-3">
          <div className="text-sm font-semibold">Node Properties</div>
          <div className="flex items-center gap-2">
            {!isEditing && (
              <button
                onClick={handleEditToggle}
                className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                aria-label="Edit properties"
              >
                Edit
              </button>
            )}
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 transition-colors"
              aria-label="Close properties panel"
            >
              <CrossButton />
            </button>
          </div>
        </div>

        {error && <AlertMessage message={error} type={AlertType.ERROR} />}
        {successMessage && (
          <AlertMessage message={successMessage} type={AlertType.SUCCESS} />
        )}

        <div className="text-xs overflow-auto max-h-[70vh]">
          {!isEditing ? (
            <div className="mt-3 space-y-2">
              {Object.entries(selectedNode?.properties || {}).map(
                ([key, value]) => (
                  <PropertyItem key={key} propertyKey={key} value={value} />
                )
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {editableProperties.map((prop, index) => (
                <EditablePropertyItem
                  key={index}
                  property={prop}
                  index={index}
                  onPropertyChange={handlePropertyChange}
                  onDelete={handleDeleteProperty}
                  onUndelete={handleUndeleteProperty}
                />
              ))}

              <button
                onClick={handleAddProperty}
                className="w-full py-2 border-2 border-dashed border-slate-300 rounded text-slate-600 hover:border-blue-400 hover:text-blue-600 transition-colors flex items-center justify-center gap-1"
              >
                <PlusIcon />
                Add Property
              </button>

              <PropertyActions
                onSave={handleSave}
                onCancel={handleCancel}
                isSaving={isSaving}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
