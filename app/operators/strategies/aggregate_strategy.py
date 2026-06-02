"""Aggregate operator implementation using Strategy Pattern.

The aggregate operator groups rows by columns and computes summary values
using pluggable aggregation strategies.
"""

from __future__ import annotations

from ..base import Operator, Rows
from ...validation.rules import AggregateValidationRule
from .aggregation.factory import AggregationStrategyFactory


class AggregateOperator(Operator):
    """
    Aggregate operator: groups rows by columns and computes summary values.
    
    Config schema:
    {
        "groupBy": [str, ...],
        "aggregations": [
            {"column": str, "op": "sum"|"count"|"avg"|"min"|"max", "as": str}
        ]
    }
    
    Uses the Strategy Pattern via AggregationStrategyFactory for aggregation
    operations, allowing each operation to be independently implemented and
    easily extended.
    
    Example:
        step = {
            "type": "aggregate",
            "config": {
                "groupBy": ["country"],
                "aggregations": [
                    {"column": "amount", "op": "sum", "as": "total_amount"},
                    {"column": "id", "op": "count", "as": "events"}
                ]
            }
        }
    """

    validator = AggregateValidationRule()

    def _apply_transform(self, rows: Rows) -> Rows:
        """Apply aggregation transformation."""
        group_by = self.config["groupBy"]
        aggregations = self.config["aggregations"]
        
        # Build groups: key = tuple of groupBy values, value = list of rows
        groups = self._build_groups(rows, group_by)
        
        # Compute aggregations for each group
        aggregated_rows = []
        for key, group_rows in groups.items():
            result_row = self._create_group_result(key, group_by, group_rows, aggregations)
            aggregated_rows.append(result_row)
        
        return aggregated_rows

    @staticmethod
    def _build_groups(rows: Rows, group_by: list[str]) -> dict:
        """Group rows by the specified columns.
        
        Args:
            rows: Input rows
            group_by: List of column names to group by
            
        Returns:
            Dictionary mapping group key tuples to lists of rows
        """
        groups = {}
        for row in rows:
            key = tuple(row.get(col) for col in group_by)
            if key not in groups:
                groups[key] = []
            groups[key].append(row)
        return groups

    @staticmethod
    def _create_group_result(
        key: tuple, group_by: list[str], group_rows: Rows, aggregations: list
    ) -> dict:
        """Create a result row for a group.
        
        Args:
            key: Tuple of groupBy column values
            group_by: List of groupBy column names
            group_rows: Rows in this group
            aggregations: List of aggregation configs
            
        Returns:
            Dictionary with group columns and aggregation results
        """
        result_row = {}
        
        # Add groupBy columns to result
        for i, col in enumerate(group_by):
            result_row[col] = key[i]
        
        # Compute each aggregation using the factory
        for agg in aggregations:
            column = agg["column"]
            op = agg["op"]
            as_name = agg["as"]
            
            # Extract values for this column from all rows in the group
            values = [row.get(column) for row in group_rows]
            
            # Get the aggregation strategy using the factory
            strategy = AggregationStrategyFactory.create(op)
            result_row[as_name] = strategy.aggregate(values)
        
        return result_row
