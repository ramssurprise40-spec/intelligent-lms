import React, { useState, useRef, useEffect, ReactNode } from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

interface DropdownItem {
  label: string;
  href?: string;
  onClick?: () => void;
  icon?: React.ComponentType<{ className?: string }>;
  disabled?: boolean;
  divider?: boolean;
}

interface DropdownProps {
  trigger: ReactNode;
  items: DropdownItem[];
  align?: 'left' | 'right';
  className?: string;
}

export default function Dropdown({ trigger, items, align = 'right', className = '' }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleItemClick = (item: DropdownItem) => {
    if (item.disabled) return;
    
    if (item.onClick) {
      item.onClick();
    }
    setIsOpen(false);
  };

  return (
    <div className={`relative inline-block text-left ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center"
      >
        {trigger}
      </button>

      {isOpen && (
        <div
          className={`absolute z-50 mt-2 w-56 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none ${
            align === 'right' ? 'right-0' : 'left-0'
          }`}
        >
          <div className="py-1">
            {items.map((item, index) => (
              <div key={index}>
                {item.divider ? (
                  <div className="border-t border-gray-100 my-1" />
                ) : (
                  <button
                    onClick={() => handleItemClick(item)}
                    disabled={item.disabled}
                    className={`group flex w-full items-center px-4 py-2 text-sm text-left transition-colors ${
                      item.disabled
                        ? 'text-gray-400 cursor-not-allowed'
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    {item.icon && (
                      <item.icon className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                    )}
                    {item.label}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
