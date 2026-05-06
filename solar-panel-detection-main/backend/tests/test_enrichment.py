"""
Tests for data enrichment services
Requirements: 1, 12, 15
"""

import pytest
from datetime import datetime
from services.enrichment import (
    calculate_accuracy_level,
    build_data_provenance,
    enrich_building_data,
    get_data_age_days,
    get_permitting_status,
    calculate_data_quality_flag,
    DATA_COLLECTION_DATE,
    DATA_SOURCE,
    DATA_SOURCE_URL,
    COLLECTION_METHOD
)


class TestCalculateAccuracyLevel:
    """Test calculate_accuracy_level function (Req 12)"""
    
    def test_high_accuracy_recent_high_confidence(self):
        """Test high accuracy for recent data with high confidence"""
        level, factors = calculate_accuracy_level(confidence=0.85, data_age_days=200)
        
        assert level == "high"
        assert factors["confidence_score"] == 0.85
        assert factors["data_age_days"] == 200
        assert factors["validation_status"] == "unvalidated"
    
    def test_high_accuracy_boundary_confidence(self):
        """Test high accuracy at confidence boundary (0.8)"""
        level, factors = calculate_accuracy_level(confidence=0.8, data_age_days=364)
        
        assert level == "high"
        assert factors["confidence_score"] == 0.8
    
    def test_medium_accuracy_good_confidence_old_data(self):
        """Test medium accuracy for good confidence but older data"""
        level, factors = calculate_accuracy_level(confidence=0.75, data_age_days=500)
        
        assert level == "medium"
        assert factors["confidence_score"] == 0.75
        assert factors["data_age_days"] == 500
    
    def test_medium_accuracy_recent_lower_confidence(self):
        """Test medium accuracy for recent data with lower confidence"""
        level, factors = calculate_accuracy_level(confidence=0.72, data_age_days=600)
        
        assert level == "medium"
    
    def test_medium_accuracy_boundary_confidence(self):
        """Test medium accuracy at confidence boundary (0.7)"""
        level, factors = calculate_accuracy_level(confidence=0.7, data_age_days=800)
        
        assert level == "medium"
    
    def test_low_accuracy_low_confidence_old_data(self):
        """Test low accuracy for low confidence and old data"""
        level, factors = calculate_accuracy_level(confidence=0.65, data_age_days=800)
        
        assert level == "low"
        assert factors["confidence_score"] == 0.65
        assert factors["data_age_days"] == 800
    
    def test_low_accuracy_very_low_confidence(self):
        """Test low accuracy for very low confidence"""
        level, factors = calculate_accuracy_level(confidence=0.55, data_age_days=900)
        
        assert level == "low"
    
    def test_factors_structure(self):
        """Test that factors object has correct structure"""
        level, factors = calculate_accuracy_level(confidence=0.8, data_age_days=100)
        
        assert "confidence_score" in factors
        assert "data_age_days" in factors
        assert "validation_status" in factors
        assert isinstance(factors["confidence_score"], float)
        assert isinstance(factors["data_age_days"], int)
        assert isinstance(factors["validation_status"], str)


class TestBuildDataProvenance:
    """Test build_data_provenance function (Req 1, 15)"""
    
    def test_provenance_structure(self):
        """Test that provenance object has correct structure"""
        provenance = build_data_provenance()
        
        assert "data_source" in provenance
        assert "collection_method" in provenance
        assert "last_updated" in provenance
    
    def test_provenance_values(self):
        """Test that provenance contains correct values"""
        provenance = build_data_provenance()
        
        assert provenance["data_source"] == DATA_SOURCE
        assert provenance["collection_method"] == COLLECTION_METHOD
        assert provenance["last_updated"] == DATA_COLLECTION_DATE.isoformat() + "Z"
    
    def test_provenance_data_source(self):
        """Test data source is Google Open Buildings v3"""
        provenance = build_data_provenance()
        
        assert provenance["data_source"] == "Google Open Buildings v3"
    
    def test_provenance_collection_method(self):
        """Test collection method is ML detection"""
        provenance = build_data_provenance()
        
        assert "ML detection" in provenance["collection_method"]
        assert "satellite imagery" in provenance["collection_method"]
    
    def test_provenance_timestamp_format(self):
        """Test that timestamp is in ISO 8601 format"""
        provenance = build_data_provenance()
        
        # Should be parseable as ISO 8601
        timestamp = provenance["last_updated"]
        assert timestamp.endswith("Z")
        # Should be parseable
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


