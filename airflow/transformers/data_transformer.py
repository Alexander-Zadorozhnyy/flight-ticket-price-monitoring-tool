from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from transformers.quality import BatchQuality, QualityCalculator


class DataTransformer(ABC):
    def __init__(self):
        self.quality_calculator = QualityCalculator()

    def structure_flight_output_list(
        self, flights: List[Dict[str, Any]], departure_date
    ) -> Tuple[List, BatchQuality]:
        result = []
        flight_qualities = []

        for flight in flights:
            try:
                structured_output = self.structure_flight_output(
                    flight_dict=flight, departure_date=departure_date
                )
            except Exception as e:
                # import traceback
                # traceback.print_exc()
                # print(f"Error while transforming flight data: {str(e)}")

                # Create invalid quality entry
                invalid_quality = self.quality_calculator.create_invalid_quality(str(e))
                flight_qualities.append(invalid_quality)
                continue
            
            # Calculate quality metrics
            quality = self.quality_calculator.calculate_flight_quality(
                flight, structured_output
            )
            flight_qualities.append(quality)

            if quality.is_valid and structured_output:
                result.append(structured_output)

        batch_quality = self.quality_calculator.calculate_batch_quality(
            flight_qualities
        )
        return result, batch_quality

    @abstractmethod
    def structure_flight_output(
        self, flight_dict: Dict[str, Any], departure_date: datetime
    ) -> Optional[Dict[str, Any]]:
        pass
