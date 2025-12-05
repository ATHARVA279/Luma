import React from 'react';

export default function Card({ children, className = '', hover = false, ...props }) {
    return (
        <div
            className={`
        bg-zinc-900/50 backdrop-blur-sm border border-zinc-800 rounded-xl p-6
        ${hover ? 'hover:border-zinc-700 hover:bg-zinc-900 transition-all duration-300' : ''}
        ${className}
      `}
            {...props}
        >
            {children}
        </div>
    );
}
