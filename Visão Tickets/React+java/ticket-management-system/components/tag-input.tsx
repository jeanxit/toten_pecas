"use client"

import { X } from "lucide-react"
import { useState, useRef, useEffect } from "react"

export function TagInput({ id, placeholder, tags, setTags, suggestions }) {
  const [inputValue, setInputValue] = useState("")
  const [filteredSuggestions, setFilteredSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const inputRef = useRef(null)
  const suggestionsRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target) &&
        inputRef.current &&
        !inputRef.current.contains(event.target)
      ) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [])

  useEffect(() => {
    if (inputValue) {
      const filtered = suggestions.filter(
        (suggestion) =>
          suggestion.name.toLowerCase().includes(inputValue.toLowerCase()) ||
          suggestion.value.toLowerCase().includes(inputValue.toLowerCase()),
      )
      setFilteredSuggestions(filtered)
    } else {
      setFilteredSuggestions([])
    }
  }, [inputValue, suggestions])

  const handleInputChange = (e) => {
    setInputValue(e.target.value)
    setShowSuggestions(true)
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && inputValue) {
      e.preventDefault()
      const suggestion = filteredSuggestions[0]
      if (suggestion) {
        addTag(suggestion)
      }
    } else if (e.key === "Backspace" && !inputValue && tags.length > 0) {
      removeTag(tags.length - 1)
    }
  }

  const addTag = (suggestion) => {
    if (!tags.some((tag) => tag.value === suggestion.value)) {
      setTags([...tags, suggestion])
    }
    setInputValue("")
    setShowSuggestions(false)
  }

  const removeTag = (index) => {
    setTags(tags.filter((_, i) => i !== index))
  }

  return (
    <div className="relative">
      <div
        className="flex flex-wrap gap-2 p-2 border rounded-md focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2"
        onClick={() => inputRef.current?.focus()}
      >
        {tags.map((tag, index) => (
          <div
            key={index}
            className="flex items-center gap-1 bg-secondary text-secondary-foreground px-2 py-1 rounded-md text-sm"
          >
            <span>{tag.name}</span>
            <button
              type="button"
              onClick={() => removeTag(index)}
              className="text-secondary-foreground/70 hover:text-secondary-foreground"
            >
              <X size={14} />
            </button>
          </div>
        ))}
        <input
          ref={inputRef}
          id={id}
          type="text"
          className="flex-grow outline-none bg-transparent min-w-[120px]"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowSuggestions(true)}
          placeholder={tags.length === 0 ? placeholder : ""}
        />
      </div>

      {showSuggestions && filteredSuggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute z-10 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto"
        >
          {filteredSuggestions.map((suggestion, index) => (
            <div key={index} className="px-4 py-2 cursor-pointer hover:bg-gray-100" onClick={() => addTag(suggestion)}>
              {suggestion.name}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
