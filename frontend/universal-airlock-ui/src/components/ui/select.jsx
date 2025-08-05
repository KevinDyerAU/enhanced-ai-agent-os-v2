import React, { useState, createContext, useContext } from 'react';

const SelectContext = createContext();

export const Select = ({ children, onValueChange, defaultValue, ...props }) => {
  const [value, setValue] = useState(defaultValue || '');
  const [isOpen, setIsOpen] = useState(false);
  
  const handleValueChange = (newValue) => {
    setValue(newValue);
    setIsOpen(false);
    if (onValueChange) onValueChange(newValue);
  };
  
  return (
    <SelectContext.Provider value={{ value, setValue: handleValueChange, isOpen, setIsOpen }}>
      <div className="relative" {...props}>
        {children}
      </div>
    </SelectContext.Provider>
  );
};

export const SelectTrigger = ({ children, className = "", ...props }) => {
  const { isOpen, setIsOpen } = useContext(SelectContext);
  
  return (
    <button
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      onClick={() => setIsOpen(!isOpen)}
      {...props}
    >
      {children}
      <svg className="h-4 w-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );
};

export const SelectValue = ({ placeholder = "Select...", ...props }) => {
  const { value } = useContext(SelectContext);
  
  return (
    <span {...props}>
      {value || placeholder}
    </span>
  );
};

export const SelectContent = ({ children, className = "", ...props }) => {
  const { isOpen } = useContext(SelectContext);
  
  if (!isOpen) return null;
  
  return (
    <div className={`absolute top-full left-0 z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg ${className}`} {...props}>
      {children}
    </div>
  );
};

export const SelectItem = ({ children, value, className = "", ...props }) => {
  const { setValue } = useContext(SelectContext);
  
  return (
    <div
      className={`px-3 py-2 text-sm cursor-pointer hover:bg-gray-100 ${className}`}
      onClick={() => setValue(value)}
      {...props}
    >
      {children}
    </div>
  );
};
