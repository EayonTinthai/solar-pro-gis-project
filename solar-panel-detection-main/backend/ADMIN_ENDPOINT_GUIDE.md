# Admin Data Quality Endpoint - Quick Reference Guide

## Overview
The `/admin/data-quality` endpoint provides comprehensive data quality metrics for monitoring the health of the building dataset. This endpoint requires API key authentication.

## Setup

### 1. Configure API Keys

Add admin API keys to your environment:

```bash
# .env file
ADMIN_API_KEYS=your_secret_key_1,your_secret_key_2,your_secret_key_3
```

Or set as environment variable:

```bash
export ADMIN_API_KEYS="key1,key2,key3"
```

### 2. Generate Secure API Keys

Use a secure method to generate API keys:

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

## Usage

### Basic Request

```bash
curl -H "X-API-Key: your_secret_key_1" \
     https://your-api-domain.com/admin/data-quality
```

### Python Example

```python
import requests

API_KEY = "your_secret_key_1"
API_URL = "https://your-api-domain.com/admin/data-quality"

headers = {
    "X-API-Key": API_KEY
}

response = requests.get(API_URL, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f"Total Buildings: {data['total_buildings']:,}")
    print(f"Low Confidence: {data['low_confidence_percentage']:.2f}%")
    print(f"Data Age: {data['data_freshness_days']} days")
    print(f"Status: {data['validation_status']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const API_KEY = 'your_secret_key_1';
const API_URL = 'https://your-api-domain.com/admin/data-quality';

async function getDataQuality() {
  try {
    const response = await axios.get(API_URL, {
      headers: {
        'X-API-Key': API_KEY
      }
    });
    
    const data = response.data;
    console.log(`Total Buildings: ${data.total_buildings.toLocaleString()}`);
    console.log(`Low Confidence: ${data.low_confidence_percentage.toFixed(2)}%`);
    console.log(`Data Age: ${data.data_freshness_days} days`);
    console.log(`Status: ${data.validation_status}`);
    
    // Regional breakdown
    console.log('\nQuality by Region:');
    data.quality_by_region.forEach(region => {
      console.log(`  ${region.region}: ${region.quality_flag} (${region.avg_confidence.toFixed(3)})`);
    });
    
  } catch (error) {
    if (error.response) {
      console.error(`Error: ${error.response.status} - ${error.response.data.detail}`);
    } else {
      console.error(`Error: ${error.message}`);
    }
  }
}

getDataQuality();
```

## Response Format

```json
{
  "total_buildings": 107682789,
  "low_confidence_count": 12456789,
  "low_confidence_percentage": 11.57,
  "data_freshness_days": 1037,
  "validation_status": "needs_attention",
  "quality_by_region": [
    {
      "region": "Bangkok Metropolitan",
      "total": 2345678,
      "avg_confidence": 0.856,
      "quality_flag": "high"
    },
    {
      "region": "Northern Thailand",
      "total": 15234567,
      "avg_confidence": 0.782,
      "quality_flag": "medium"
    },
    {
      "region": "Central Thailand",
      "total": 45678901,
      "avg_confidence": 0.791,
      "quality_flag": "medium"
    },
    {
      "region": "Southern Thailand",
      "total": 44201443,
      "avg_confidence": 0.768,
      "quality_flag": "medium"
    }
  ],
  "generated_at": "2026-04-17T15:30:00.123456"
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `total_buildings` | integer | Total number of buildings in dataset |
| `low_confidence_count` | integer | Number of buildings with confidence < 0.7 |
| `low_confidence_percentage` | float | Percentage of low confidence buildings |
| `data_freshness_days` | integer | Days since data was collected |
| `validation_status` | string | Overall health: "healthy", "acceptable", or "needs_attention" |
| `quality_by_region` | array | Quality metrics broken down by region |
| `generated_at` | string | ISO 8601 timestamp of when report was generated |

### Validation Status Thresholds

- **healthy**: < 10% low confidence AND < 180 days old
- **acceptable**: < 20% low confidence AND < 365 days old  
- **needs_attention**: Exceeds acceptable thresholds

### Quality Flag (per region)

- **high**: Average confidence >= 0.8
- **medium**: Average confidence >= 0.7 and < 0.8
- **low**: Average confidence < 0.7

## Error Responses

### 401 Unauthorized - Missing API Key

```json
{
  "detail": "Missing API key. Provide X-API-Key header."
}
```

### 401 Unauthorized - Invalid API Key

```json
{
  "detail": "Invalid API key"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Data quality query error: [error details]"
}
```

## Caching

- The endpoint is cached for **1 hour** (3600 seconds)
- Cache headers are included in the response:
  - `X-Cache-Status`: "HIT" or "MISS"
  - `Cache-Control`: "public, max-age=3600"

## Monitoring Dashboard Example

Here's a simple monitoring dashboard using the endpoint:

```python
import requests
import time
from datetime import datetime

