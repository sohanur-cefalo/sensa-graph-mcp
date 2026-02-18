import React from 'react';

type PropertyItemProps = {
  propertyKey: string;
  value: any;
};

export function PropertyItem({
  propertyKey,
  value,
}: PropertyItemProps): React.JSX.Element {
  return (
    <div className="border-b border-[#e9f0f5] pb-2 last:border-b-0">
      <div className="font-medium text-slate-700">{propertyKey}:</div>
      <div className="text-slate-600 wrap-break-word">
        {typeof value === 'object'
          ? JSON.stringify(value, null, 2)
          : String(value)}
      </div>
    </div>
  );
}
