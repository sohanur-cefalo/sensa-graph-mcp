import { useState, useEffect } from 'react';
import type { GraphResultNode, NodeWithColor } from '../types';
import { updateNodeProperties } from '../graph/graphService';
import {
  type EditableProperty,
  PropertyField,
} from '../graph/node-properties/EditablePropertyItem';

interface UseNodePropertiesProps {
  selectedNode: NodeWithColor;
  onNodeUpdate: (updatedNode: GraphResultNode) => void;
}

export function useNodeProperties({
  selectedNode,
  onNodeUpdate,
}: UseNodePropertiesProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editableProperties, setEditableProperties] = useState<
    EditableProperty[]
  >([]);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (selectedNode && isEditing) {
      const props = Object.entries(selectedNode.properties || {}).map(
        ([key, value]) => ({
          key,
          value:
            typeof value === 'object'
              ? JSON.stringify(value, null, 2)
              : String(value),
          originalKey: key,
        })
      );
      setEditableProperties(props);
    }
  }, [selectedNode, isEditing]);

  const handleEditToggle = () => {
    setIsEditing(!isEditing);
    setError(null);
    setSuccessMessage(null);
  };

  const handlePropertyChange = (
    index: number,
    field: PropertyField,
    newValue: string
  ) => {
    const updated = [...editableProperties];
    updated[index][field] = newValue;
    setEditableProperties(updated);
  };

  const handleAddProperty = () => {
    setEditableProperties([
      ...editableProperties,
      { key: '', value: '', isNew: true },
    ]);
  };

  const handleDeleteProperty = (index: number) => {
    const updated = [...editableProperties];
    if (updated[index].isNew) {
      updated.splice(index, 1);
    } else {
      updated[index].isDeleted = true;
    }
    setEditableProperties(updated);
  };

  const handleUndeleteProperty = (index: number) => {
    const updated = [...editableProperties];
    updated[index].isDeleted = false;
    setEditableProperties(updated);
  };

  const parseValue = (value: string): any => {
    try {
      return JSON.parse(value);
    } catch {
      const num = Number(value);
      if (!isNaN(num) && value.trim() !== '') {
        return num;
      }
      if (value.toLowerCase() === 'true') return true;
      if (value.toLowerCase() === 'false') return false;
      return value;
    }
  };

  const validateProperties = (): boolean => {
    const activeProps = editableProperties.filter((p) => !p.isDeleted);
    const keys = activeProps.map((p) => p.key.trim());
    const emptyKeys = keys.filter((k) => k === '');

    let validationError = '';

    if (emptyKeys.length > 0) {
      validationError = 'Property keys cannot be empty';
    }

    const duplicates = keys.filter((key, index) => keys.indexOf(key) !== index);
    if (duplicates.length > 0) {
      validationError = `Duplicate property keys: ${duplicates.join(', ')}`;
    }

    if (validationError) {
      setError(validationError);
      return false;
    }

    return true;
  };

  const buildPropertyChanges = (): {
    properties: Record<string, any>;
    deleteProperties: string[];
  } => {
    const properties: Record<string, any> = {};
    const deleteProperties: string[] = [];

    editableProperties.forEach((prop) => {
      if (prop.isDeleted && prop.originalKey) {
        deleteProperties.push(prop.originalKey);
      } else if (!prop.isDeleted) {
        properties[prop.key.trim()] = parseValue(prop.value);
      }
    });

    editableProperties.forEach((prop) => {
      if (
        prop.originalKey &&
        prop.key.trim() !== prop.originalKey &&
        !prop.isDeleted
      ) {
        deleteProperties.push(prop.originalKey);
      }
    });

    return { properties, deleteProperties };
  };

  const handleSave = async () => {
    setError(null);
    setSuccessMessage(null);

    const isValid = validateProperties();
    if (!isValid) {
      return;
    }

    try {
      setIsSaving(true);
      const { properties, deleteProperties } = buildPropertyChanges();

      const updatedNode = await updateNodeProperties(
        selectedNode.id,
        properties,
        deleteProperties
      );

      setSuccessMessage('Properties updated successfully!');
      setIsEditing(false);
      onNodeUpdate(updatedNode);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to update properties'
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError(null);
    setSuccessMessage(null);
  };

  return {
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
  };
}
