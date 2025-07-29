def wrap_text(text, max_width, font):
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        text_width = font.size(test_line)[0]
        
        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Single word is too long, just add it anyway
                lines.append(word)
                current_line = ""
    
    if current_line:
        lines.append(current_line)
    
    return lines