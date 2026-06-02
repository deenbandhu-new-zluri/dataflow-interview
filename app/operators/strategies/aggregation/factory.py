"""Factory for creating aggregation strategy instances.

Implements the Factory Pattern for aggregation operations,
centralizing strategy creation and management.
"""

from __future__ import annotations

from ...errors import ValidationError
from .base import AggregationStrategy
from .strategies import (
    AverageAggregation,
    CountAggregation,
    MaxAggregation,
    MinAggregation,
    SumAggregation,
)


class AggregationStrategyFactory:
    """Factory for creating and managing aggregation strategy instances.
    
    Implements the Factory Pattern, providing a centralized way to:
    - Create aggregation strategies by operation name
    - List supported operations
    - Register custom strategies
    
    Example:
        strategy = AggregationStrategyFactory.create("sum")
        result = strategy.aggregate([10, 20, 30])
    """

    # Registry of built-in strategies
    _strategies = {
        "sum": SumAggregation(),
        "count": CountAggregation(),
        "avg": AverageAggregation(),
        "min": MinAggregation(),
        "max": MaxAggregation(),
    }

    @classmethod
    def create(cls, op_name: str) -> AggregationStrategy:
        """
        Create an aggregation strategy by operation name.
        
        Args:
            op_name: Name of the aggregation operation (e.g., "sum", "count")
            
        Returns:
            AggregationStrategy instance
            
        Raises:
            ValidationError: If operation is unknown
            
        Example:
            strategy = AggregationStrategyFactory.create("sum")
        """
        if op_name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValidationError(
                f'Unknown aggregation operation: "{op_name}". '
                f'Available: {available}'
            )
        return cls._strategies[op_name]

    @classmethod
    def get_supported_operations(cls) -> list[str]:
        """
        Get list of supported aggregation operations.
        
        Returns:
            List of operation names
            
        Example:
            ops = AggregationStrategyFactory.get_supported_operations()
            # ['sum', 'count', 'avg', 'min', 'max']
        """
        return list(cls._strategies.keys())

    @classmethod
    def register(cls, op_name: str, strategy: AggregationStrategy) -> None:
        """
        Register a custom aggregation strategy.
        
        Allows extending the framework with custom aggregation operations
        without modifying existing code.
        
        Args:
            op_name: Name of the aggregation operation
            strategy: Instance of AggregationStrategy
            
        Raises:
            ValidationError: If operation name is already registered
            
        Example:
            class MedianAggregation(AggregationStrategy):
                def aggregate(self, values):
                    non_null = sorted([v for v in values if v is not None])
                    if not non_null:
                        return None
                    mid = len(non_null) // 2
                    return non_null[mid]
            
            AggregationStrategyFactory.register("median", MedianAggregation())
        """
        if op_name in cls._strategies:
            raise ValidationError(
                f'Aggregation operation "{op_name}" is already registered'
            )
        cls._strategies[op_name] = strategy

    @classmethod
    def replace(cls, op_name: str, strategy: AggregationStrategy) -> None:
        """
        Replace an existing aggregation strategy.
        
        Allows overriding built-in or previously registered strategies.
        
        Args:
            op_name: Name of the aggregation operation
            strategy: Instance of AggregationStrategy
            
        Raises:
            ValidationError: If operation is not registered
        """
        if op_name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValidationError(
                f'Cannot replace unknown aggregation operation: "{op_name}". '
                f'Available: {available}'
            )
        cls._strategies[op_name] = strategy

    @classmethod
    def unregister(cls, op_name: str) -> None:
        """
        Unregister an aggregation strategy.
        
        Note: Be careful unregistering built-in operations.
        
        Args:
            op_name: Name of the aggregation operation
            
        Raises:
            ValidationError: If operation is not registered
        """
        if op_name not in cls._strategies:
            raise ValidationError(f'Aggregation operation "{op_name}" is not registered')
        del cls._strategies[op_name]
