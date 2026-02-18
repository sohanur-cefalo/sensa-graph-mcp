import { useState, useEffect, useRef } from 'react';
import { searchEmployees, type Employee } from './employeeService';

type ChatInputProps = {
    input: string;
    isLoading: boolean;
    setInput: (v: string) => void;
    sendMessage: () => void;
    handleEnter: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  };

type SuggestionItem = {
  type: 'employee';
  data: Employee;
};
  
  export function ChatInput({
    input,
    isLoading,
    setInput,
    sendMessage,
    handleEnter,
  }: ChatInputProps) {
    const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [mentionStart, setMentionStart] = useState<number | null>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const suggestionsRef = useRef<HTMLDivElement>(null);

    // Debounce search for employee mentions
    useEffect(() => {
      const timer = setTimeout(() => {
        const cursorPos = textareaRef.current?.selectionStart || 0;
        const textBeforeCursor = input.substring(0, cursorPos);
        const mentionMatch = textBeforeCursor.match(/@([^\s@]*)$/);

        if (mentionMatch) {
          // Handle @ mention for employees
          const searchQuery = mentionMatch[1];
          const startPos = cursorPos - mentionMatch[0].length;
          
          setMentionStart(startPos);
          
          if (searchQuery.length > 0) {
            searchEmployees(searchQuery, 10).then((results) => {
              setSuggestions(results.map(emp => ({ type: 'employee' as const, data: emp })));
              setShowSuggestions(results.length > 0);
              setSelectedIndex(0);
            });
          } else {
            setSuggestions([]);
            setShowSuggestions(false);
          }
        } else {
          // Hide suggestions when not typing @ mention
          setMentionStart(null);
          setSuggestions([]);
          setShowSuggestions(false);
        }
      }, 300);

      return () => clearTimeout(timer);
    }, [input]);

    const insertSuggestion = (item: SuggestionItem) => {
      if (!textareaRef.current) return;

      // Handle employee mention
      if (mentionStart === null) return;
      
      const displayName = item.data.slackDisplayName || item.data.name;
      const beforeMention = input.substring(0, mentionStart);
      const afterMention = input.substring(textareaRef.current.selectionStart);
      const newInput = `${beforeMention}@${displayName} ${afterMention}`;

      setInput(newInput);
      setShowSuggestions(false);
      setSuggestions([]);
      setMentionStart(null);

      // Set cursor position after the inserted mention
      setTimeout(() => {
        const newCursorPos = mentionStart + displayName.length + 2; // +2 for "@" and space
        textareaRef.current?.setSelectionRange(newCursorPos, newCursorPos);
        textareaRef.current?.focus();
      }, 0);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (showSuggestions && suggestions.length > 0) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          setSelectedIndex((prev) => 
            prev < suggestions.length - 1 ? prev + 1 : prev
          );
          return;
        }
        if (e.key === 'ArrowUp') {
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          return;
        }
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          insertSuggestion(suggestions[selectedIndex]);
          return;
        }
        if (e.key === 'Escape') {
          e.preventDefault();
          setShowSuggestions(false);
          return;
        }
        if (e.key === 'Tab') {
          e.preventDefault();
          insertSuggestion(suggestions[selectedIndex]);
          return;
        }
      }

      // Call original handleEnter for non-suggestion cases
      if (!showSuggestions) {
        handleEnter(e);
      }
    };

    // Scroll selected suggestion into view
    useEffect(() => {
      if (showSuggestions && suggestionsRef.current) {
        const selectedElement = suggestionsRef.current.children[selectedIndex] as HTMLElement;
        if (selectedElement) {
          selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
      }
    }, [selectedIndex, showSuggestions]);

    return (
      <div className="px-2 sm:px-3 py-2 sm:py-3 border-t border-[#eef4f8] bg-white relative">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              className="flex-1 w-full p-2.5 sm:p-2 rounded-md border border-[#e6edf2] text-base sm:text-sm resize-none min-h-[44px] sm:h-12 focus:ring-[#cfe4ff] focus:outline-none"
              value={input}
              placeholder="Type your message…"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
            />
            
            {showSuggestions && suggestions.length > 0 && (
              <div
                ref={suggestionsRef}
                className="absolute bottom-full left-0 right-0 mb-1 bg-white border border-[#e6edf2] rounded-md shadow-lg max-h-60 overflow-y-auto z-10"
              >
                <div className="px-2 py-1 text-xs text-gray-500 border-b border-[#e6edf8] bg-gray-50">
                  Employees
                </div>
                {suggestions.map((item, index) => {
                  const isSelected = index === selectedIndex;
                  
                  return (
                    <div
                      key={item.data.userId}
                      className={`px-3 py-2.5 sm:py-2 cursor-pointer text-base sm:text-sm touch-manipulation ${
                        isSelected
                          ? 'bg-[#0f62ff] text-white'
                          : 'hover:bg-[#f3f7fb] active:bg-[#f3f7fb] text-[#0f1723]'
                      }`}
                      onClick={() => insertSuggestion(item)}
                      onMouseEnter={() => setSelectedIndex(index)}
                      onTouchStart={() => setSelectedIndex(index)}
                    >
                      <div className="font-medium">{item.data.name}</div>
                      {item.data.designation && (
                        <div className={`text-xs sm:text-xs ${isSelected ? 'text-blue-100' : 'text-gray-500'}`}>
                          {item.data.designation}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
  
          <button
            className="px-4 py-2.5 sm:px-3 sm:py-2 rounded-md bg-[#0f62ff] text-white text-base sm:text-sm font-medium disabled:opacity-50 touch-manipulation min-h-[44px] sm:min-h-0 active:bg-[#0a4fcc] transition-colors"
            disabled={isLoading || !input.trim()}
            onClick={sendMessage}
          >
            Send
          </button>
        </div>
      </div>
    );
  }
  