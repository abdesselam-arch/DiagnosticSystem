"""
Diagnostic Collection System - Search Service

This module provides services for searching and filtering diagnostic rules,
replacing the TOPSIS algorithm with simpler but effective search functionality.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set

from models.rule import Rule

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching and filtering diagnostic rules."""
    
    # Maximum number of recent searches to store
    MAX_RECENT_SEARCHES = 10
    
    def __init__(self, config, storage_service):
        """Initialize the search service with configuration.
        
        Args:
            config: Configuration object with settings.
            storage_service: Storage service for accessing rule data.
        """
        self.config = config
        self.storage_service = storage_service
        self.recent_searches = []
        self.search_counts = {}  # Track how often each search term is used
    
    def search(self, query: str, rule_type: str = None, 
              advanced_criteria: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for rules matching the query and criteria.
        
        Args:
            query (str): Search query text.
            rule_type (str, optional): Type of rule to filter by. Defaults to None.
            advanced_criteria (dict, optional): Additional search criteria. Defaults to None.
            
        Returns:
            list: List of matching rule dictionaries.
        """
        # Add to recent searches if non-empty
        if query and query.strip():
            self._add_to_recent_searches(query.strip())
        
        # Use storage service for basic search
        results = self.storage_service.search_rules(
            query, rule_type, advanced_criteria
        )
        
        # Score and rank results
        if query.strip():
            scored_results = self._score_results(results, query, advanced_criteria)
            results = [result for score, result in scored_results]
        
        return results
    
    def _score_results(self, results: List[Dict[str, Any]], query: str, 
                      advanced_criteria: Dict[str, Any] = None) -> List[Tuple[float, Dict[str, Any]]]:
        """Score and rank search results based on relevance to query.
        
        Args:
            results (list): List of rule dictionaries to score.
            query (str): The search query used.
            advanced_criteria (dict, optional): Advanced search criteria. Defaults to None.
            
        Returns:
            list: List of tuples (score, rule) sorted by descending score.
        """
        # Prepare query for scoring
        query_terms = query.lower().split()
        
        # Determine if we're doing case-sensitive searching
        case_sensitive = False
        if advanced_criteria and "match_case" in advanced_criteria:
            case_sensitive = advanced_criteria.get("match_case", False)
        
        scored_results = []
        
        for rule_data in results:
            score = 0.0
            
            # 1. Title/name matching (highest weight)
            rule_name = rule_data.get("name", "")
            if rule_name:
                name_text = rule_name if case_sensitive else rule_name.lower()
                # Exact match in name is highest score
                if query.lower() == name_text.lower():
                    score += 10.0
                # Partial match in name
                elif query.lower() in name_text.lower():
                    score += 5.0
                # Term matches in name
                else:
                    for term in query_terms:
                        if term in name_text.lower():
                            score += 1.0
            
            # 2. Rule text matching
            rule_text = rule_data.get("text", "")
            if rule_text:
                text = rule_text if case_sensitive else rule_text.lower()
                
                # Count exact occurrences of full query
                if query:
                    count = text.count(query.lower() if not case_sensitive else query)
                    score += count * 0.5
                
                # Count occurrences of individual terms
                for term in query_terms:
                    term_count = text.count(term if case_sensitive else term.lower())
                    score += term_count * 0.2
            
            # 3. Boost recently used rules
            if rule_data.get("last_used"):
                try:
                    last_used = datetime.fromisoformat(rule_data["last_used"])
                    # Rules used in the last week get a boost
                    days_ago = (datetime.now() - last_used).days
                    if days_ago < 7:
                        score += max(0, (7 - days_ago) * 0.1)
                except (ValueError, TypeError):
                    pass
            
            # 4. Boost frequently used rules
            use_count = rule_data.get("use_count", 0)
            if use_count > 0:
                # Logarithmic boost for frequently used rules
                import math
                score += math.log(1 + use_count) * 0.3
            
            # 5. Apply type-specific boosting
            if "pathway_data" in rule_data:
                # Pathways are more visual and detailed, boost when appropriate
                if advanced_criteria and advanced_criteria.get("search_fields") == "Visual Pathways":
                    score += 2.0
            elif rule_data.get("metadata", {}).get("problem_type"):
                # Captured rules have real-world context, useful for problems
                if query_terms and any(term in ["problem", "issue", "error"] for term in query_terms):
                    score += 1.0
            
            # Add scored result
            scored_results.append((score, rule_data))
        
        # Sort by score (descending)
        scored_results.sort(reverse=True, key=lambda x: x[0])
        
        return scored_results
    
    def highlight_matches(self, text: str, query: str, case_sensitive: bool = False) -> str:
        """Highlight matching terms in text.
        
        Args:
            text (str): Text to search within.
            query (str): Query to highlight.
            case_sensitive (bool, optional): Whether to use case-sensitive matching. Defaults to False.
            
        Returns:
            str: Text with HTML highlighting markup.
        """
        if not text or not query:
            return text
        
        # Prepare query terms
        query_terms = query.split()
        
        # Escape text for HTML
        escaped_text = text.replace("<", "&lt;").replace(">", "&gt;")
        
        # Create a pattern that matches any of the query terms
        pattern_parts = []
        for term in query_terms:
            # Escape special regex characters
            escaped_term = re.escape(term)
            pattern_parts.append(escaped_term)
        
        # Combine patterns with OR
        pattern = "|".join(pattern_parts)
        
        # Apply case insensitivity if needed
        flags = 0 if case_sensitive else re.IGNORECASE
        
        # Highlight matches with HTML span
        def replace_match(match):
            return f'<span class="highlight">{match.group(0)}</span>'
        
        highlighted = re.sub(pattern, replace_match, escaped_text, flags=flags)
        
        return highlighted
    
    def get_recent_searches(self) -> List[str]:
        """Get the list of recent searches.
        
        Returns:
            list: List of recent search queries, most recent first.
        """
        return self.recent_searches
    
    def _add_to_recent_searches(self, query: str) -> None:
        """Add a query to the recent searches list.
        
        Args:
            query (str): The search query to add.
        """
        # Remove if already exists (to move to top)
        if query in self.recent_searches:
            self.recent_searches.remove(query)
        
        # Add to beginning of list
        self.recent_searches.insert(0, query)
        
        # Update search count
        self.search_counts[query] = self.search_counts.get(query, 0) + 1
        
        # Trim to maximum size
        if len(self.recent_searches) > self.MAX_RECENT_SEARCHES:
            self.recent_searches = self.recent_searches[:self.MAX_RECENT_SEARCHES]
    
    def clear_recent_searches(self) -> None:
        """Clear the list of recent searches."""
        self.recent_searches = []
    
    def get_popular_searches(self, count: int = 5) -> List[Tuple[str, int]]:
        """Get the most popular search terms.
        
        Args:
            count (int, optional): Maximum number of terms to return. Defaults to 5.
            
        Returns:
            list: List of tuples (query, count) sorted by count.
        """
        # Sort by count (descending)
        popular = sorted(
            self.search_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Return top N
        return popular[:count]
    
    def get_search_suggestions(self, partial_query: str, count: int = 5) -> List[str]:
        """Get search suggestions based on a partial query.
        
        Args:
            partial_query (str): Partial query text.
            count (int, optional): Maximum number of suggestions. Defaults to 5.
            
        Returns:
            list: List of suggested search queries.
        """
        if not partial_query:
            # If no query, return popular searches
            return [query for query, _ in self.get_popular_searches(count)]
        
        # Find matching recent searches
        matches = []
        for query in self.recent_searches:
            if partial_query.lower() in query.lower():
                matches.append(query)
                if len(matches) >= count:
                    break
        
        # If we don't have enough matches, try to find prefix matches in rules
        if len(matches) < count:
            # Get all rules
            all_rules = self.storage_service.load_rules()
            
            # Extract text content for matching
            rule_texts = set()
            for rule in all_rules:
                # Add rule text
                rule_texts.add(rule.get("text", ""))
                
                # Add name if present
                if rule.get("name"):
                    rule_texts.add(rule.get("name"))
                
                # Add condition parameters
                for condition in rule.get("conditions", []):
                    param = condition.get("param", "")
                    if param:
                        rule_texts.add(param)
            
            # Find matches
            for text in rule_texts:
                words = text.lower().split()
                for word in words:
                    if word.startswith(partial_query.lower()) and len(word) > 3:
                        if word not in [m.lower() for m in matches]:
                            matches.append(word)
                            if len(matches) >= count:
                                break
                if len(matches) >= count:
                    break
        
        return matches
    
    def get_related_searches(self, query: str, count: int = 3) -> List[str]:
        """Get related searches based on a query.
        
        Args:
            query (str): The search query.
            count (int, optional): Maximum number of related searches. Defaults to 3.
            
        Returns:
            list: List of related search terms.
        """
        if not query:
            return []
        
        # Find searches that share terms with this query
        query_terms = set(query.lower().split())
        
        related = []
        for previous_query in self.recent_searches:
            if previous_query.lower() != query.lower():
                previous_terms = set(previous_query.lower().split())
                # Calculate Jaccard similarity
                intersection = len(query_terms.intersection(previous_terms))
                union = len(query_terms.union(previous_terms))
                
                if intersection > 0 and union > 0:
                    similarity = intersection / union
                    related.append((previous_query, similarity))
        
        # Sort by similarity (descending)
        related.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N
        return [query for query, _ in related[:count]]
    
    def create_search_summary(self, results: List[Dict[str, Any]], 
                             query: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of search results for display.
        
        Args:
            results (list): List of search result dictionaries.
            query (str): The search query.
            criteria (dict): The search criteria used.
            
        Returns:
            dict: Summary information about the search results.
        """
        # Count rule types
        type_counts = {
            "Pathway": 0,
            "Capture": 0, 
            "Rule": 0
        }
        
        # Count recently used rules
        recently_used = 0
        
        # Find the latest use date
        latest_use = None
        
        for rule in results:
            # Count by type
            if "pathway_data" in rule:
                type_counts["Pathway"] += 1
            elif rule.get("metadata", {}).get("problem_type"):
                type_counts["Capture"] += 1
            else:
                type_counts["Rule"] += 1
            
            # Check usage
            if rule.get("last_used"):
                try:
                    last_used = datetime.fromisoformat(rule.get("last_used"))
                    
                    # Update latest use date
                    if latest_use is None or last_used > latest_use:
                        latest_use = last_used
                    
                    # Count recently used (last 30 days)
                    if (datetime.now() - last_used).days <= 30:
                        recently_used += 1
                except (ValueError, TypeError):
                    pass
        
        return {
            "total": len(results),
            "query": query,
            "type_counts": type_counts,
            "recently_used": recently_used,
            "latest_use": latest_use.isoformat() if latest_use else None,
            "criteria": criteria
        }
    
    def get_date_range_options(self) -> Dict[str, Dict[str, str]]:
        """Get standard date range options for searches.
        
        Returns:
            dict: Dictionary of date range options.
        """
        today = datetime.now()
        
        return {
            "today": {
                "label": "Today",
                "from": today.replace(hour=0, minute=0, second=0).isoformat(),
                "to": today.replace(hour=23, minute=59, second=59).isoformat()
            },
            "yesterday": {
                "label": "Yesterday",
                "from": (today - timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat(),
                "to": (today - timedelta(days=1)).replace(hour=23, minute=59, second=59).isoformat()
            },
            "this_week": {
                "label": "This Week",
                "from": (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0).isoformat(),
                "to": today.replace(hour=23, minute=59, second=59).isoformat()
            },
            "last_week": {
                "label": "Last Week",
                "from": (today - timedelta(days=today.weekday() + 7)).replace(hour=0, minute=0, second=0).isoformat(),
                "to": (today - timedelta(days=today.weekday() + 1)).replace(hour=23, minute=59, second=59).isoformat()
            },
            "this_month": {
                "label": "This Month",
                "from": today.replace(day=1, hour=0, minute=0, second=0).isoformat(),
                "to": today.replace(hour=23, minute=59, second=59).isoformat()
            },
            "last_month": {
                "label": "Last Month",
                "from": (today.replace(day=1) - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0).isoformat(),
                "to": (today.replace(day=1) - timedelta(days=1)).replace(hour=23, minute=59, second=59).isoformat()
            },
            "last_30_days": {
                "label": "Last 30 Days",
                "from": (today - timedelta(days=30)).isoformat(),
                "to": today.isoformat()
            },
            "this_year": {
                "label": "This Year",
                "from": today.replace(month=1, day=1, hour=0, minute=0, second=0).isoformat(),
                "to": today.replace(hour=23, minute=59, second=59).isoformat()
            }
        }