"""
Solar calculation models
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class CustomSolarParameters(BaseModel):
    """Custom parameters for solar calculations"""
    panel_efficiency: Optional[float] = Field(None, ge=0.15, le=0.25, description="Panel efficiency ratio")
    system_efficiency: Optional[float] = Field(None, ge=0.70, le=0.90, description="System performance ratio")
    usable_roof_ratio: Optional[float] = Field(None, ge=0.30, le=0.70, description="Usable roof percentage")
    cost_per_wp: Optional[float] = Field(None, ge=20, le=50, description="Installation cost THB/Wp")
    electricity_rate: Optional[float] = Field(None, ge=3.0, le=6.0, description="Electricity rate THB/kWh")
    co2_factor: Optional[float] = Field(None, ge=0.30, le=0.50, description="CO2 emission factor kg/kWh")


class SolarCalculationRequest(BaseModel):
    """Request for solar potential calculation"""
    latitude: float
    longitude: float
    area_m2: float
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    tilt: Optional[float] = None
    azimuth: Optional[float] = 180
    custom_params: Optional[CustomSolarParameters] = None


class CalculationStep(BaseModel):
    """Individual calculation step with formula and inputs"""
    formula: str = Field(..., description="Mathematical formula used")
    inputs: Dict[str, Any] = Field(..., description="Input values")
    result: float = Field(..., description="Calculated result")
    unit: str = Field(..., description="Unit of measurement")


class CalculationBreakdown(BaseModel):
    """Detailed breakdown of calculation steps"""
    step_1_usable_area: CalculationStep
    step_2_system_size: CalculationStep
    step_3_annual_production: CalculationStep
    step_4_financial: CalculationStep


class SolarCalculationResponse(BaseModel):
    """Enhanced solar calculation response"""
    # Existing fields
    usable_roof_area: float
    system_size_kwp: float
    annual_production_kwh: float
    installation_cost_thb: float
    annual_savings_thb: float
    payback_period_years: Optional[float]
    co2_reduction_kg: float
    co2_reduction_ton: float
    irradiance_source: str
    irradiance_kwh_m2_day: float
    assumptions: Dict[str, Any]
    weather_forecast: Optional[Dict[str, Any]] = None
    
    # NEW: Calculation breakdown (Req 5)
    calculation_breakdown: CalculationBreakdown
    
    # NEW: Custom parameters tracking (Req 13)
    custom_parameters: Optional[Dict[str, float]] = Field(
        None,
        description="Parameters that were customized from defaults"
    )
