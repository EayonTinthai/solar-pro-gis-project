#!/usr/bin/env python3
"""
Download Bangkok district boundaries (50 districts/เขต) as GeoJSON.

Strategy:
1. Try Google Earth Engine (FAO GAUL level 2) with service account
2. Fallback: Download GADM Thailand admin level 2 and filter for Bangkok

Output: frontend/public/bangkok-districts.geojson
"""

import json
import os
import sys
import urllib.request
import zipfile
import tempfile

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'frontend', 'public', 'bangkok-districts.geojson'
)

GEE_KEY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'gee-key.json'
)

PROJECT_ID = 'trim-descent-452802-t2'


def try_gee():
    """Try to get Bangkok districts from Google Earth Engine."""
    try:
        import ee
    except ImportError:
        print("earthengine-api not installed, installing...")
        os.system(f"{sys.executable} -m pip install earthengine-api --quiet")
        import ee

    try:
        credentials = ee.ServiceAccountCredentials(
            None, GEE_KEY_PATH
        )
        ee.Initialize(credentials, project=PROJECT_ID)
        print("GEE authenticated successfully")

        # Try FAO GAUL Level 2 (districts)
        # Bangkok province in GAUL
        try:
            gaul2 = ee.FeatureCollection('FAO/GAUL/2015/level2')
            # Filter for Bangkok - ADM1_NAME = 'Krung Thep Maha Nakhon' or 'Bangkok'
            bangkok = gaul2.filter(
                ee.Filter.Or(
                    ee.Filter.eq('ADM1_NAME', 'Krung Thep Maha Nakhon'),
                    ee.Filter.eq('ADM1_NAME', 'Bangkok'),
                    ee.Filter.eq('ADM1_NAME', 'Bangkok Metropolis'),
                )
            )
            
            count = bangkok.size().getInfo()
            print(f"FAO GAUL: Found {count} features for Bangkok")
            
            if count > 0:
                geojson = bangkok.getInfo()
                # Save
                os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
                with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                    json.dump(geojson, f, ensure_ascii=False)
                print(f"Saved {count} districts to {OUTPUT_PATH}")
                return True
        except Exception as e:
            print(f"FAO GAUL failed: {e}")

        # Try GADM via GEE (if available as asset)
        try:
            # GADM 4.1 Thailand level 2
            gadm = ee.FeatureCollection('projects/sat-io/open-datasets/geoboundaries/CGAZ_ADM2')
            bangkok = gadm.filter(
                ee.Filter.And(
                    ee.Filter.eq('shapeGroup', 'THA'),
                    ee.Filter.Or(
                        ee.Filter.stringContains('shapeName', 'Bangkok'),
                        ee.Filter.eq('ADM1_NAME', 'Bangkok'),
                    )
                )
            )
            count = bangkok.size().getInfo()
            if count > 0:
                geojson = bangkok.getInfo()
                os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
                with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                    json.dump(geojson, f, ensure_ascii=False)
                print(f"Saved {count} districts from geoboundaries to {OUTPUT_PATH}")
                return True
        except Exception as e:
            print(f"Geoboundaries via GEE failed: {e}")

        return False

    except Exception as e:
        print(f"GEE initialization failed: {e}")
        return False


