import React from 'react';

export enum AlertType {
  ERROR = 'error',
  SUCCESS = 'success',
}

type AlertMessageProps = {
  message: string;
  type: AlertType;
};

export function AlertMessage({
  message,
  type,
}: AlertMessageProps): React.JSX.Element {
  const isError = type === 'error';

  return (
    <div
      className={`mb-3 p-2 rounded text-xs ${
        isError
          ? 'bg-red-50 border border-red-200 text-red-700'
          : 'bg-green-50 border border-green-200 text-green-700'
      }`}
    >
      {message}
    </div>
  );
}
