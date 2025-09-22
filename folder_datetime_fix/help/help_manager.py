"""
Central help system manager that orchestrates all help output.
"""

import random
from typing import Optional, List, Dict
from pathlib import Path


class HelpManager:
    """Manages the modular help system."""
    
    def __init__(self, prog: str = 'fdtfix.py'):
        """
        Initialize the help manager.
        
        Args:
            prog: Program name for examples
        """
        self.prog = prog
        self.sections = {}
        self.topics = {}
        self._load_sections()
        self._load_topics()
        self._load_tips()
    
    def _load_sections(self):
        """Load all help sections."""
        # Import sections dynamically
        from .sections import basic, strategy, advanced, network, tips
        
        self.sections = {
            'basic': basic,
            'strategy': strategy,
            'advanced': advanced,
            'network': network,
            'tips': tips
        }
    
    def _load_topics(self):
        """Load all help topics."""
        # Import topics dynamically
        from .topics import strategy, analyze, program, layers, patterns
        
        self.topics = {
            'strategy': strategy,
            'analyze': analyze,
            'fdtfix': program,
            'program': program,  # Alias
            'layers': layers,
            'patterns': patterns,
            'exclude': patterns,  # Alias
            'include': patterns,  # Alias
        }
    
    def _load_tips(self):
        """Load random tips pool from all sections dynamically."""
        self.tips_pool = []
        
        # Gather tips from all sections
        for name, module in self.sections.items():
            if hasattr(module, 'get_tips'):
                section_tips = module.get_tips()
                if section_tips:
                    self.tips_pool.extend(section_tips)
        
        # Also load from dedicated tips module for additional tips
        from .sections.tips import TIPS_POOL
        self.tips_pool.extend(TIPS_POOL)
    
    def get_minimal_help(self) -> str:
        """
        Get ultra-concise help for when no arguments provided.
        Target: 10-15 lines maximum.
        """
        return f"""{self.prog} - Fix folder timestamps to match their content

Usage: {self.prog} [path] [options]

Common Commands:
  {self.prog} .                    # Fix current directory
  {self.prog} . -f2                # Fix current + immediate children
  {self.prog} . -fa --dry-run      # Preview all changes (safe)

Options:
  --depth N        Process specific depth(s)
  --strategy MODE  How to scan (shallow/deep/smart)
  --dry-run        Preview without changes
  
For more examples: {self.prog} --help
For specific topics: {self.prog} --help <topic>
Available topics: strategy, analyze, patterns, layers, fdtfix"""
    
    def get_standard_help(self) -> str:
        """
        Get standard help output for --help flag.
        Shows selected sections to keep it reasonable.
        """
        sections = []
        displayed_sections = []
        
        # Get condensed versions of key sections
        if 'basic' in self.sections:
            content = self.sections['basic'].get_short(self.prog)
            sections.append(content)
            displayed_sections.append('basic')
        
        if 'strategy' in self.sections:
            content = self.sections['strategy'].get_short(self.prog)
            sections.append(content)
            displayed_sections.append('strategy')
        
        if 'advanced' in self.sections:
            content = self.sections['advanced'].get_short(self.prog)
            sections.append(content)
            displayed_sections.append('advanced')
        
        # Add footer
        sections.append(self._get_footer())
        
        # Build complete displayed content for duplicate detection
        displayed_content = '\n\n'.join(sections)
        
        # Add a random tip from sections not displayed
        # This ensures users get hints about features they haven't seen
        # and avoids duplicating visible content
        tip = self.get_random_tip(
            exclude_sections=displayed_sections,
            displayed_content=displayed_content
        )
        if tip:
            sections.append(tip)
        
        return '\n\n'.join(sections)
    
    def get_full_help(self) -> str:
        """
        Get complete help with all sections.
        Used for --help all or similar.
        """
        sections = []
        
        # Get full versions of all sections
        for name in ['basic', 'strategy', 'advanced', 'network']:
            if name in self.sections:
                sections.append(self.sections[name].get_full(self.prog))
        
        # Add footer
        sections.append(self._get_footer())
        
        return '\n\n'.join(sections)
    
    def get_topic_help(self, topic: str) -> Optional[str]:
        """
        Get detailed help for a specific topic.
        
        Args:
            topic: Topic name (e.g., 'strategy', 'analyze', 'patterns')
            
        Returns:
            Help text or None if topic not found
        """
        topic = topic.lower()
        
        if topic in self.topics:
            return self.topics[topic].get_help()
        
        # Try to find similar topics
        similar = self._find_similar_topics(topic)
        if similar:
            return f"Topic '{topic}' not found. Did you mean: {', '.join(similar)}?"
        
        return f"Topic '{topic}' not found. Available topics: {', '.join(sorted(self.topics.keys()))}"
    
    def get_random_tip(self, exclude_sections: List[str] = None, displayed_content: str = "") -> str:
        """
        Get a random helpful tip, avoiding duplication of displayed content.
        
        Args:
            exclude_sections: Sections already shown (to avoid their tips)
            displayed_content: Text already shown to check for duplicates
            
        Returns:
            Formatted tip string
        """
        if not self.tips_pool:
            return ""
        
        # Build pool of candidate tips
        candidate_tips = []
        
        if exclude_sections:
            # Only get tips from non-displayed sections
            for name, module in self.sections.items():
                if name not in exclude_sections and hasattr(module, 'get_tips'):
                    tips = module.get_tips()
                    if tips:
                        candidate_tips.extend(tips)
        else:
            # Use all tips
            candidate_tips = self.tips_pool.copy()
        
        # Filter out tips that would duplicate displayed content
        if displayed_content:
            filtered_tips = []
            for tip in candidate_tips:
                # Check if key parts of the tip are already visible
                # Look for the main command or concept in the tip
                tip_keywords = self._extract_tip_keywords(tip)
                if not self._is_duplicate_content(tip_keywords, displayed_content):
                    filtered_tips.append(tip)
            candidate_tips = filtered_tips
        
        # Select a random tip from candidates
        if candidate_tips:
            tip = random.choice(candidate_tips)
            # Optionally indicate section for tips from hidden sections
            if exclude_sections:
                section_name = self._find_tip_section(tip)
                if section_name and section_name not in ['tips'] and section_name not in exclude_sections:
                    return f"💡 TIP ({section_name}): {tip}"
            return f"💡 TIP: {tip}"
        
        # No suitable tips found
        return ""
    
    def _extract_tip_keywords(self, tip: str) -> List[str]:
        """Extract key commands/options from a tip for duplicate detection."""
        keywords = []
        # Look for command-line options (--something or -x)
        import re
        options = re.findall(r'--?\w+[-\w]*', tip)
        keywords.extend(options)
        # Look for specific values like 'shallow', 'deep', etc.
        for term in ['shallow', 'deep', 'smart', 'folder-only', 'tree', 'dry-run']:
            if term in tip.lower():
                keywords.append(term)
        return keywords
    
    def _is_duplicate_content(self, keywords: List[str], displayed_content: str) -> bool:
        """Check if keywords are already in displayed content."""
        if not keywords:
            return False
        displayed_lower = displayed_content.lower()
        # If most keywords are already visible, consider it duplicate
        matches = sum(1 for kw in keywords if kw.lower() in displayed_lower)
        return matches >= len(keywords) * 0.7  # 70% threshold
    
    def _find_tip_section(self, tip: str) -> Optional[str]:
        """Find which section a tip belongs to."""
        for name, module in self.sections.items():
            if hasattr(module, 'get_tips'):
                tips = module.get_tips()
                if tips and tip in tips:
                    if hasattr(module, 'get_title'):
                        return module.get_title()
                    return name
        return None
    
    def _get_footer(self) -> str:
        """Get the standard help footer."""
        return f"""For detailed explanations and more examples:
  {self.prog} --help strategy     # How scan strategies work
  {self.prog} --help analyze      # How analysis strategies work  
  {self.prog} --help patterns     # Exclude/include patterns guide
  {self.prog} --help layers       # How options layer together
  {self.prog} --help fdtfix       # Complete program manual
  
See also: docs/Recipes-and-Examples.md and docs/Performance-Optimization.md"""
    
    def _find_similar_topics(self, topic: str) -> List[str]:
        """Find topics with similar names."""
        similar = []
        for known_topic in self.topics.keys():
            if topic in known_topic or known_topic in topic:
                similar.append(known_topic)
        return similar
    
    def list_topics(self) -> List[str]:
        """Get list of available help topics."""
        return sorted(set(self.topics.keys()))
    
    def has_topic(self, topic: str) -> bool:
        """Check if a help topic exists."""
        return topic.lower() in self.topics