"""Aggregation operations module."""

from .base import AggregationStrategy
from .strategies import (
    SumAggregation,
    CountAggregation,
    AverageAggregation,
    MinAggregation,
    MaxAggregation,
)
from .factory import AggregationStrategyFactory

__all__ = [
    "AggregationStrategy",
    "SumAggregation",
    "CountAggregation",
    "AverageAggregation",
    "MinAggregation",
    "MaxAggregation",
    "AggregationStrategyFactory",
]
