from pybloom_live import BloomFilter
from typing import Optional

class OptimizedBloomFilter:
    def __init__(self, expected_items: int, false_positive_rate: float):
        """
        Initialize a Bloom filter with specified capacity and error rate.

        Args:
            expected_items (int): Expected number of items to store.
            false_positive_rate (float): Desired false positive probability (0.0 to 1.0).

        Raises:
            ValueError: If expected_items is non-positive or false_positive_rate is invalid.
        """
        if expected_items <= 0:
            raise ValueError("expected_items must be positive")
        if not 0.0 < false_positive_rate < 1.0:
            raise ValueError("false_positive_rate must be between 0.0 and 1.0")
        self.filter = BloomFilter(expected_items, false_positive_rate)

    def insert(self, item: str) -> None:
        """
        Add an item to the Bloom filter.

        Args:
            item (str): Item to add.

        Raises:
            ValueError: If item is empty or not a string.
        """
        if not isinstance(item, str) or not item:
            raise ValueError("Item must be a non-empty string")
        self.filter.add(item)

    def contains(self, item: str) -> bool:
        """
        Check if an item is likely in the Bloom filter.

        Args:
            item (str): Item to check.

        Returns:
            bool: True if the item is likely present, False otherwise.

        Raises:
            ValueError: If item is empty or not a string.
        """
        if not isinstance(item, str) or not item:
            raise ValueError("Item must be a non-empty string")
        return item in self.filter

    def reset(self) -> None:
        """
        Clear the Bloom filter by recreating it with the same parameters.
        """
        try:
            self.filter = BloomFilter(self.filter.capacity, self.filter.error_rate())
        except Exception as e:
            raise RuntimeError(f"Failed to reset Bloom filter: {str(e)}")

    def estimated_false_positive_rate(self) -> float:
        """
        Estimate the current false positive rate.

        Returns:
            float: Configured false positive rate.
        """
        return self.filter.error_rate()

    def memory_size_bytes(self) -> int:
        """
        Estimate memory usage of the Bloom filter in bytes.

        Returns:
            int: Approximate memory usage in bytes.
        """
        try:
            # pybloom-live uses a bit array; estimate size based on bit count
            return self.filter.bit_array.bit_length() // 8
        except AttributeError:
            # Fallback if bit_array is not accessible
            return int(self.filter.capacity * 1.44 / 8)  # Approximate based on Bloom filter theory

    @classmethod
    def adaptive(cls, network_size: int) -> 'OptimizedBloomFilter':
        """
        Create a Bloom filter optimized for the given network size.

        Args:
            network_size (int): Estimated number of peers in the network.

        Returns:
            OptimizedBloomFilter: A new Bloom filter instance.

        Raises:
            ValueError: If network_size is negative.
        """
        if network_size < 0:
            raise ValueError("network_size must be non-negative")
        expected_items = max(100, network_size * 10)  # Heuristic: 10 items per peer
        false_positive_rate = 0.01  # Fixed rate for balanced performance
        return cls(expected_items, false_positive_rate)