class TestEnrichBuildingData:
    """Test enrich_building_data function (Req 1, 6, 12, 15)"""
    
    def test_enrichment_adds_all_fields(self):
        """Test that enrichment adds all required fields"""
        raw_data = {
            "id": 123456,
            "open_buildings_id": "OB_12345",
            "latitude": 13.7563,
            "longitude": 100.5018,
            "area_m2": 250.0,
            "confidence": 0.85
        }
        
        enriched = enrich_building_data(raw_data)
        
        # Check original fields preserved
        assert enriched["id"] == 123456
        assert enriched["confidence"] == 0.85
        
        # Check new fields added
        assert "data_provenance" in enriched
        assert "confidence_warning" in enriched
        assert "accuracy_level" in enriched
        assert "accuracy_factors" in enriched
        assert "permitting_status" in enriched
        assert "data_source" in enriched
        assert "data_collection_date" in enriched
        assert "data_source_url" in enriched
        assert "data_quality_flag" in enriched
    
    def test_confidence_warning_true_for_low_confidence(self):
        """Test confidence warning is True when confidence < 0.7"""
        raw_data = {
            "latitude": 13.7563,
            "longitude": 100.5018,
            "confidence": 0.65
        }
        
        enriched = enrich_building_data(raw_data)
        
        assert enriched["confidence_warning"] is True
    
    def test_confidence_warning_false_for_high_confidence(self):
        """Test confidence warning is False when confidence >= 0.7"""
        raw_data = {
            "latitude": 13.7563,
            "longitude": 100.5018,
            "confidence": 0.85
        }
        
        enriched = enrich_building_data(raw_data)
        
        assert enriched["confidence_warning"] is False
    
    def test_confidence_warning_boundary(self):
        """Test confidence warning at boundary (0.7)"""
        raw_data = {
            "latitude": 13.7563,
            "longitude": 100.5018,
            "confidence": 0.7
        }
        
        enriched = enrich_building_data(raw_data)
        
        assert enriched["confidence_warning"] is False
    
    def test_permitting_status_default(self):
        """Test permitting status defaults to unknown"""
        raw_data = {
            "latitude": 13.7563,
            "longitude": 100.5018,
            "confidence": 0.85
        }
        
        enriched = enrich_building_data(raw_data)
        
        assert enriched["permitting_status"] == "unknown"
    
    def test_data_source_fields(self):
        """Test data source traceability fields (Req 15)"""
        raw_data = {
            "latitude": 13.7563,
            "longitude": 100.5018,
            "confidence": 0.85
        }
        
        enriched = enrich_building_data(raw_data)
        
        assert enriched["data_source"] == DATA_SOURCE
        assert enriched["data_collection_date"] == DATA_COLLECTION_DATE.isoformat() + "Z"
        assert enriched["data_source_url"] == DATA_SOURCE_URL
    
    def test_accuracy_level_high(self):
        """Test accuracy level is calculated correctly for high confidence"""
        raw_data = {
            "latitude": 13.7563,
            "longitude": 100.5018,
            "confidence": 0.9
        }
        
        enriched = enrich_building_data(raw_data)
        
        # Data is old (2023), so won't be "high" unless data_age < 365
        # Since data is from 2023-06-15, it's > 365 days old
        assert enriched["accuracy_level"] in ["high", "medium"]
    
    def test_data_quality_flag_high(self):
        """Test data quality flag for high confidence"""
        raw_data = {
            "latitude": 13.7563,
            "longitude": 100.5018,
            "confidence": 0.85
        }
        
        enriched = enrich_building_data(raw_data)
        
        assert enriched["data_quality_flag"] == "high"
    
    def test_data_quality_flag_medium(self):
        """Test data quality flag for medium confidence"""
        raw_data = {
            "latitude": 13.7563,
            "longitude": 100.5018,
            "confidence": 0.75
        }
        
        enriched = enrich_building_data(raw_data)
        
        assert enriched["data_quality_flag"] == "medium"
    
    def test_data_quality_flag_low(self):
        """Test data quality flag for low confidence"""
        raw_data = {
            "latitude": 13.7563,
            "longitude": 100.5018,
            "confidence": 0.65
        }
        
        enriched = enrich_building_data(raw_data)
        
        assert enriched["data_quality_flag"] == "low"


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_get_data_age_days(self):
        """Test data age calculation"""
        age_days = get_data_age_days()
        
        # Should be positive
        assert age_days > 0
        
        # Should be reasonable (data from 2023-06-15)
        # As of 2026-04-18, should be around 1000+ days
        assert age_days > 900
    
    def test_get_permitting_status(self):
        """Test permitting status lookup (placeholder)"""
        status = get_permitting_status(13.7563, 100.5018)
        
        # Currently returns "unknown" for all locations
        assert status == "unknown"
    
    def test_calculate_data_quality_flag_high(self):
        """Test quality flag calculation for high confidence"""
        flag = calculate_data_quality_flag(0.85)
        assert flag == "high"
    
    def test_calculate_data_quality_flag_medium(self):
        """Test quality flag calculation for medium confidence"""
        flag = calculate_data_quality_flag(0.75)
        assert flag == "medium"
    
    def test_calculate_data_quality_flag_low(self):
        """Test quality flag calculation for low confidence"""
        flag = calculate_data_quality_flag(0.65)
        assert flag == "low"
    
    def test_calculate_data_quality_flag_boundary_high(self):
        """Test quality flag at high boundary (0.8)"""
        flag = calculate_data_quality_flag(0.8)
        assert flag == "high"
    
    def test_calculate_data_quality_flag_boundary_medium(self):
        """Test quality flag at medium boundary (0.7)"""
        flag = calculate_data_quality_flag(0.7)
        assert flag == "medium"