def try_gadm_download():
    """Download GADM Thailand level 2 boundaries and filter for Bangkok."""
    print("Trying GADM download...")
    
    # GADM 4.1 GeoJSON for Thailand level 2
    urls = [
        'https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_THA_2.json.zip',
        'https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_THA_2.json',
    ]
    
    for url in urls:
        try:
            print(f"Downloading from {url}...")
            
            if url.endswith('.zip'):
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                    urllib.request.urlretrieve(url, tmp.name)
                    with zipfile.ZipFile(tmp.name, 'r') as zf:
                        # Find the JSON file inside
                        json_files = [f for f in zf.namelist() if f.endswith('.json')]
                        if json_files:
                            with zf.open(json_files[0]) as jf:
                                data = json.load(jf)
                        else:
                            continue
                    os.unlink(tmp.name)
            else:
                with urllib.request.urlopen(url) as response:
                    data = json.loads(response.read().decode('utf-8'))
            
            # Filter for Bangkok (NAME_1 = 'Bangkok' or 'Krung Thep Maha Nakhon')
            bangkok_names = {'Bangkok', 'Krung Thep Maha Nakhon', 'Bangkok Metropolis'}
            bangkok_features = [
                f for f in data.get('features', [])
                if f.get('properties', {}).get('NAME_1', '') in bangkok_names
            ]
            
            if not bangkok_features:
                # Try GID_1 pattern
                bangkok_features = [
                    f for f in data.get('features', [])
                    if 'THA.1_' in str(f.get('properties', {}).get('GID_1', ''))
                    or 'Bangkok' in str(f.get('properties', {}))
                ]
            
            if bangkok_features:
                result = {
                    'type': 'FeatureCollection',
                    'features': bangkok_features
                }
                os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
                with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False)
                print(f"Saved {len(bangkok_features)} Bangkok districts to {OUTPUT_PATH}")
                return True
            else:
                print(f"No Bangkok features found in GADM data. Available NAME_1 values sample:")
                names = set(f.get('properties', {}).get('NAME_1', '') for f in data.get('features', [])[:20])
                print(f"  {names}")
                
        except Exception as e:
            print(f"Failed with {url}: {e}")
            continue
    
    return False


def try_overpass_api():
    """Use OpenStreetMap Overpass API to get Bangkok district boundaries."""
    print("Trying Overpass API (OpenStreetMap)...")
    
    # Overpass query for Bangkok district boundaries (admin_level=6 in Thailand)
    query = """
[out:json][timeout:60];
area["name:en"="Bangkok"]["admin_level"="4"]->.bangkok;
(
  relation["admin_level"="6"](area.bangkok);
);
out body;
>;
out skel qt;
"""
    
    try:
        url = 'https://overpass-api.de/api/interpreter'
        data = urllib.parse.urlencode({'data': query}).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('User-Agent', 'SolarPotentialApp/1.0')
        
        with urllib.request.urlopen(req, timeout=120) as response:
            osm_data = json.loads(response.read().decode('utf-8'))
        
        # Convert OSM data to GeoJSON (simplified - just extract relations with ways)
        # This is complex, so we'll use a simpler approach
        elements = osm_data.get('elements', [])
        relations = [e for e in elements if e.get('type') == 'relation']
        print(f"Found {len(relations)} district relations from OSM")
        
        if len(relations) >= 40:  # Bangkok should have ~50 districts
            # We need to reconstruct polygons from ways - this is complex
            # Let's use a simpler GeoJSON export
            return try_osm_geojson_export()
        
    except Exception as e:
        print(f"Overpass API failed: {e}")
    
    return False


def try_osm_geojson_export():
    """Try to get Bangkok districts from a pre-built GeoJSON source."""
    print("Trying alternative GeoJSON sources...")
    
    # Try GitHub-hosted Thailand admin boundaries
    urls = [
        'https://raw.githubusercontent.com/apisit/thailand.json/master/thailandWithName.json',
        'https://raw.githubusercontent.com/cvibhagool/thailand-bindary/master/thailand-province.json',
    ]
    
    for url in urls:
        try:
            print(f"  Trying {url}...")
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'SolarPotentialApp/1.0')
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            features = data.get('features', [])
            if features:
                # Check if this has district-level data for Bangkok
                bangkok_features = [
                    f for f in features
                    if 'Bangkok' in str(f.get('properties', {}))
                    or 'กรุงเทพ' in str(f.get('properties', {}))
                ]
                if bangkok_features:
                    result = {'type': 'FeatureCollection', 'features': bangkok_features}
                    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
                    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False)
                    print(f"Saved {len(bangkok_features)} features to {OUTPUT_PATH}")
                    return True
        except Exception as e:
            print(f"  Failed: {e}")
    
    return False