def monitor_data_quality(api_key, interval_minutes=60):
    """Monitor data quality and alert on issues"""
    
    url = "https://your-api-domain.com/admin/data-quality"
    headers = {"X-API-Key": api_key}
    
    while True:
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] Data Quality Report")
            print("=" * 60)
            
            # Overall metrics
            print(f"Total Buildings: {data['total_buildings']:,}")
            print(f"Low Confidence: {data['low_confidence_percentage']:.2f}%")
            print(f"Data Age: {data['data_freshness_days']} days")
            print(f"Status: {data['validation_status'].upper()}")
            
            # Alert on issues
            if data['validation_status'] == 'needs_attention':
                print("\n⚠️  ALERT: Data quality needs attention!")
                
                if data['low_confidence_percentage'] > 20:
                    print(f"   - High percentage of low confidence buildings: {data['low_confidence_percentage']:.2f}%")
                
                if data['data_freshness_days'] > 365:
                    print(f"   - Data is stale: {data['data_freshness_days']} days old")
            
            # Regional issues
            low_quality_regions = [
                r for r in data['quality_by_region'] 
                if r['quality_flag'] == 'low'
            ]
            
            if low_quality_regions:
                print("\n⚠️  Low quality regions:")
                for region in low_quality_regions:
                    print(f"   - {region['region']}: {region['avg_confidence']:.3f}")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"Error fetching data quality: {e}")
        
        # Wait before next check
        time.sleep(interval_minutes * 60)

# Run monitor
if __name__ == "__main__":
    API_KEY = "your_secret_key_1"
    monitor_data_quality(API_KEY, interval_minutes=60)
```

## Security Best Practices

1. **Never commit API keys to version control**
   - Use environment variables
   - Use secrets management services (AWS Secrets Manager, GCP Secret Manager, etc.)

2. **Rotate API keys regularly**
   - Generate new keys periodically
   - Remove old keys from environment

3. **Use HTTPS only**
   - Never send API keys over unencrypted connections

4. **Limit API key distribution**
   - Only share with authorized personnel
   - Use different keys for different teams/purposes

5. **Monitor API key usage**
   - Check audit logs regularly
   - Look for suspicious patterns

## Audit Trail

All queries to the `/admin/data-quality` endpoint are logged with:
- Timestamp
- Truncated API key (first 8 characters)
- Query details
- Success/failure status

Check application logs for audit trail:

```bash
# Example log entries
2026-04-17 15:30:00 INFO Data quality query initiated by API key: test_key...
2026-04-17 15:30:00 INFO Querying total buildings count
2026-04-17 15:30:01 INFO Querying low confidence buildings
2026-04-17 15:30:02 INFO Querying quality by region
2026-04-17 15:30:03 INFO Data quality query completed successfully
```

## Troubleshooting

### Issue: 401 Unauthorized

**Solution**: Check that:
1. API key is set in environment: `echo $ADMIN_API_KEYS`
2. API key is included in request header: `X-API-Key: your_key`
3. API key matches one in the environment variable

### Issue: Slow response times

**Solution**: 
1. Check if cache is working (look for `X-Cache-Status: HIT`)
2. Verify BigQuery performance
3. Consider increasing cache TTL if data doesn't change frequently

### Issue: Unexpected validation_status

**Solution**: Review the thresholds:
- Check `low_confidence_percentage` against 10% and 20% thresholds
- Check `data_freshness_days` against 180 and 365 day thresholds

## Support

For issues or questions:
1. Check application logs for detailed error messages
2. Verify environment configuration
3. Review API documentation at `/docs`
4. Contact system administrator

---

**Last Updated**: April 17, 2026
**API Version**: 2.2.0
