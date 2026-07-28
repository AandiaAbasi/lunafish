from dataclasses import dataclass

@dataclass
class WeightItem:
    option_id: int
    scale_id: int
    weight: float

@dataclass
class SaveWeightsDTO:
    test_id: int
    items: list[WeightItem]