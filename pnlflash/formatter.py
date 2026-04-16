def format_number(value, scale="auto"):
    # Format financial numbers with scale: 'raw', 'K', 'mm', 'auto'
    # Negatives shown in parentheses
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        return value
    if not isinstance(value, (int, float)):
        return str(value)
    is_negative = value < 0
    abs_val = abs(value)
    if scale == "mm":
        formatted = f"{abs_val / 1000000:,.0f}mm"
    elif scale == "K":
        formatted = f"{abs_val / 1000:,.0f}K"
    elif scale == "auto":
        if abs_val >= 1000000:
            formatted = f"{abs_val / 1000000:,.0f}mm"
        elif abs_val >= 1000:
            formatted = f"{abs_val / 1000:,.0f}K"
        else:
            formatted = f"{abs_val:,.0f}"
    else:
        # raw
        formatted = f"{abs_val:,.0f}"
    if is_negative:
        return f"({formatted})"
    return formatted


def is_negative_display(text):
    # Check if a formatted string represents a negative value (wrapped in parens)
    if isinstance(text, str):
        return text.startswith("(") and text.endswith(")")
    if isinstance(text, (int, float)):
        return text < 0
    return False
