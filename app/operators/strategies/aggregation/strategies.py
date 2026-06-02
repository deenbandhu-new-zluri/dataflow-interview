"""Concrete implementations of aggregation strategies."""

from __future__ import annotations

from typing import Any

from .base import AggregationStrategy


class SumAggregation(AggregationStrategy):
    """Sum aggregation: adds up all non-null values.
    
    Example:
        values = [10, 20, 30, None]
        strategy = SumAggregation()
        result = strategy.aggregate(values)  # 60
    """

    def aggregate(self, values: list[Any]) -> Any:
        """Sum all non-null values."""
        return sum(v for v in values if v is not None)


class CountAggregation(AggregationStrategy):
    """Count aggregation: counts total rows in group.
    
    Note: Counts all rows, including those with null values.
    
    Example:
        values = [1, 2, None, 4]
        strategy = CountAggregation()
        result = strategy.aggregate(values)  # 4
    """

    def aggregate(self, values: list[Any]) -> int:
        """Count all rows."""
        return len(values)


class AverageAggregation(AggregationStrategy):
    """Average aggregation: computes mean of non-null values.
    
    Returns 0 if all values are null.
    
    Example:
        values = [10, 20, 30, None]
        strategy = AverageAggregation()
        result = strategy.aggregate(values)  # 20
    """

    def aggregate(self, values: list[Any]) -> Any:
        """Compute average of non-null values."""
        non_null = [v for v in values if v is not None]
        return sum(non_null) / len(non_null) if non_null else 0


class MinAggregation(AggregationStrategy):
    """Min aggregation: finds minimum non-null value.
    
    Returns None if all values are null.
    
    Example:
        values = [10, 5, 20, None]
        strategy = MinAggregation()
        result = strategy.aggregate(values)  # 5
    """

    def aggregate(self, values: list[Any]) -> Any:
        """Find minimum non-null value."""
        non_null = [v for v in values if v is not None]
        return min(non_null) if non_null else None


class MaxAggregation(AggregationStrategy):
    """Max aggregation: finds maximum non-null value.
    
    Returns None if all values are null.
    
    Example:
        values = [10, 5, 20, None]
        strategy = MaxAggregation()
        result = strategy.aggregate(values)  # 20
    """

    def aggregate(self, values: list[Any]) -> Any:
        """Find maximum non-null value."""
        non_null = [v for v in values if v is not None]
        return max(non_null) if non_null else None