def create_synthetic_districts():
    """
    Create synthetic Bangkok district boundaries as a fallback.
    Uses approximate centroids and Voronoi-like polygons for the 50 districts.
    """
    print("Creating synthetic Bangkok district boundaries...")
    
    # Bangkok 50 districts with approximate centroids
    # Source: Wikipedia / Thai government data
    districts = [
        {"name": "Phra Nakhon", "name_th": "พระนคร", "lat": 13.7580, "lon": 100.4990},
        {"name": "Dusit", "name_th": "ดุสิต", "lat": 13.7780, "lon": 100.5140},
        {"name": "Nong Chok", "name_th": "หนองจอก", "lat": 13.8560, "lon": 100.8590},
        {"name": "Bang Rak", "name_th": "บางรัก", "lat": 13.7280, "lon": 100.5240},
        {"name": "Bang Khen", "name_th": "บางเขน", "lat": 13.8740, "lon": 100.5930},
        {"name": "Bang Kapi", "name_th": "บางกะปิ", "lat": 13.7650, "lon": 100.6470},
        {"name": "Pathum Wan", "name_th": "ปทุมวัน", "lat": 13.7380, "lon": 100.5340},
        {"name": "Pom Prap Sattru Phai", "name_th": "ป้อมปราบศัตรูพ่าย", "lat": 13.7530, "lon": 100.5110},
        {"name": "Phra Khanong", "name_th": "พระโขนง", "lat": 13.7020, "lon": 100.6010},
        {"name": "Min Buri", "name_th": "มีนบุรี", "lat": 13.8120, "lon": 100.7530},
        {"name": "Lat Krabang", "name_th": "ลาดกระบัง", "lat": 13.7270, "lon": 100.7740},
        {"name": "Yan Nawa", "name_th": "ยานนาวา", "lat": 13.6930, "lon": 100.5430},
        {"name": "Samphanthawong", "name_th": "สัมพันธวงศ์", "lat": 13.7380, "lon": 100.5130},
        {"name": "Phaya Thai", "name_th": "พญาไท", "lat": 13.7780, "lon": 100.5410},
        {"name": "Thon Buri", "name_th": "ธนบุรี", "lat": 13.7220, "lon": 100.4870},
        {"name": "Bangkok Yai", "name_th": "บางกอกใหญ่", "lat": 13.7310, "lon": 100.4760},
        {"name": "Huai Khwang", "name_th": "ห้วยขวาง", "lat": 13.7770, "lon": 100.5800},
        {"name": "Khlong San", "name_th": "คลองสาน", "lat": 13.7270, "lon": 100.5050},
        {"name": "Taling Chan", "name_th": "ตลิ่งชัน", "lat": 13.7770, "lon": 100.4340},
        {"name": "Bangkok Noi", "name_th": "บางกอกน้อย", "lat": 13.7620, "lon": 100.4740},
        {"name": "Bang Khun Thian", "name_th": "บางขุนเทียน", "lat": 13.6060, "lon": 100.4350},
        {"name": "Phasi Charoen", "name_th": "ภาษีเจริญ", "lat": 13.7140, "lon": 100.4370},
        {"name": "Nong Khaem", "name_th": "หนองแขม", "lat": 13.7060, "lon": 100.3490},
        {"name": "Rat Burana", "name_th": "ราษฎร์บูรณะ", "lat": 13.6730, "lon": 100.5020},
        {"name": "Bang Phlat", "name_th": "บางพลัด", "lat": 13.7890, "lon": 100.4870},
        {"name": "Din Daeng", "name_th": "ดินแดง", "lat": 13.7720, "lon": 100.5580},
        {"name": "Bueng Kum", "name_th": "บึงกุ่ม", "lat": 13.8100, "lon": 100.6520},
        {"name": "Sathon", "name_th": "สาทร", "lat": 13.7180, "lon": 100.5280},
        {"name": "Bang Sue", "name_th": "บางซื่อ", "lat": 13.8060, "lon": 100.5280},
        {"name": "Chatuchak", "name_th": "จตุจักร", "lat": 13.8300, "lon": 100.5590},
        {"name": "Bang Kho Laem", "name_th": "บางคอแหลม", "lat": 13.6930, "lon": 100.5090},
        {"name": "Prawet", "name_th": "ประเวศ", "lat": 13.7160, "lon": 100.6940},
        {"name": "Khlong Toei", "name_th": "คลองเตย", "lat": 13.7080, "lon": 100.5720},
        {"name": "Suan Luang", "name_th": "สวนหลวง", "lat": 13.7250, "lon": 100.6320},
        {"name": "Chom Thong", "name_th": "จอมทอง", "lat": 13.6800, "lon": 100.4580},
        {"name": "Don Mueang", "name_th": "ดอนเมือง", "lat": 13.9280, "lon": 100.5930},
        {"name": "Ratchathewi", "name_th": "ราชเทวี", "lat": 13.7580, "lon": 100.5350},
        {"name": "Lat Phrao", "name_th": "ลาดพร้าว", "lat": 13.8060, "lon": 100.6020},
        {"name": "Watthana", "name_th": "วัฒนา", "lat": 13.7370, "lon": 100.5780},
        {"name": "Bang Khae", "name_th": "บางแค", "lat": 13.7130, "lon": 100.3900},
        {"name": "Lak Si", "name_th": "หลักสี่", "lat": 13.8870, "lon": 100.5680},
        {"name": "Sai Mai", "name_th": "สายไหม", "lat": 13.9180, "lon": 100.6470},
        {"name": "Khan Na Yao", "name_th": "คันนายาว", "lat": 13.8230, "lon": 100.6870},
        {"name": "Saphan Sung", "name_th": "สะพานสูง", "lat": 13.7700, "lon": 100.7050},
        {"name": "Wang Thonglang", "name_th": "วังทองหลาง", "lat": 13.7830, "lon": 100.6100},
        {"name": "Khlong Sam Wa", "name_th": "คลองสามวา", "lat": 13.8680, "lon": 100.7230},
        {"name": "Bang Na", "name_th": "บางนา", "lat": 13.6680, "lon": 100.6240},
        {"name": "Thawi Watthana", "name_th": "ทวีวัฒนา", "lat": 13.7730, "lon": 100.3560},
        {"name": "Thung Khru", "name_th": "ทุ่งครุ", "lat": 13.6310, "lon": 100.5050},
        {"name": "Bang Bon", "name_th": "บางบอน", "lat": 13.6580, "lon": 100.3780},
    ]
    
    # Create approximate polygon boundaries using buffered points
    # Each district gets a ~2km radius hexagonal approximation
    features = []
    for d in districts:
        # Create a simple polygon (approximate hexagon) around centroid
        # Radius varies by district (inner city smaller, outer larger)
        dist_from_center = ((d['lat'] - 13.75)**2 + (d['lon'] - 100.52)**2)**0.5
        radius = 0.015 + dist_from_center * 0.03  # degrees, roughly 1.5-4 km
        
        # Generate hexagonal boundary
        import math
        coords = []
        for i in range(6):
            angle = math.pi / 3 * i + math.pi / 6
            lat = d['lat'] + radius * math.sin(angle)
            lon = d['lon'] + radius * math.cos(angle) / math.cos(math.radians(d['lat']))
            coords.append([lon, lat])
        coords.append(coords[0])  # Close the polygon
        
        feature = {
            "type": "Feature",
            "properties": {
                "NAME_2": d["name"],
                "NL_NAME_2": d["name_th"],
                "NAME_1": "Bangkok",
                "TYPE_2": "Khet",
                "centroid_lat": d["lat"],
                "centroid_lon": d["lon"],
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }
        features.append(feature)
    
    result = {
        "type": "FeatureCollection",
        "name": "Bangkok Districts",
        "features": features
    }
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Created synthetic boundaries for {len(features)} Bangkok districts")
    print(f"Saved to {OUTPUT_PATH}")
    return True


def main():
    print(f"Output: {OUTPUT_PATH}")
    print(f"GEE Key: {GEE_KEY_PATH}")
    print()
    
    # Strategy 1: Try GEE
    if os.path.exists(GEE_KEY_PATH):
        print("=== Trying Google Earth Engine ===")
        if try_gee():
            return
    else:
        print("GEE key not found, skipping GEE")
    
    # Strategy 2: Try GADM download
    print("\n=== Trying GADM Download ===")
    if try_gadm_download():
        return
    
    # Strategy 3: Try Overpass/OSM
    print("\n=== Trying OpenStreetMap ===")
    if try_overpass_api():
        return
    
    # Strategy 4: Create synthetic boundaries (always works)
    print("\n=== Creating Synthetic Boundaries ===")
    create_synthetic_districts()


if __name__ == '__main__':
    import urllib.parse
    main()
