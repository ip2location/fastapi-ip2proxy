import os
import httpx
import IP2Proxy
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, List

class IP2ProxyMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, 
        app, 
        bin_path: Optional[str] = None, 
        api_key: Optional[str] = None,
        use_memory: bool = True,
        ip_headers: Optional[List[str]] = None,
        test_ip: Optional[str] = None,
        language: Optional[str] = None  # Added language parameter
    ):
        super().__init__(app)
        
        # Validation: Must have at least one method of lookup
        if not bin_path and not api_key:
            raise ValueError(
                "Configuration Error: You must provide either 'bin_path' (for local BIN file) "
                "or 'api_key' (for IP2Location.io API)."
            )
            
        self.db_path = bin_path
        self.api_key = api_key
        self.ip_headers = ip_headers or ["X-Forwarded-For", "X-Real-IP"]
        self.test_ip = test_ip
        self.language = language
        
        self.ip2pro_db = None
        self.http_client = None  # Placeholder for our HTTP connection pool
        
        # Initialize Local DB if a path is provided
        if self.db_path:
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"IP2Proxy database not found at {self.db_path}")
            try:
                # mode = "SHARED_MEMORY" if use_memory else "FILE_IO"
                # self.ip2pro_db = IP2Proxy.IP2Proxy(self.db_path)
                self.ip2pro_db = IP2Proxy.IP2Proxy()
                self.ip2pro_db.open(self.db_path)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize IP2Proxy database: {e}")

    def _get_client_ip(self, request: Request) -> str:
        """Extracts the real client IP, respecting proxy headers and test IPs."""
        client_ip = None
        
        # 1. Check Headers first
        for header in self.ip_headers:
            if header in request.headers:
                client_ip = request.headers[header].split(",")[0].strip()
                break
                
        # 2. Fallback to direct connection IP
        if not client_ip:
            client_ip = request.client.host if request.client else "127.0.0.1"

        # 3. OVERRIDE: If it's a local IP and a test_ip is provided, use the test_ip
        if self.test_ip and client_ip in ("127.0.0.1", "::1", "localhost"):
            return self.test_ip
            
        return client_ip

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        
        # Base proxy object
        proxy_data = {
            "ip": client_ip,
            "error": None
        }
        
        try:
            # 1. Prioritize Local DB if both are provided (faster, no network latency)
            if self.ip2pro_db:
                record = self.ip2pro_db.get_all(client_ip)
                proxy_data.update({
                    "is_proxy": record['is_proxy'] if 'is_proxy' in record else None,
                    "proxy_type": record['proxy_type'] if 'proxy_type' in record else None,
                    "country_short": record['country_short'] if 'country_short' in record else None,
                    "country_long": record['country_long'] if 'country_long' in record else None,
                    "region": record['region'] if 'region' in record else None,
                    "city": record['city'] if 'city' in record else None,
                    "isp": record['isp'] if 'isp' in record else None,
                    "domain": record['domain'] if 'domain' in record else None,
                    "usage_type": record['usage_type'] if 'usage_type' in record else None,
                    "asn": record['asn'] if 'asn' in record else None,
                    "as_name": record['as_name'] if 'as_name' in record else None,
                    "last_seen": record['last_seen'] if 'last_seen' in record else None,
                    "threat": record['threat'] if 'threat' in record else None,
                    "provider": record['provider'] if 'provider' in record else None,
                    "fraud_score": record['fraud_score'] if 'fraud_score' in record else None,
                })
                
            # 2. Fallback to API if DB is not configured
            elif self.api_key:
                # Initialize the httpx client once per application lifecycle (Connection Pooling)
                if self.http_client is None:
                    self.http_client = httpx.AsyncClient()
                
                # Construct the API URL
                api_url = f"https://api.ip2location.io/?key={self.api_key}&ip={client_ip}"
                
                # Append the language parameter if provided (ignored if free plan drops it)
                if self.language:
                    api_url += f"&lang={self.language}"
                
                # Make the non-blocking asynchronous request using the pooled client
                response = await self.http_client.get(api_url)
                response.raise_for_status()
                data = response.json()
                
                # Map API response keys to match our standard format
                proxy_data.update({
                    "country_short": data.get("country_code"),
                    "country_long": data.get("country_name"),
                    "region": data.get("region_name"),
                    "city": data.get("city_name"),
                    # "district": data.get("district"),
                    # "latitude": data.get("latitude"),
                    # "longitude": data.get("longitude"),
                    # "zipcode": data.get("zip_code"),
                    # "timezone": data.get("time_zone"),
                    "asn": data.get("asn"),
                    "as": data.get("as"),
                    "isp": data.get("isp"),
                    "domain": data.get("domain"),
                    # "net_speed": data.get("net_speed"),
                    # "idd_code": data.get("idd_code"),
                    # "area_code": data.get("area_code"),
                    # "weather_station_code": data.get("weather_station_code"),
                    # "weather_station_name": data.get("weather_station_name"),
                    # "mcc": data.get("mcc"),
                    # "mnc": data.get("mnc"),
                    # "mobile_brand": data.get("mobile_brand"),
                    # "elevation": data.get("elevation"),
                    "usage_type": data.get("usage_type"),
                    # "address_type": data.get("address_type"),
                    # "ads_category": data.get("ads_category"),
                    # "ads_category_name": data.get("ads_category_name"),
                    # AS info data
                    # "as_name": data.get("as_info", {}).get("as_name"),
                    # "as_number": data.get("as_info", {}).get("as_number"),
                    # "as_domain": data.get("as_info", {}).get("as_domain"),
                    # "as_cidr": data.get("as_info", {}).get("as_cidr"),
                    # "as_usage_type": data.get("as_info", {}).get("as_usage_type"),
                    # Continent data
                    # "continent_name": data.get("continent", {}).get("name"),
                    # "continent_code": data.get("continent", {}).get("code"),
                    # "continent_hemisphere": data.get("continent", {}).get("hemisphere"),
                    # "continent_translation": data.get("continent", {}).get("translation"),
                    # Country data
                    # "country_name": data.get("country", {}).get("name"),
                    # "country_alpha3_code": data.get("country", {}).get("alpha3_code"),
                    # "country_numeric_code": data.get("country", {}).get("numeric_code"),
                    # "country_demonym": data.get("country", {}).get("demonym"),
                    # "country_flag": data.get("country", {}).get("flag"),
                    # "country_capital": data.get("country", {}).get("capital"),
                    # "country_total_area": data.get("country", {}).get("total_area"),
                    # "country_population": data.get("country", {}).get("population"),
                    # "country_currency": data.get("country", {}).get("currency"),
                    # "country_language": data.get("country", {}).get("language"),
                    # "country_tld": data.get("country", {}).get("tld"),
                    # "country_translation": data.get("country", {}).get("translation"),
                    # Region data
                    # "region_name": data.get("region", {}).get("name"),
                    # "region_code": data.get("region", {}).get("code"),
                    # "region_translation": data.get("region", {}).get("translation"),
                    # City data
                    # "city_name": data.get("city", {}).get("name"),
                    # "city_translation": data.get("city", {}).get("translation"),
                    # Time Zone Info data
                    # "time_zone_olson": data.get("time_zone_info", {}).get("olson"),
                    # "time_zone_current_time": data.get("time_zone_info", {}).get("current_time"),
                    # "time_zone_gmt_offset": data.get("time_zone_info", {}).get("gmt_offset"),
                    # "time_zone_is_dst": data.get("time_zone_info", {}).get("is_dst"),
                    # "time_zone_abbreviation": data.get("time_zone_info", {}).get("abbreviation"),
                    # "time_zone_dst_start_date": data.get("time_zone_info", {}).get("dst_start_date"),
                    # "time_zone_dst_end_date": data.get("time_zone_info", {}).get("dst_end_date"),
                    # "time_zone_sunrise": data.get("time_zone_info", {}).get("sunrise"),
                    # "time_zone_sunset": data.get("time_zone_info", {}).get("sunset"),
                    # Geotargeting data
                    # "geotargeting_metro": data.get("geotargeting", {}).get("metro"),
                    "is_proxy": data.get("is_proxy"),
                    "fraud_score": data.get("fraud_score"),
                    # Proxy data
                    "proxy_last_seen": data.get("proxy", {}).get("last_seen"),
                    "proxy_type": data.get("proxy", {}).get("proxy_type"),
                    "proxy_threat": data.get("proxy", {}).get("threat"),
                    "proxy_provider": data.get("proxy", {}).get("provider"),
                    "proxy_is_vpn": data.get("proxy", {}).get("is_vpn"),
                    "proxy_is_tor": data.get("proxy", {}).get("is_tor"),
                    "proxy_is_data_center": data.get("proxy", {}).get("is_data_center"),
                    "proxy_is_public_proxy": data.get("proxy", {}).get("is_public_proxy"),
                    "proxy_is_web_proxy": data.get("proxy", {}).get("is_web_proxy"),
                    "proxy_is_web_crawler": data.get("proxy", {}).get("is_web_crawler"),
                    "proxy_is_ai_crawler": data.get("proxy", {}).get("is_ai_crawler"),
                    "proxy_is_residential_proxy": data.get("proxy", {}).get("is_residential_proxy"),
                    "proxy_is_spammer": data.get("proxy", {}).get("is_spammer"),
                    "proxy_is_scanner": data.get("proxy", {}).get("is_scanner"),
                    "proxy_is_botnet": data.get("proxy", {}).get("is_botnet"),
                    "proxy_is_bogon": data.get("proxy", {}).get("is_bogon"),
                    "proxy_is_consumer_privacy_network": data.get("proxy", {}).get("is_consumer_privacy_network"),
                    "proxy_is_enterprise_private_network": data.get("proxy", {}).get("is_enterprise_private_network"),
                })
                    
        except Exception as e:
            proxy_data["error"] = f"Lookup failed: {str(e)}"

        # Inject into the FastAPI request state with the generic 'proxy' key
        request.state.proxy = proxy_data

        # Continue the request lifecycle
        return await call_next(request)