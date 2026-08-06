import re
line = "1. Kaiming He, Deep Residual Learning..."
numbered_pattern = re.compile(r"^\d+\.(?!\s*\**\s*(?:Title|Authors?|Venue|Conference|Year|DOI|Abstract|Summary|Key Contribution|Link|Publication)\b)\s*", re.IGNORECASE)
print(numbered_pattern.match(line))
