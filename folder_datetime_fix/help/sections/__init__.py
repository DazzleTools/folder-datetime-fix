"""
Central registry of all help sections.

Each section defines its own content items locally, and this module
collects them all for easy access.
"""

# Import all sections
from .basic import basic_section, BASIC_ITEMS
from .strategy import strategy_section, STRATEGY_ITEMS
from .advanced import advanced_section, ADVANCED_ITEMS
from .network import network_section, NETWORK_ITEMS
from .detailed_help import detailed_help_section, DETAILED_HELP_ITEMS

# Collect all sections in order of priority
ALL_SECTIONS = {
    'basic': basic_section,
    'strategy': strategy_section,
    'advanced': advanced_section,
    'network': network_section,
    'detailed_help': detailed_help_section,
}

# Collect all content items from all sections
ALL_ITEMS = {}
ALL_ITEMS.update(BASIC_ITEMS)
ALL_ITEMS.update(STRATEGY_ITEMS)
ALL_ITEMS.update(ADVANCED_ITEMS)
ALL_ITEMS.update(NETWORK_ITEMS)
ALL_ITEMS.update(DETAILED_HELP_ITEMS)

# Export convenience functions
def get_section(name: str):
    """Get a specific section by name."""
    return ALL_SECTIONS.get(name)

def get_item(item_id: str):
    """Get a specific content item by ID."""
    return ALL_ITEMS.get(item_id)

def get_items_for_context(context: str):
    """Get all items that should appear in a given context."""
    items = []
    for item in ALL_ITEMS.values():
        if context in item.contexts:
            items.append(item)
    # Sort by priority (lower number = higher priority)
    return sorted(items, key=lambda x: (x.priority, x.id))