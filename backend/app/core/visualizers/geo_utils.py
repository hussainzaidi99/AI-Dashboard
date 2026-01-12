"""
Geographic Utilities - Geographic data detection and normalization
Provides utilities for working with geographic data in visualizations
"""
#backend/app/core/visualizers/geo_utils.py

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import logging
import re

logger = logging.getLogger(__name__)


# Country name mappings (common variations)
COUNTRY_MAPPINGS = {
    "usa": "United States",
    "us": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "britain": "United Kingdom",
    "great britain": "United Kingdom",
    "uae": "United Arab Emirates",
    "russia": "Russian Federation",
    "south korea": "Korea, Republic of",
    "north korea": "Korea, Democratic People's Republic of",
}


class GeoUtils:
    """Utilities for geographic data processing"""
    
    @staticmethod
    def detect_geographic_columns(df: pd.DataFrame) -> Dict[str, str]:
        """
        Detect geographic columns in DataFrame
        
        Args:
            df: DataFrame to analyze
        
        Returns:
            Dictionary mapping column types to column names
            Types: 'latitude', 'longitude', 'country', 'state', 'city', 'region'
        """
        geo_columns = {}
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Latitude detection
            if any(keyword in col_lower for keyword in ['lat', 'latitude']):
                if GeoUtils._is_latitude_column(df[col]):
                    geo_columns['latitude'] = col
            
            # Longitude detection
            elif any(keyword in col_lower for keyword in ['lon', 'long', 'longitude']):
                if GeoUtils._is_longitude_column(df[col]):
                    geo_columns['longitude'] = col
            
            # Country detection
            elif any(keyword in col_lower for keyword in ['country', 'nation']):
                geo_columns['country'] = col
            
            # State detection
            elif any(keyword in col_lower for keyword in ['state', 'province', 'region']):
                if 'state' not in geo_columns:  # Prefer 'state' over 'region'
                    geo_columns['state'] = col
            
            # City detection
            elif any(keyword in col_lower for keyword in ['city', 'town', 'municipality']):
                geo_columns['city'] = col
            
            # Postal code
            elif any(keyword in col_lower for keyword in ['zip', 'postal', 'postcode']):
                geo_columns['postal_code'] = col
        
        return geo_columns
    
    @staticmethod
    def _is_latitude_column(series: pd.Series) -> bool:
        """Check if column contains valid latitude values"""
        try:
            # Convert to numeric
            numeric_series = pd.to_numeric(series, errors='coerce')
            
            # Check if values are in valid latitude range (-90 to 90)
            valid_mask = (numeric_series >= -90) & (numeric_series <= 90)
            
            # At least 80% of non-null values should be valid
            valid_percentage = valid_mask.sum() / numeric_series.notna().sum()
            
            return valid_percentage > 0.8
        except:
            return False
    
    @staticmethod
    def _is_longitude_column(series: pd.Series) -> bool:
        """Check if column contains valid longitude values"""
        try:
            # Convert to numeric
            numeric_series = pd.to_numeric(series, errors='coerce')
            
            # Check if values are in valid longitude range (-180 to 180)
            valid_mask = (numeric_series >= -180) & (numeric_series <= 180)
            
            # At least 80% of non-null values should be valid
            valid_percentage = valid_mask.sum() / numeric_series.notna().sum()
            
            return valid_percentage > 0.8
        except:
            return False
    
    @staticmethod
    def normalize_country_names(series: pd.Series) -> pd.Series:
        """
        Normalize country names to standard format
        
        Args:
            series: Series with country names
        
        Returns:
            Series with normalized country names
        """
        def normalize_name(name):
            if pd.isna(name):
                return name
            
            name_lower = str(name).lower().strip()
            
            # Check mappings
            if name_lower in COUNTRY_MAPPINGS:
                return COUNTRY_MAPPINGS[name_lower]
            
            # Title case for standard names
            return str(name).strip().title()
        
        return series.apply(normalize_name)
    
    @staticmethod
    def validate_coordinates(
        lat: pd.Series,
        lon: pd.Series
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Validate and clean latitude/longitude coordinates
        
        Args:
            lat: Latitude series
            lon: Longitude series
        
        Returns:
            Tuple of (cleaned_lat, cleaned_lon, valid_mask)
        """
        # Convert to numeric
        lat_numeric = pd.to_numeric(lat, errors='coerce')
        lon_numeric = pd.to_numeric(lon, errors='coerce')
        
        # Create validity mask
        valid_mask = (
            lat_numeric.notna() &
            lon_numeric.notna() &
            (lat_numeric >= -90) &
            (lat_numeric <= 90) &
            (lon_numeric >= -180) &
            (lon_numeric <= 180)
        )
        
        return lat_numeric, lon_numeric, valid_mask
    
    @staticmethod
    def get_map_center(
        lat: pd.Series,
        lon: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate map center from coordinates
        
        Args:
            lat: Latitude series
            lon: Longitude series
        
        Returns:
            Dictionary with 'lat' and 'lon' center coordinates
        """
        lat_clean, lon_clean, valid_mask = GeoUtils.validate_coordinates(lat, lon)
        
        if valid_mask.sum() == 0:
            # Default to world center
            return {'lat': 0.0, 'lon': 0.0}
        
        # Calculate mean of valid coordinates
        center_lat = lat_clean[valid_mask].mean()
        center_lon = lon_clean[valid_mask].mean()
        
        return {
            'lat': float(center_lat),
            'lon': float(center_lon)
        }
    
    @staticmethod
    def infer_location_scope(df: pd.DataFrame, location_column: str) -> str:
        """
        Infer the geographic scope of location data
        
        Args:
            df: DataFrame
            location_column: Column with location names
        
        Returns:
            Scope: 'world', 'usa', 'europe', etc.
        """
        # Get unique locations
        unique_locations = df[location_column].dropna().unique()
        
        if len(unique_locations) == 0:
            return 'world'
        
        # Check for US states
        us_states = {
            'alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado',
            'connecticut', 'delaware', 'florida', 'georgia', 'hawaii', 'idaho',
            'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana',
            'maine', 'maryland', 'massachusetts', 'michigan', 'minnesota',
            'mississippi', 'missouri', 'montana', 'nebraska', 'nevada',
            'new hampshire', 'new jersey', 'new mexico', 'new york',
            'north carolina', 'north dakota', 'ohio', 'oklahoma', 'oregon',
            'pennsylvania', 'rhode island', 'south carolina', 'south dakota',
            'tennessee', 'texas', 'utah', 'vermont', 'virginia', 'washington',
            'west virginia', 'wisconsin', 'wyoming'
        }
        
        locations_lower = {str(loc).lower() for loc in unique_locations}
        
        # Check if mostly US states
        us_match = len(locations_lower & us_states) / len(locations_lower)
        if us_match > 0.5:
            return 'usa'
        
        # Default to world
        return 'world'
    
    @staticmethod
    def get_iso_country_codes(countries: pd.Series) -> pd.Series:
        """
        Convert country names to ISO 3-letter codes
        
        Args:
            countries: Series with country names
        
        Returns:
            Series with ISO codes
        """
        # Simple mapping for common countries
        iso_mapping = {
            'united states': 'USA',
            'united kingdom': 'GBR',
            'canada': 'CAN',
            'australia': 'AUS',
            'germany': 'DEU',
            'france': 'FRA',
            'italy': 'ITA',
            'spain': 'ESP',
            'china': 'CHN',
            'japan': 'JPN',
            'india': 'IND',
            'brazil': 'BRA',
            'mexico': 'MEX',
            'russia': 'RUS',
            'south africa': 'ZAF',
        }
        
        def get_iso_code(country):
            if pd.isna(country):
                return None
            
            country_lower = str(country).lower().strip()
            return iso_mapping.get(country_lower, country)
        
        return countries.apply(get_iso_code)
