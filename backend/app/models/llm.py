"""
Pydantic models for LLM structured outputs 
- define LLM response schema for route planning
- used by instructor to guide LLM and validate responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RoutingPreferences(BaseModel):
    """
    Structured output returned by LLM after analyzing a user prompt for route planning

    Attributes:
    - preferences: dict of user preferences extracted from the prompt, used to adjust routing costs
        Keys: road types (e.g. "highway", "residential", "scenic") and special attributes (e.g. "unlit", "scenic")
        Values: cost multipliers (1.0 = neutral, >1.0 = avoid, <1.0 = prefer)

    - reasoning: human-readable explanation of how the LLM interpreted the prompt and derived the preferences
    - time_of_day: time if specified in the prompt(morning/afternoon/evening/night)
    - distance_preference: distance if specified in the prompt (e.g. "5km")

    Example:
    Input: 'scenic night run avoiding highways, about 5km'
    Ouput:
    {
        "preferences": {
            "highway": 10.0,   # Strongly avoid highways
            "scenic": 0.5,     # Prefer scenic routes (half cost if scenic_score > 7)
            "unlit": 2.0       # Avoid unlit roads at night (double cost)
        },
        "reasoning": "User wants a scenic night run, avoiding major roads",
        "time_of_day": "night",
        "distance_preference": "5km"
    }
    """

    preferences: Dict[str, float] = Field(
        default_factory=dict,
        description="""
        Cost multipliers for routing

        Road type keys:
        - motorway: interstate highways
        - trunk: major roads
        - primary: main connecting roads
        - secondary: secondary roads
        - tertiary: minor roads
        - residential: neighbourhood streets
        - path: trails/paths
        - footway: sidewalks
        - cycleway: bike paths
        
        Attribute keys:
        - scenic: prefer high scenic value routes
        - unlit: avoid unlit streets

        Values:
        - 1.0 = neutral (default, no preference)
        - >1.0 = avoid (e.g. 10.0 to strongly avoid)
        - <1.0 = prefer (e.g. 0.5 to prefer)

        Examples:
        - "avoid highways" -> {"motorway": 10.0, "trunk": 5.0, "highway": 10.0}
        - "prefer trails" -> {"path": 0.5, "footway": 0.4}
        - "night run" -> {"unlit": 10.0} 
        - "scenic route" -> {"scenic": 0.3}
"""
    )
    reasoning: Optional[str] = Field(
        None,
        description="LLM's explanation of routing preferences derived from the prompt"
    )
    time_of_day: Optional[str] = Field(
        None,
        description="Time preference if mentioned in the prompt (e.g. 'morning', 'afternoon', 'evening', 'night')"
    )
    distance_preference: Optional[str] = Field(
        None,
        description="Distance preference extracted from the prompt (e.g. '5km', '10 miles', 'long', 'short')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "preferences": {
                    "highway": 10.0,
                    "scenic": 0.5,
                    "unlit": 2.0
                },
                "reasoning": "User wants a 5km scenic night run, avoiding major roads",
                "time_of_day": "night",
                "distance_preference": "5km"
            }
            }