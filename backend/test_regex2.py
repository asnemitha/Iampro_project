import re
line = "**Authors:** Kaiming He"
pat = re.compile(r"\**\s*(?:Title|Authors?|Venue|Conference|Year|DOI|Abstract|Summary|Key Contribution|Link|Publication)\b", re.IGNORECASE)
print(pat.match(line))
