"""Base class for aggregation strategies.

Implements the Strategy Pattern, allowing each aggregation operation
to be independently implemented and extended.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AggregationStrategy(ABC):
    """Base class for aggregation operations.
    
    Implements the Strategy Pattern, allowing each aggregation operation
    to be independently implemented and extended.
    
    Example:
        class MedianAggregation(AggregationStrategy):
            def aggregate(self, values):
                # Compute median
                pass
    """

    @abstractmethod
    def aggregate(self, values: list[Any]) -> Any:
        """
        Compute the aggregation over a list of values.
        
        Args:
            values: List of values from a column for a group
            
        Returns:
            Aggregated result
        """
        pass
