import sys
from datetime import timezone

if sys.version_info >= (3, 11):
    from datetime import UTC
else:
    UTC = timezone.utc
