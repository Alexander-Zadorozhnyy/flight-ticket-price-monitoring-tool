from collections import defaultdict
import re
from typing import Any, Dict, List, Optional
from dataclasses import asdict, dataclass
from enum import Enum


class QualityMetric(Enum):
    """Quality metrics for flight data."""

    VALID = "valid"
    INVALID = "invalid"
    PARTIAL = "partial"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


class Quality(Enum):
    """Overall quality classification for whole batch."""

    VERY_POOR = "very_poor"
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class FlightQuality:
    """Data quality metrics for a single flight."""

    is_valid: bool = False
    completeness_score: float = 0.0  # 0.0 to 1.0
    missing_fields: Optional[List[str]] = None
    invalid_fields: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    quality_category: QualityMetric = QualityMetric.INVALID

    def __post_init__(self):
        if self.missing_fields is None:
            self.missing_fields = []
        if self.invalid_fields is None:
            self.invalid_fields = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class BatchQuality:
    """Aggregated quality metrics for a batch of flights."""

    total_flights: int = 0
    valid_flights: int = 0
    invalid_flights: int = 0
    partial_flights: int = 0
    completeness_scores: Optional[List[float]] = None
    missing_fields_summary: Optional[Dict[str, int]] = None
    invalid_fields_summary: Optional[Dict[str, int]] = None
    warnings_summary: Optional[Dict[str, int]] = None
    overall_completeness: float = 0.0
    overall_quality: Quality = Quality.POOR

    def __post_init__(self):
        if self.completeness_scores is None:
            self.completeness_scores = []
        if self.missing_fields_summary is None:
            self.missing_fields_summary = {}
        if self.invalid_fields_summary is None:
            self.invalid_fields_summary = {}
        if self.warnings_summary is None:
            self.warnings_summary = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert BatchQuality to dictionary."""
        result = asdict(self)
        result["overall_quality"] = self.overall_quality.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchQuality":
        """Create BatchQuality from dictionary."""
        if "overall_quality" in data and isinstance(data["overall_quality"], str):
            data["overall_quality"] = Quality(data["overall_quality"])
        return cls(**data)


class QualityCalculator:
    def __init__(self):
        self.required_fields = [
            "airline",
            "departure_time",
            "departure_airport",
            "arrival_airport",
            "duration",
            "price",
        ]

        self.important_fields = [
            "arrival_time",
            "stop_type",
            "baggage_included",
            "seats_left",
        ]

        self.optional_fields = []

    def create_invalid_quality(self, error: str):
        return FlightQuality(
            is_valid=False,
            completeness_score=0.0,
            quality_category=QualityMetric.INVALID,
            warnings=[f"Transformation error: {error}"],
        )

    def calculate_flight_quality(
        self, flight_dict: Dict[str, Any], structured_output: Optional[Dict[str, Any]]
    ) -> FlightQuality:
        """
        Calculate data quality metrics for a single flight.

        Args:
            flight_dict: Raw flight data
            structured_output: Structured output (None if transformation failed)

        Returns:
            FlightQuality object with quality metrics
        """
        quality = FlightQuality()

        # Check if transformation was successful
        if structured_output is None:
            quality.is_valid = False
            quality.quality_category = QualityMetric.INVALID
            quality.warnings.append("Transformation failed")
            return quality

        # Check field completeness
        present_fields = []
        missing_fields = []

        # Check required fields
        for field in self.required_fields:
            if field in flight_dict and flight_dict[field]:
                present_fields.append(field)
            else:
                missing_fields.append(field)

        # Check important fields
        important_missing = []
        for field in self.important_fields:
            if field in flight_dict and flight_dict[field] not in [None, ""]:
                present_fields.append(field)
            else:
                important_missing.append(field)

        # Calculate completeness score
        total_checked = len(self.required_fields) + len(self.important_fields)
        present_count = len(present_fields)
        completeness = present_count / total_checked if total_checked > 0 else 0.0
        quality.completeness_score = round(completeness, 2)

        # Check data validity
        invalid_fields = []
        warnings = []

        # Validate specific fields
        if "price" in flight_dict:
            price_str = flight_dict["price"]
            if not self._is_valid_price(price_str):
                invalid_fields.append("price")
                warnings.append(f"Invalid price format: {price_str}")

        if "duration" in flight_dict:
            duration_str = flight_dict["duration"]
            if not self._is_valid_duration(duration_str):
                invalid_fields.append("duration")
                warnings.append(f"Invalid duration format: {duration_str}")

        if "departure_time" in flight_dict:
            time_str = flight_dict["departure_time"]
            if not self._is_valid_time(time_str):
                invalid_fields.append("departure_time")
                warnings.append(f"Invalid time format: {time_str}")

        if "airline" in flight_dict and flight_dict["airline"]:
            airline_str = flight_dict["airline"]
            if len(airline_str) < 2:
                warnings.append(f"Very short airline name: {airline_str}")

        # Set quality metrics
        quality.missing_fields = missing_fields
        quality.invalid_fields = invalid_fields
        quality.warnings = warnings

        # Determine quality category
        if len(missing_fields) == 0 and len(invalid_fields) == 0:
            quality.is_valid = True
            quality.quality_category = QualityMetric.COMPLETE
        elif len(missing_fields) > 0 and completeness >= 0.7:
            quality.is_valid = True
            quality.quality_category = QualityMetric.PARTIAL
        elif completeness >= 0.5:
            quality.is_valid = True
            quality.quality_category = QualityMetric.PARTIAL
        else:
            quality.is_valid = False
            quality.quality_category = QualityMetric.INCOMPLETE

        return quality

    def calculate_batch_quality(
        self, flight_qualities: List[FlightQuality]
    ) -> BatchQuality:
        """
        Calculate aggregated quality metrics for a batch of flights.

        Args:
            flight_qualities: List of FlightQuality objects

        Returns:
            BatchQuality object with aggregated metrics
        """
        batch = BatchQuality(total_flights=len(flight_qualities))

        if not flight_qualities:
            return batch

        # Initialize summary dictionaries
        missing_summary = {}
        invalid_summary = {}
        warnings_summary = {}

        for quality in flight_qualities:
            # Count by quality category
            if quality.quality_category == QualityMetric.COMPLETE:
                batch.valid_flights += 1
            elif quality.quality_category == QualityMetric.PARTIAL:
                batch.partial_flights += 1
                batch.valid_flights += 1
            else:
                batch.invalid_flights += 1

            # Collect completeness scores
            batch.completeness_scores.append(quality.completeness_score)

            # Aggregate missing fields
            for field in quality.missing_fields:
                missing_summary[field] = missing_summary.get(field, 0) + 1

            # Aggregate invalid fields
            for field in quality.invalid_fields:
                invalid_summary[field] = invalid_summary.get(field, 0) + 1

            # Aggregate warnings
            for warning in quality.warnings:
                warnings_summary[warning] = warnings_summary.get(warning, 0) + 1

        # Calculate overall metrics
        batch.missing_fields_summary = dict(
            sorted(missing_summary.items(), key=lambda x: x[1], reverse=True)
        )

        batch.invalid_fields_summary = dict(
            sorted(invalid_summary.items(), key=lambda x: x[1], reverse=True)
        )

        batch.warnings_summary = dict(
            sorted(warnings_summary.items(), key=lambda x: x[1], reverse=True)
        )

        # Calculate overall completeness
        if batch.completeness_scores:
            batch.overall_completeness = round(
                sum(batch.completeness_scores) / len(batch.completeness_scores), 2
            )

        # Determine overall quality
        valid_ratio = batch.valid_flights / batch.total_flights
        if valid_ratio >= 0.9 and batch.overall_completeness >= 0.9:
            batch.overall_quality = Quality.EXCELLENT
        elif valid_ratio >= 0.8 and batch.overall_completeness >= 0.8:
            batch.overall_quality = Quality.GOOD
        elif valid_ratio >= 0.6 and batch.overall_completeness >= 0.6:
            batch.overall_quality = Quality.FAIR
        elif valid_ratio >= 0.4:
            batch.overall_quality = Quality.POOR
        else:
            batch.overall_quality = Quality.VERY_POOR

        return batch

    def merge_batch_qualities(
        self, batch_qualities: List[BatchQuality]
    ) -> Dict[str, Any]:
        """
        Merge multiple BatchQuality responses into a single mean response.

        Args:
            batch_qualities: List of BatchQuality objects to merge

        Returns:
            Dictionary with merged statistics and metrics
        """
        if not batch_qualities:
            return {
                "total_routes": 0,
                "merged_quality": {
                    "total_flights": 0,
                    "valid_flights": 0,
                    "invalid_flights": 0,
                    "partial_flights": 0,
                    "overall_completeness": 0.0,
                    "overall_quality": Quality.POOR.value,
                    "route_statistics": {
                        "avg_flights_per_route": 0,
                        "min_flights_per_route": 0,
                        "max_flights_per_route": 0,
                        "std_flights_per_route": 0,
                    },
                },
            }

        # Initialize aggregated counters
        total_batches = len(batch_qualities)

        # Aggregate basic statistics
        total_flights = sum(bq.total_flights for bq in batch_qualities)
        valid_flights = sum(bq.valid_flights for bq in batch_qualities)
        invalid_flights = sum(bq.invalid_flights for bq in batch_qualities)
        partial_flights = sum(bq.partial_flights for bq in batch_qualities)

        # Aggregate field summaries
        missing_fields_agg = defaultdict(int)
        invalid_fields_agg = defaultdict(int)
        warnings_agg = defaultdict(int)

        for bq in batch_qualities:
            for field, count in bq.missing_fields_summary.items():
                missing_fields_agg[field] += count
            for field, count in bq.invalid_fields_summary.items():
                invalid_fields_agg[field] += count
            for warning, count in bq.warnings_summary.items():
                warnings_agg[warning] += count

        # Sort aggregated summaries by frequency
        missing_fields_summary = dict(
            sorted(missing_fields_agg.items(), key=lambda x: x[1], reverse=True)
        )

        invalid_fields_summary = dict(
            sorted(invalid_fields_agg.items(), key=lambda x: x[1], reverse=True)
        )

        warnings_summary = dict(
            sorted(warnings_agg.items(), key=lambda x: x[1], reverse=True)
        )

        # Calculate batch statistics
        flights_per_batch = [bq.total_flights for bq in batch_qualities]
        avg_flights_per_batch = (
            sum(flights_per_batch) / total_batches if total_batches > 0 else 0
        )
        min_flights_per_batch = min(flights_per_batch) if flights_per_batch else 0
        max_flights_per_batch = max(flights_per_batch) if flights_per_batch else 0

        # Calculate standard deviation for flights per batch
        if len(flights_per_batch) > 1:
            mean_flights = avg_flights_per_batch
            variance = sum((x - mean_flights) ** 2 for x in flights_per_batch) / (
                len(flights_per_batch) - 1
            )
            std_flights_per_batch = variance**0.5
        else:
            std_flights_per_batch = 0

        # Calculate overall completeness (weighted average by number of flights)
        total_completeness = sum(
            bq.overall_completeness * bq.total_flights for bq in batch_qualities
        )
        overall_completeness = (
            total_completeness / total_flights if total_flights > 0 else 0.0
        )

        # Calculate quality ratios
        valid_ratio = valid_flights / total_flights if total_flights > 0 else 0
        complete_ratio = overall_completeness

        # Determine overall quality based on ratios
        if valid_ratio >= 0.9 and complete_ratio >= 0.9:
            overall_quality = Quality.EXCELLENT
        elif valid_ratio >= 0.8 and complete_ratio >= 0.8:
            overall_quality = Quality.GOOD
        elif valid_ratio >= 0.6 and complete_ratio >= 0.6:
            overall_quality = Quality.FAIR
        elif valid_ratio >= 0.4:
            overall_quality = Quality.POOR
        else:
            overall_quality = Quality.VERY_POOR

        # Prepare the merged result
        merged_quality = BatchQuality(
            total_flights=total_flights,
            valid_flights=valid_flights,
            invalid_flights=invalid_flights,
            partial_flights=partial_flights,
            missing_fields_summary=missing_fields_summary,
            invalid_fields_summary=invalid_fields_summary,
            warnings_summary=warnings_summary,
            overall_completeness=round(overall_completeness, 4),
            overall_quality=overall_quality,
        )

        # Calculate per-batch statistics
        completeness_scores = [bq.overall_completeness for bq in batch_qualities]
        avg_completeness = (
            sum(completeness_scores) / total_batches if total_batches > 0 else 0
        )

        # Determine most common quality
        quality_counts = defaultdict(int)
        for bq in batch_qualities:
            quality_counts[bq.overall_quality] += 1
        most_common_quality = (
            max(quality_counts.items(), key=lambda x: x[1])[0]
            if quality_counts
            else Quality.POOR
        )

        result = {
            "total_routes": total_batches,
            "total_flights_processed": total_flights,
            "merged_quality": merged_quality.to_dict(),
            "route_statistics": {
                "avg_flights_per_route": round(avg_flights_per_batch, 2),
                "min_flights_per_route": min_flights_per_batch,
                "max_flights_per_route": max_flights_per_batch,
                "std_flights_per_route": round(std_flights_per_batch, 2),
                "avg_completeness_per_route": round(avg_completeness, 4),
                "min_completeness_per_route": min(completeness_scores)
                if completeness_scores
                else 0,
                "max_completeness_per_route": max(completeness_scores)
                if completeness_scores
                else 0,
                "route_quality_distribution": {
                    quality.value: count for quality, count in quality_counts.items()
                },
                "most_common_quality": most_common_quality.value,
            },
            "quality_ratios": {
                "valid_flights_ratio": round(valid_ratio, 4),
                "partial_flights_ratio": round(partial_flights / total_flights, 4)
                if total_flights > 0
                else 0,
                "invalid_flights_ratio": round(invalid_flights / total_flights, 4)
                if total_flights > 0
                else 0,
                "completeness_ratio": round(overall_completeness, 4),
            },
            "field_issues": {
                "total_missing_field_occurrences": sum(missing_fields_summary.values()),
                "total_invalid_field_occurrences": sum(invalid_fields_summary.values()),
                "total_warnings": sum(warnings_summary.values()),
                "top_missing_fields": dict(
                    list(missing_fields_summary.items())[:10]
                ),  # Top 10
                "top_invalid_fields": dict(
                    list(invalid_fields_summary.items())[:10]
                ),  # Top 10
                "top_warnings": dict(list(warnings_summary.items())[:10]),  # Top 10
            },
        }

        return result

    # Helper methods for validation
    def _is_valid_price(self, price_str: str) -> bool:
        """Validate price string format with more flexible patterns."""
        if not price_str:
            return False

        # Convert to string and clean
        price_str = str(price_str).strip()
        if not price_str:
            return False

        # Check if it contains any numbers
        has_numbers = any(char.isdigit() for char in price_str)
        if not has_numbers:
            return False

        # More flexible currency detection
        currency_patterns = [
            r"[A-Z]{3}",  # Three-letter currency codes (USD, EUR, RUB)
            r"[₽€$£¥]",  # Currency symbols
            r"руб",
            r"р\.",  # Russian ruble variations
            r"дол",
            r"\$",  # Dollar variations
            r"евр",
            r"€",  # Euro variations
            r"фунт",
            r"£",  # Pound variations
        ]

        has_currency = False
        for pattern in currency_patterns:
            if re.search(pattern, price_str, re.IGNORECASE):
                has_currency = True
                break

        # Some valid formats might not have explicit currency symbols (default to RUB)
        # Check if it looks like a price with numbers and separators
        price_patterns = [
            r"^\d+(?:[,\s]\d+)*(?:\.\d+)?\s*[A-Z]{3}$",  # "7,825 RUB"
            r"^[A-Z]{3}\s*\d+(?:[,\s]\d+)*(?:\.\d+)?$",  # "RUB 7,825"
            r"^[₽€$£¥]\s*\d+(?:[,\s]\d+)*(?:\.\d+)?$",  # "₽ 7,825"
            r"^\d+(?:[,\s]\d+)*(?:\.\d+)?\s*[₽€$£¥]$",  # "7,825 ₽"
            r"^\d+(?:[,\s]\d+)*(?:\.\d+)?$",  # Just numbers "7825", "7,825"
        ]

        for pattern in price_patterns:
            if re.match(pattern, price_str, re.IGNORECASE):
                return True

        # If it has numbers and either currency symbols or looks like a reasonable price
        reasonable_price = re.match(r"^\d{1,6}(?:[,\s]\d{3})*(?:\.\d{2})?$", price_str)
        if reasonable_price:
            return True

        return has_currency and has_numbers

    def _is_valid_duration(self, duration_str: str) -> bool:
        """Validate duration string format with more flexible patterns."""
        if not duration_str:
            return False

        # Convert to string and clean
        duration_str = str(duration_str).strip().lower()
        if not duration_str:
            return False

        # Check if it contains any numbers
        has_numbers = any(char.isdigit() for char in duration_str)
        if not has_numbers:
            return False

        # More flexible duration pattern detection
        duration_patterns = [
            r"(\d+)\s*[hч]\s*(\d+)\s*[mм]",  # 1h 30m, 1ч 30м
            r"(\d+)[hч](\d+)[mм]",  # 1h30m, 1ч30м
            r"(\d+)\s*[hч]",  # 1h, 1ч
            r"(\d+)\s*[mм]",  # 90m, 90м
            r"(\d+)\s*мин",
            r"(\d+)\s*min",  # 90 мин, 90 min
            r"(\d+)\s*часов",
            r"(\d+)\s*hours",  # 2 часов, 2 hours
            r"(\d+):(\d+)",  # 1:30
            r"\d+\s*час",
            r"\d+\s*hour",  # 1 час, 1 hour
        ]

        for pattern in duration_patterns:
            if re.search(pattern, duration_str):
                return True

        # Check for common duration indicators
        has_time_indicators = any(
            indicator in duration_str
            for indicator in ["h", "ч", "m", "м", "мин", "min", "hour", "час", ":"]
        )

        # If it has numbers and looks like a reasonable duration (1-48 hours in minutes)
        if has_numbers:
            # Try to extract numbers
            num_matches = re.findall(r"\d+", duration_str)
            if num_matches:
                # Check if any number could be a reasonable duration
                for num_str in num_matches:
                    try:
                        num = int(num_str)
                        # Reasonable flight duration: 30 minutes to 48 hours (2880 minutes)
                        if 30 <= num <= 2880:
                            return True
                    except ValueError:
                        continue

        return has_time_indicators and has_numbers

    def _is_valid_time(self, time_str: str) -> bool:
        """Validate time string format with more flexible patterns."""
        if not time_str:
            return False

        # Convert to string and clean
        time_str = str(time_str).strip()
        if not time_str:
            return False

        # Standard HH:MM format
        if re.match(r"^\d{1,2}:\d{2}$", time_str):
            try:
                hour, minute = map(int, time_str.split(":"))
                return 0 <= hour <= 23 and 0 <= minute <= 59
            except (ValueError, AttributeError):
                return False

        # HH:MM:SS format
        if re.match(r"^\d{1,2}:\d{2}:\d{2}$", time_str):
            try:
                hour, minute, _ = map(int, time_str.split(":"))
                return 0 <= hour <= 23 and 0 <= minute <= 59
            except (ValueError, AttributeError):
                return False

        # 12-hour format with AM/PM
        am_pm_pattern = r"^(\d{1,2}):(\d{2})\s*([AP]M|[ap]m)$"
        match = re.match(am_pm_pattern, time_str, re.IGNORECASE)
        if match:
            try:
                hour = int(match.group(1))
                minute = int(match.group(2))
                am_pm = match.group(3).upper()

                if not (0 <= minute <= 59):
                    return False

                if am_pm == "AM":
                    return 1 <= hour <= 12
                elif am_pm == "PM":
                    return 1 <= hour <= 12
                else:
                    return False
            except (ValueError, AttributeError):
                return False

        # Check if it's just hours (like "10" for 10:00)
        if re.match(r"^\d{1,2}$", time_str):
            try:
                hour = int(time_str)
                return 0 <= hour <= 23
            except (ValueError, AttributeError):
                return False

        return False
