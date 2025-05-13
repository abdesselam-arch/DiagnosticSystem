"""
Diagnostic Collection System - Analytics Service

This module provides services for analyzing diagnostic rules and extracting insights
from the collected data, helping users understand patterns and effectiveness.
"""

import os
import json
import logging
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analyzing diagnostic rule collection data."""
    
    def __init__(self, config, storage_service):
        """Initialize the analytics service with configuration.
        
        Args:
            config: Configuration object with data paths and settings.
            storage_service: Storage service for accessing rule data.
        """
        self.config = config
        self.storage_service = storage_service
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize the analytics service, ensuring analytics directories exist."""
        try:
            # Ensure analytics directories exist
            analytics_dir = os.path.join(self.config.DATA_DIR, "analytics")
            os.makedirs(analytics_dir, exist_ok=True)
            os.makedirs(os.path.join(analytics_dir, "reports"), exist_ok=True)
            os.makedirs(os.path.join(analytics_dir, "usage"), exist_ok=True)
            os.makedirs(os.path.join(analytics_dir, "trends"), exist_ok=True)
            
            logger.info("Analytics service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing analytics service: {str(e)}")
    
    def get_collection_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the rule collection.
        
        Returns:
            dict: Statistics about the rule collection.
        """
        try:
            # Get basic statistics from storage service
            base_stats = self.storage_service.get_statistics()
            
            # Enhance with additional analytics
            enhanced_stats = self._enhance_collection_statistics(base_stats)
            
            return enhanced_stats
        except Exception as e:
            logger.error(f"Error getting collection statistics: {str(e)}")
            return {"error": str(e)}
    
    def _enhance_collection_statistics(self, base_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance basic collection statistics with deeper analytics.
        
        Args:
            base_stats (dict): Basic statistics from storage service.
            
        Returns:
            dict: Enhanced statistics with additional analytics.
        """
        # Load all rules for analysis
        rules = self.storage_service.load_rules()
        
        # Initialize enhanced stats with base stats
        stats = base_stats.copy()
        
        # Add effectiveness analysis (if available)
        effectiveness_counts = Counter()
        for rule in rules:
            if "metadata" in rule and "effectiveness" in rule["metadata"]:
                effectiveness_counts[rule["metadata"]["effectiveness"]] += 1
        
        if effectiveness_counts:
            stats["effectiveness"] = dict(effectiveness_counts)
        
        # Add complexity analysis
        stats["complexity"] = {
            "conditions_per_rule": self._calculate_average_conditions(rules),
            "actions_per_rule": self._calculate_average_actions(rules),
            "complex_rule_count": sum(1 for rule in rules if rule.get("is_complex", False))
        }
        
        # Add time-based analysis
        today = datetime.now()
        stats["time_analysis"] = {
            "created_last_30_days": sum(1 for rule in rules if self._is_within_days(rule.get("created_date"), 30)),
            "created_last_90_days": sum(1 for rule in rules if self._is_within_days(rule.get("created_date"), 90)),
            "used_last_30_days": sum(1 for rule in rules if self._is_within_days(rule.get("last_used"), 30)),
            "used_last_90_days": sum(1 for rule in rules if self._is_within_days(rule.get("last_used"), 90)),
            "never_used_percentage": self._calculate_never_used_percentage(rules)
        }
        
        # Count connection patterns in pathways
        stats["pathway_analysis"] = self._analyze_pathways(rules)
        
        return stats
    
    def _calculate_average_conditions(self, rules: List[Dict[str, Any]]) -> float:
        """Calculate the average number of conditions per rule.
        
        Args:
            rules (list): List of rule dictionaries.
            
        Returns:
            float: Average number of conditions per rule.
        """
        total_conditions = sum(len(rule.get("conditions", [])) for rule in rules)
        if not rules:
            return 0.0
        return total_conditions / len(rules)
    
    def _calculate_average_actions(self, rules: List[Dict[str, Any]]) -> float:
        """Calculate the average number of actions per rule.
        
        Args:
            rules (list): List of rule dictionaries.
            
        Returns:
            float: Average number of actions per rule.
        """
        total_actions = sum(len(rule.get("actions", [])) for rule in rules)
        if not rules:
            return 0.0
        return total_actions / len(rules)
    
    def _is_within_days(self, date_str: Optional[str], days: int) -> bool:
        """Check if a date is within the specified number of days from now.
        
        Args:
            date_str (str): Date string in ISO format.
            days (int): Number of days.
            
        Returns:
            bool: True if the date is within the specified days, False otherwise.
        """
        if not date_str:
            return False
            
        try:
            date = datetime.fromisoformat(date_str)
            return (datetime.now() - date).days <= days
        except (ValueError, TypeError):
            return False
    
    def _calculate_never_used_percentage(self, rules: List[Dict[str, Any]]) -> float:
        """Calculate the percentage of rules that have never been used.
        
        Args:
            rules (list): List of rule dictionaries.
            
        Returns:
            float: Percentage of rules never used.
        """
        if not rules:
            return 0.0
            
        never_used = sum(1 for rule in rules if not rule.get("last_used"))
        return (never_used / len(rules)) * 100
    
    def _analyze_pathways(self, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze pathway patterns in rules.
        
        Args:
            rules (list): List of rule dictionaries.
            
        Returns:
            dict: Analysis of pathway patterns.
        """
        # Get only rules with pathway data
        pathway_rules = [rule for rule in rules if rule.get("pathway_data")]
        
        if not pathway_rules:
            return {"pathway_count": 0}
            
        # Analyze node and connection patterns
        node_counts = []
        connection_counts = []
        node_types = Counter()
        
        for rule in pathway_rules:
            pathway_data = rule.get("pathway_data", {})
            nodes = pathway_data.get("nodes", {})
            connections = pathway_data.get("connections", [])
            
            # Count nodes and connections
            node_counts.append(len(nodes))
            connection_counts.append(len(connections))
            
            # Count node types
            for node_id, node in nodes.items():
                node_types[node.get("node_type", "unknown")] += 1
        
        # Calculate averages
        avg_nodes = sum(node_counts) / len(node_counts) if node_counts else 0
        avg_connections = sum(connection_counts) / len(connection_counts) if connection_counts else 0
        
        return {
            "pathway_count": len(pathway_rules),
            "avg_nodes_per_pathway": avg_nodes,
            "avg_connections_per_pathway": avg_connections,
            "node_type_distribution": dict(node_types)
        }
    
    def generate_usage_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate a report on rule usage over a specified time period.
        
        Args:
            days (int, optional): Number of days to include in the report. Defaults to 30.
            
        Returns:
            dict: Usage report data.
        """
        try:
            # Get interaction log
            log_entries = self._load_interaction_log()
            
            # Filter to specified time period
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_logs = [
                entry for entry in log_entries 
                if self._parse_timestamp(entry.get("timestamp")) >= cutoff_date
            ]
            
            # Analyze usage
            rule_usage = Counter()
            daily_usage = defaultdict(int)
            problem_types = Counter()
            
            for entry in recent_logs:
                # Count rule usage
                for action in entry.get("actions", []):
                    rule_usage[action] += 1
                
                # Track daily usage
                timestamp = self._parse_timestamp(entry.get("timestamp"))
                if timestamp:
                    date_str = timestamp.strftime("%Y-%m-%d")
                    daily_usage[date_str] += 1
                
                # Analyze problem descriptions
                problem_desc = entry.get("problem_description", "").lower()
                if problem_desc:
                    # Extract problem types based on keywords
                    if "error" in problem_desc or "fail" in problem_desc:
                        problem_types["Error/Failure"] += 1
                    elif "quality" in problem_desc:
                        problem_types["Quality Issue"] += 1
                    elif "setup" in problem_desc or "configuration" in problem_desc:
                        problem_types["Setup/Configuration"] += 1
                    elif "material" in problem_desc or "supply" in problem_desc:
                        problem_types["Material/Supply"] += 1
                    else:
                        problem_types["Other"] += 1
            
            # Build report
            report = {
                "period": f"Last {days} days",
                "total_interactions": len(recent_logs),
                "unique_rules_used": len(rule_usage),
                "most_used_rules": dict(rule_usage.most_common(5)),
                "daily_usage": dict(sorted(daily_usage.items())),
                "problem_type_distribution": dict(problem_types)
            }
            
            # Calculate average daily usage
            if daily_usage:
                report["avg_daily_usage"] = sum(daily_usage.values()) / len(daily_usage)
            else:
                report["avg_daily_usage"] = 0
            
            # Save report
            self._save_usage_report(report)
            
            return report
        except Exception as e:
            logger.error(f"Error generating usage report: {str(e)}")
            return {"error": str(e)}
    
    def _load_interaction_log(self) -> List[Dict[str, Any]]:
        """Load the interaction log.
        
        Returns:
            list: List of interaction log entries.
        """
        log_file = self.config.INTERACTION_LOG
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading interaction log: {str(e)}")
        
        return []
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse a timestamp string to datetime.
        
        Args:
            timestamp_str (str): Timestamp string in ISO format.
            
        Returns:
            datetime: Parsed datetime, or None if parsing failed.
        """
        if not timestamp_str:
            return None
            
        try:
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            return None
    
    def _save_usage_report(self, report: Dict[str, Any]) -> None:
        """Save a usage report to file.
        
        Args:
            report (dict): Usage report data.
        """
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"usage_report_{timestamp}.json"
            report_path = os.path.join(
                self.config.DATA_DIR, 
                "analytics", 
                "reports", 
                filename
            )
            
            # Save report
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Saved usage report to {report_path}")
        except Exception as e:
            logger.error(f"Error saving usage report: {str(e)}")
    
    def analyze_effectiveness(self) -> Dict[str, Any]:
        """Analyze the effectiveness of rules based on metadata.
        
        Returns:
            dict: Effectiveness analysis results.
        """
        try:
            # Load all rules
            rules = self.storage_service.load_rules()
            
            # Filter to rules with effectiveness data
            rules_with_effectiveness = [
                rule for rule in rules 
                if rule.get("metadata", {}).get("effectiveness")
            ]
            
            if not rules_with_effectiveness:
                return {"status": "no_data", "message": "No effectiveness data available"}
            
            # Count effectiveness ratings
            effectiveness_counts = Counter()
            effectiveness_by_type = defaultdict(Counter)
            
            for rule in rules_with_effectiveness:
                effectiveness = rule.get("metadata", {}).get("effectiveness")
                effectiveness_counts[effectiveness] += 1
                
                # Group by rule type
                rule_type = "Rule"
                if "pathway_data" in rule:
                    rule_type = "Pathway"
                elif rule.get("metadata", {}).get("problem_type"):
                    rule_type = "Capture"
                
                effectiveness_by_type[rule_type][effectiveness] += 1
            
            # Calculate percentages
            total = len(rules_with_effectiveness)
            effectiveness_percentages = {
                rating: (count / total) * 100
                for rating, count in effectiveness_counts.items()
            }
            
            # Analyze patterns
            complete_solutions = [
                rule for rule in rules_with_effectiveness
                if rule.get("metadata", {}).get("effectiveness") == "Complete Solution"
            ]
            
            # Look for patterns in complete solutions
            patterns = self._analyze_solution_patterns(complete_solutions)
            
            return {
                "total_rules_with_effectiveness": total,
                "effectiveness_counts": dict(effectiveness_counts),
                "effectiveness_percentages": effectiveness_percentages,
                "effectiveness_by_type": {k: dict(v) for k, v in effectiveness_by_type.items()},
                "patterns": patterns
            }
        except Exception as e:
            logger.error(f"Error analyzing effectiveness: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_solution_patterns(self, complete_solutions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in effective solutions.
        
        Args:
            complete_solutions (list): List of rules rated as complete solutions.
            
        Returns:
            dict: Analysis of patterns in effective solutions.
        """
        if not complete_solutions:
            return {}
            
        # Analyze action types
        action_types = Counter()
        condition_terms = Counter()
        
        for rule in complete_solutions:
            # Count action types
            for action in rule.get("actions", []):
                action_type = action.get("type", "Unknown")
                action_types[action_type] += 1
            
            # Extract common terms from conditions
            for condition in rule.get("conditions", []):
                param = condition.get("param", "").lower()
                for term in param.split():
                    if len(term) > 3:  # Ignore short terms
                        condition_terms[term] += 1
        
        return {
            "common_action_types": dict(action_types.most_common(5)),
            "common_condition_terms": dict(condition_terms.most_common(10))
        }
    
    def generate_trend_report(self, interval: str = "monthly") -> Dict[str, Any]:
        """Generate a trend report showing changes over time.
        
        Args:
            interval (str, optional): Time interval for aggregation ('daily', 'weekly', 'monthly').
                                     Defaults to "monthly".
        
        Returns:
            dict: Trend report data.
        """
        try:
            # Load all rules
            rules = self.storage_service.load_rules()
            
            # Load interaction log
            log_entries = self._load_interaction_log()
            
            # Prepare timeline data
            timeline = self._prepare_timeline(rules, log_entries, interval)
            
            # Calculate growth rates
            growth_rates = self._calculate_growth_rates(timeline)
            
            # Identify trends
            trends = self._identify_trends(timeline, growth_rates)
            
            report = {
                "interval": interval,
                "timeline": timeline,
                "growth_rates": growth_rates,
                "trends": trends
            }
            
            # Save report
            self._save_trend_report(report)
            
            return report
        except Exception as e:
            logger.error(f"Error generating trend report: {str(e)}")
            return {"error": str(e)}
    
    def _prepare_timeline(self, rules: List[Dict[str, Any]], 
                         log_entries: List[Dict[str, Any]], 
                         interval: str) -> Dict[str, Dict[str, int]]:
        """Prepare timeline data for trend analysis.
        
        Args:
            rules (list): List of rule dictionaries.
            log_entries (list): List of interaction log entries.
            interval (str): Time interval for aggregation.
            
        Returns:
            dict: Timeline data aggregated by interval.
        """
        # Determine date format based on interval
        if interval == "daily":
            date_format = "%Y-%m-%d"
            days_in_period = 1
        elif interval == "weekly":
            date_format = "%Y-W%W"  # ISO week
            days_in_period = 7
        else:  # monthly
            date_format = "%Y-%m"
            days_in_period = 30
        
        # Initialize timeline
        timeline = {
            "rule_creation": defaultdict(int),
            "rule_usage": defaultdict(int),
            "problem_reports": defaultdict(int)
        }
        
        # Process rule creation dates
        for rule in rules:
            created_date = self._parse_timestamp(rule.get("created_date"))
            if created_date:
                period = created_date.strftime(date_format)
                timeline["rule_creation"][period] += 1
        
        # Process rule usage and problem reports from log
        for entry in log_entries:
            timestamp = self._parse_timestamp(entry.get("timestamp"))
            if timestamp:
                period = timestamp.strftime(date_format)
                
                # Count interactions as problem reports
                timeline["problem_reports"][period] += 1
                
                # Count rule applications
                timeline["rule_usage"][period] += len(entry.get("actions", []))
        
        # Sort and fill in missing periods
        start_date = self._find_earliest_date(rules, log_entries)
        if start_date:
            end_date = datetime.now()
            
            current_date = start_date
            while current_date <= end_date:
                period = current_date.strftime(date_format)
                
                # Ensure period exists in all series
                for series in timeline.values():
                    if period not in series:
                        series[period] = 0
                
                # Move to next period
                if interval == "daily":
                    current_date += timedelta(days=1)
                elif interval == "weekly":
                    current_date += timedelta(days=7)
                else:  # monthly
                    # Simple approximation for monthly increment
                    month = current_date.month + 1
                    year = current_date.year
                    if month > 12:
                        month = 1
                        year += 1
                    current_date = current_date.replace(year=year, month=month, day=1)
        
        # Convert defaultdicts to regular dicts with sorted keys
        return {
            k: dict(sorted(v.items())) for k, v in timeline.items()
        }
    
    def _find_earliest_date(self, rules: List[Dict[str, Any]], 
                           log_entries: List[Dict[str, Any]]) -> Optional[datetime]:
        """Find the earliest date in rules and log entries.
        
        Args:
            rules (list): List of rule dictionaries.
            log_entries (list): List of interaction log entries.
            
        Returns:
            datetime: Earliest date found, or None if no dates available.
        """
        dates = []
        
        # Check rule creation dates
        for rule in rules:
            created_date = self._parse_timestamp(rule.get("created_date"))
            if created_date:
                dates.append(created_date)
        
        # Check log entry timestamps
        for entry in log_entries:
            timestamp = self._parse_timestamp(entry.get("timestamp"))
            if timestamp:
                dates.append(timestamp)
        
        if dates:
            return min(dates)
        return None
    
    def _calculate_growth_rates(self, timeline: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, float]]:
        """Calculate growth rates between intervals.
        
        Args:
            timeline (dict): Timeline data.
            
        Returns:
            dict: Growth rates between intervals.
        """
        growth_rates = {}
        
        for series_name, data in timeline.items():
            growth_rates[series_name] = {}
            
            # Convert to list for easier processing
            periods = list(data.keys())
            values = list(data.values())
            
            # Calculate growth rates
            for i in range(1, len(periods)):
                current = values[i]
                previous = values[i-1]
                
                if previous > 0:
                    growth = ((current - previous) / previous) * 100
                else:
                    growth = float('inf') if current > 0 else 0
                
                growth_rates[series_name][periods[i]] = growth
        
        return growth_rates
    
    def _identify_trends(self, timeline: Dict[str, Dict[str, int]], 
                        growth_rates: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Identify trends in the timeline data.
        
        Args:
            timeline (dict): Timeline data.
            growth_rates (dict): Growth rates between intervals.
            
        Returns:
            dict: Identified trends.
        """
        trends = {}
        
        for series_name, data in timeline.items():
            # Get periods and values
            periods = list(data.keys())
            values = list(data.values())
            
            if len(values) < 3:
                # Not enough data for trend analysis
                trends[series_name] = {
                    "trend": "insufficient_data",
                    "message": "Not enough data points for trend analysis"
                }
                continue
            
            # Calculate simple linear regression
            n = len(values)
            x = list(range(n))
            sum_x = sum(x)
            sum_y = sum(values)
            sum_xy = sum(xi * yi for xi, yi in zip(x, values))
            sum_xx = sum(xi**2 for xi in x)
            
            # Calculate slope
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
            
            # Determine trend direction
            if slope > 0.1:
                trend = "increasing"
            elif slope < -0.1:
                trend = "decreasing"
            else:
                trend = "stable"
            
            # Check for acceleration/deceleration
            growth_values = list(growth_rates[series_name].values())
            if len(growth_values) >= 3:
                # Compare recent growth rates to earlier ones
                recent_growth = sum(growth_values[-3:]) / 3
                earlier_growth = sum(growth_values[:-3]) / max(1, len(growth_values) - 3)
                
                if recent_growth > earlier_growth * 1.2:
                    trend_change = "accelerating"
                elif recent_growth < earlier_growth * 0.8:
                    trend_change = "decelerating"
                else:
                    trend_change = "consistent"
            else:
                trend_change = "unknown"
            
            trends[series_name] = {
                "trend": trend,
                "slope": slope,
                "trend_change": trend_change,
                "latest_value": values[-1] if values else 0,
                "max_value": max(values) if values else 0,
                "avg_value": sum(values) / len(values) if values else 0
            }
        
        return trends
    
    def _save_trend_report(self, report: Dict[str, Any]) -> None:
        """Save a trend report to file.
        
        Args:
            report (dict): Trend report data.
        """
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trend_report_{timestamp}.json"
            report_path = os.path.join(
                self.config.DATA_DIR, 
                "analytics", 
                "trends", 
                filename
            )
            
            # Save report
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Saved trend report to {report_path}")
        except Exception as e:
            logger.error(f"Error saving trend report: {str(e)}")
    
    def export_analytics_to_csv(self, report_type: str, file_path: Optional[str] = None) -> Tuple[bool, str]:
        """Export analytics data to a CSV file.
        
        Args:
            report_type (str): Type of report to export ('usage', 'effectiveness', 'trends', 'stats').
            file_path (str, optional): Path to save the CSV file. Defaults to auto-generated.
            
        Returns:
            tuple: (Success flag, file path or error message)
        """
        try:
            # Get appropriate report data
            if report_type == "usage":
                report_data = self.generate_usage_report()
            elif report_type == "effectiveness":
                report_data = self.analyze_effectiveness()
            elif report_type == "trends":
                report_data = self.generate_trend_report()
            elif report_type == "stats":
                report_data = self.get_collection_statistics()
            else:
                return False, f"Unknown report type: {report_type}"
            
            # Check for errors
            if "error" in report_data:
                return False, f"Error generating report: {report_data['error']}"
            
            # Generate file path if not provided
            if not file_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(
                    self.config.DATA_DIR, 
                    "analytics", 
                    "reports", 
                    f"{report_type}_report_{timestamp}.csv"
                )
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Flatten and export data
            success = self._export_dict_to_csv(report_data, file_path)
            
            if success:
                logger.info(f"Exported {report_type} report to {file_path}")
                return True, file_path
            else:
                return False, "Failed to write CSV file"
        except Exception as e:
            error_msg = f"Error exporting analytics to CSV: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _export_dict_to_csv(self, data: Dict[str, Any], file_path: str) -> bool:
        """Export a nested dictionary to CSV.
        
        Args:
            data (dict): Dictionary to export.
            file_path (str): Path to save the CSV file.
            
        Returns:
            bool: True if export was successful, False otherwise.
        """
        try:
            # Flatten the nested dictionary
            flat_data = self._flatten_dict(data)
            
            # Write to CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["Key", "Value"])
                
                # Write data
                for key, value in flat_data.items():
                    writer.writerow([key, value])
            
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten a nested dictionary.
        
        Args:
            d (dict): Dictionary to flatten.
            parent_key (str, optional): Parent key prefix. Defaults to ''.
            sep (str, optional): Separator between keys. Defaults to '.'.
            
        Returns:
            dict: Flattened dictionary.
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                # Handle lists by serializing them
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
                
        return dict(items)