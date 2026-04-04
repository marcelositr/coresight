"""
i18n loader for CoreSight.
Detects locale and loads the correct labels.
"""

import locale
from . import en_US, pt_BR

def get_labels():
    """
    Detects the system locale and returns the corresponding labels.
    """
    try:
        current_locale, _ = locale.getdefaultlocale()
        if current_locale and current_locale.startswith('pt'):
            return pt_BR.LABELS
        else:
            return en_US.LABELS
    except Exception:
        # Default to English if anything fails
        return en_US.LABELS

# Expose labels for other modules
labels = get_labels()
