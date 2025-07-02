def validate_region(val):
    """Ensure region is not empty."""
    return len(val.strip()) > 0 or "Region cannot be empty."

def validate_tags(val):
    """Ensure tags are in key=value format."""
    try:
        tags = [tag.strip() for tag in val.split(",") if tag.strip()]
        return all("=" in tag and len(tag.split("=")) == 2 for tag in tags) or "Tags must be in key=value format"
    except Exception:
        return "Tags must be in key=value format"

def validate_resources(answer):
    """Ensure at least one resource is selected."""
    return len(answer) > 0 or "You must choose at least one resource."
