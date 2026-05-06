"""
Rankings Calculation Job

This script calculates ranking scores for all buildings and stores them in the rankings_cache table.
It should be run daily via Cloud Scheduler or manually when needed.

Requirements: 7
"""

import os
from datetime import datetime, timedelta
from google.cloud import bigquery
from services.ranking import calculate_ranking_score
from services.enrichment import enrich_building_data


# BigQuery configuration
PROJECT_ID = os.getenv('GCP_PROJECT', 'trim-descent-452802-t2')
DATASET = 'openbuildings'
TABLE = 'thailand_raw'
RANKINGS_TABLE = 'rankings_cache'

# Solar calculation constants
PANEL_EFFICIENCY = 0.20
USABLE_ROOF_RATIO = 0.50
COST_PER_WP = 25  # THB/Wp
ELECTRICITY_RATE = 4.18  # THB/kWh
AVG_IRRADIANCE = 5.06  # kWh/m²/day (Thailand average)
SYSTEM_EFFICIENCY = 0.80


def calculate_solar_metrics(area_m2: float, confidence: float) -> dict:
    """
    Calculate solar metrics for a building
    
    Args:
        area_m2: Building area in square meters
        confidence: ML confidence score
        
    Returns:
        Dict with solar metrics
    """
    # Adjust for confidence
    confidence_adjustment = max(confidence, 0.7)
    usable_roof_area = area_m2 * USABLE_ROOF_RATIO * confidence_adjustment
    system_size_kwp = usable_roof_area * PANEL_EFFICIENCY
    
    # Annual production
    annual_production_kwh = system_size_kwp * AVG_IRRADIANCE * 365 * SYSTEM_EFFICIENCY
    
    # Financial calculations
    installation_cost_thb = system_size_kwp * 1000 * COST_PER_WP
    annual_savings_thb = annual_production_kwh * ELECTRICITY_RATE
    payback_years = installation_cost_thb / annual_savings_thb if annual_savings_thb > 0 else 999
    
    return {
        "system_size_kwp": system_size_kwp,
        "annual_production_kwh": annual_production_kwh,
        "installation_cost_thb": installation_cost_thb,
        "annual_savings_thb": annual_savings_thb,
        "payback_years": payback_years
    }


def calculate_rankings_for_scope(
    bq_client: bigquery.Client,
    scope_type: str,
    scope_value: str,
    limit: int = 10000
) -> list:
    """
    Calculate rankings for a specific scope
    
    Args:
        bq_client: BigQuery client
        scope_type: Scope type ("global", "country", "region", "province")
        scope_value: Scope identifier (e.g., "TH", "Bangkok")
        limit: Maximum number of buildings to rank
        
    Returns:
        List of ranking records
    """
    print(f"Calculating rankings for {scope_type}: {scope_value}")
    
    # Build query based on scope
    where_clause = "confidence >= 0.7"  # Minimum confidence threshold
    
    if scope_type == "country":
        # For Thailand, we don't need additional filtering
        # In the future, this could filter by country code
        pass
    elif scope_type == "region" or scope_type == "province":
        # TODO: Add spatial filtering based on region/province boundaries
        # For now, we'll just use the country-level data
        pass
    
    # Query buildings
    query = f"""
        SELECT 
            full_plus_code as open_buildings_id,
            latitude,
            longitude,
            area_in_meters as area_m2,
            confidence
        FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
        WHERE {where_clause}
        ORDER BY area_in_meters DESC, confidence DESC
        LIMIT {limit}
    """
    
    print(f"Querying buildings...")
    results = list(bq_client.query(query).result())
    print(f"Found {len(results)} buildings")
    
    # Calculate rankings
    rankings = []
    calculated_at = datetime.now()
    expires_at = calculated_at + timedelta(hours=24)
    
    for idx, row in enumerate(results):
        # Get building data
        building_id = row['open_buildings_id'] or f"OB_{hash(str(row['latitude']) + str(row['longitude'])) % 10000000}"
        area_m2 = float(row['area_m2'])
        confidence = float(row['confidence'])
        latitude = float(row['latitude'])
        longitude = float(row['longitude'])
        
        # Calculate solar metrics
        solar_metrics = calculate_solar_metrics(area_m2, confidence)
        
        # Get permitting status (default to unknown for now)
        permitting_status = "unknown"
        
        # Calculate ranking score
        ranking_data = calculate_ranking_score(
            annual_production_kwh=solar_metrics['annual_production_kwh'],
            area_m2=area_m2,
            confidence=confidence,
            payback_years=solar_metrics['payback_years'],
            permitting_status=permitting_status
        )
        
        # Create ranking record
        ranking = {
            "building_id": building_id,
            "open_buildings_id": row['open_buildings_id'],
            "latitude": latitude,
            "longitude": longitude,
            "area_m2": area_m2,
            "confidence": confidence,
            "ranking_score": ranking_data['ranking_score'],
            "ranking_position": idx + 1,
            "solar_potential_score": ranking_data['solar_potential_score'],
            "roof_area_score": ranking_data['roof_area_score'],
            "confidence_score": ranking_data['confidence_score'],
            "payback_score": ranking_data['payback_score'],
            "permitting_score": ranking_data['permitting_score'],
            "scope_type": scope_type,
            "scope_value": scope_value,
            "calculated_at": calculated_at,
            "expires_at": expires_at
        }
        
        rankings.append(ranking)
        
        # Progress indicator
        if (idx + 1) % 1000 == 0:
            print(f"Processed {idx + 1}/{len(results)} buildings...")
    
    return rankings


def store_rankings(bq_client: bigquery.Client, rankings: list) -> None:
    """
    Store rankings in BigQuery
    
    Args:
        bq_client: BigQuery client
        rankings: List of ranking records
    """
    if not rankings:
        print("No rankings to store")
        return
    
    table_id = f"{PROJECT_ID}.{DATASET}.{RANKINGS_TABLE}"
    
    # Delete existing rankings for this scope
    scope_type = rankings[0]['scope_type']
    scope_value = rankings[0]['scope_value']
    
    delete_query = f"""
        DELETE FROM `{table_id}`
        WHERE scope_type = '{scope_type}' AND scope_value = '{scope_value}'
    """
    
    print(f"Deleting existing rankings for {scope_type}: {scope_value}")
    bq_client.query(delete_query).result()
    
    # Insert new rankings
    print(f"Inserting {len(rankings)} new rankings...")
    
    errors = bq_client.insert_rows_json(table_id, rankings)
    
    if errors:
        print(f"Errors inserting rankings: {errors}")
    else:
        print(f"Successfully stored {len(rankings)} rankings")


def main():
    """
    Main function to calculate and store rankings
    """
    print("=" * 60)
    print("Rankings Calculation Job")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Initialize BigQuery client
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    # Calculate rankings for different scopes
    scopes = [
        ("country", "TH"),
        # Add more scopes as needed:
        # ("region", "Central"),
        # ("province", "Bangkok"),
    ]
    
    for scope_type, scope_value in scopes:
        try:
            # Calculate rankings
            rankings = calculate_rankings_for_scope(
                bq_client,
                scope_type,
                scope_value,
                limit=10000  # Top 10K buildings per scope
            )
            
            # Store rankings
            store_rankings(bq_client, rankings)
            
            print()
        except Exception as e:
            print(f"Error calculating rankings for {scope_type}: {scope_value}")
            print(f"Error: {str(e)}")
            print()
    
    print("=" * 60)
    print(f"Completed at: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
