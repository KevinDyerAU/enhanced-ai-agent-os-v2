import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

export default function Dropzone({ onFiles }) {
  const onDrop = useCallback((acceptedFiles) => {
    onFiles(acceptedFiles);
  }, [onFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  return (
    <div
      {...getRootProps()}
      className={`flex flex-col items-center justify-center border-2 border-dashed rounded p-6 cursor-pointer transition-colors ${
        isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
      }`}
    >
      <input {...getInputProps()} />
      <p className="text-gray-600">
        {isDragActive ? 'Drop files here...' : 'Drag and drop files here, or click to select'}
      </p>
    </div>
  );
}
