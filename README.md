# FastAPI IP2Proxy Middleware — Proxy, VPN & IP Intelligence

[![PyPI version](https://img.shields.io/pypi/v/fastapi-ip2proxy.svg)](https://pypi.org/project/fastapi-ip2proxy/)
[![Python version](https://img.shields.io/pypi/pyversions/fastapi-ip2proxy.svg)](https://pypi.org/project/fastapi-ip2proxy/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.TXT)

FastAPI IP2Proxy Middleware (`fastapi-ip2proxy`) enables FastAPI applications to detect proxies, VPNs, Tor networks, data center IP addresses, and other IP-related security signals using the IP2Proxy database or IP2Location.io API.

The middleware automatically performs an IP lookup for incoming HTTP requests and makes the results available through `request.state.proxy`, allowing developers to integrate IP intelligence into their applications with minimal code.

Quick links: [IP2Proxy Database](https://www.ip2location.com/databases/ip2proxy) · [Free LITE Database](https://www.ip2location.com/database/lite) · [Get an API Key](https://www.ip2location.io/) · [API Documentation](https://www.ip2location.io/ip2location-documentation) · [PyPI Package](https://pypi.org/project/fastapi-ip2proxy/)

## Features

- **Proxy and VPN Detection:** Identify proxies, VPNs, Tor networks, residential proxies, and other network types.
- **Dual Lookup Modes:** Use a local IP2Proxy BIN database or the IP2Location.io API.
- **IPv4 and IPv6 Support:** Perform lookups for both IP address formats using a compatible data source.
- **IP and Network Intelligence:** Retrieve country, region, city, ISP, ASN, proxy type, fraud score, and other available attributes.
- **Asynchronous API Requests:** Uses `httpx` with connection pooling for non-blocking API lookups.
- **Reverse Proxy Support:** Supports configurable client IP headers for applications behind reverse proxies and load balancers.
- **Local Testing:** Override localhost IP addresses using the `test_ip` parameter.
- **Multilingual Support:** Retrieve localized place names through supported IP2Location.io API plans.
- **Error Handling:** Captures lookup exceptions in the request state for application-level handling.

Available fields depend on the selected database package or API subscription plan.

## Requirements

- Python 3.8 or later.
- FastAPI.
- At least one of the following data sources:
  - An IP2Proxy BIN database from [IP2Proxy](https://www.ip2location.com/databases/ip2proxy) or [IP2Location LITE](https://www.ip2location.com/database/lite).
  - An [IP2Location.io API key](https://www.ip2location.io/).
- Internet access when using API mode.

## Installation

Install the middleware using pip:

```bash
pip install fastapi-ip2proxy
```

Install Uvicorn if you do not already have an ASGI server:

```bash
pip install uvicorn
```

## Quick start

### 1. Using a local IP2Proxy database

Download and extract an IP2Proxy BIN database.

Create a Python file named `main.py` with the following code:

```python
from fastapi import FastAPI, Request
from fastapi_ip2proxy import IP2ProxyMiddleware

app = FastAPI()

app.add_middleware(
    IP2ProxyMiddleware,
    bin_path="IP2PROXY-LITE-PX12.BIN",
    test_ip="8.8.8.8"
)

@app.get("/")
async def get_proxy_info(request: Request):
    return request.state.proxy
```

Replace `bin_path` with the actual path to your downloaded BIN file.

The `test_ip` parameter allows you to test the middleware on localhost using a public IP address.

Local database mode does not require an external API request or API key.

### 2. Using the IP2Location.io API

Sign up for an API key at [IP2Location.io](https://www.ip2location.io/).

Set your API key as an environment variable.

Linux and macOS:

```bash
export IP2LOCATION_API_KEY="YOUR_API_KEY"
```

Windows PowerShell:

```powershell
$env:IP2LOCATION_API_KEY="YOUR_API_KEY"
```

Create a Python file named `main.py`:

```python
import os
from fastapi import FastAPI, Request
from fastapi_ip2proxy import IP2ProxyMiddleware

app = FastAPI()

app.add_middleware(
    IP2ProxyMiddleware,
    api_key=os.environ["IP2LOCATION_API_KEY"],
    test_ip="8.8.8.8"
)

@app.get("/")
async def get_proxy_info(request: Request):
    return request.state.proxy
```

Refer to the [IP2Location.io pricing page](https://www.ip2location.io/pricing) for available features and API query limits.

### 3. Run the application

Start the FastAPI application using Uvicorn:

```bash
uvicorn main:app --reload
```

Open the following URL in your browser:

```
http://127.0.0.1:8000/
```

Alternatively, test the endpoint using curl:

```bash
curl http://127.0.0.1:8000/
```

The application returns the available proxy and IP intelligence data for the detected IP address or the configured test IP.

## Configuration

The `IP2ProxyMiddleware` class supports the following configuration parameters:

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `bin_path` | str | None | Path to the local IP2Proxy BIN database. |
| `api_key` | str | None | IP2Location.io API key. |
| `ip_headers` | list | X-Forwarded-For, X-Real-IP | HTTP headers checked in order to obtain the client IP address. |
| `test_ip` | str | None | IP address used in place of localhost for testing. |
| `language` | str | None | Language code for localized results in supported API plans. |

At least one of `bin_path` or `api_key` must be provided.

If both are configured, the middleware prioritizes the local database. The API is used when no local database is configured; it is not automatically used as a fallback when a database lookup fails.

### Custom configuration

```python
app.add_middleware(
    IP2ProxyMiddleware,
    bin_path="IP2PROXY-LITE-PX12.BIN",
    ip_headers=[
        "X-Forwarded-For",
        "X-Real-IP",
        "CF-Connecting-IP"
    ],
    test_ip="8.8.8.8"
)
```

## Response example

The middleware makes the lookup results available through `request.state.proxy`.

Example of selected response fields in API mode:

```json
{
    "ip": "8.8.8.8",
    "country_short": "US",
    "country_long": "United States",
    "asn": "15169",
    "as": "Google LLC",
    "is_proxy": false,
    "error": null
}
```

This is an illustrative response. Actual values and available fields depend on the IP address and data source.

### Common response fields

| Field | Description |
| --- | --- |
| `ip` | IP address used for the lookup. |
| `is_proxy` | Proxy detection status. |
| `proxy_type` | Type of proxy or network detected. |
| `country_short` | Two-letter country code. |
| `country_long` | Country name. |
| `region` | Region or state name. |
| `city` | City name. |
| `isp` | Internet service provider. |
| `domain` | Domain associated with the IP address. |
| `usage_type` | IP address usage classification. |
| `asn` | Autonomous system number. |
| `fraud_score` | IP-related fraud risk score, when available. |
| `error` | Lookup error message, or null if no exception occurred. |

Additional attributes, including proxy provider, threat information, and VPN or Tor indicators, may be available depending on the data source.

Some field names and value types differ between local database and API modes.

In particular, `is_proxy` is an integer status in database mode and normally a boolean in API mode. Refer to the corresponding data source documentation before applying security rules.

## Error handling

If a lookup raises an exception, the middleware records the error in `request.state.proxy["error"]` and continues processing the request.

Applications should handle lookup failures according to their requirements.

Invalid middleware configuration or an unavailable database file may cause application initialization to fail.

## Common use cases

- **Fraud Prevention:** Incorporate IP intelligence into transaction and account risk assessments.
- **API Security:** Identify requests originating from suspicious proxy networks.
- **Access Control:** Apply additional verification based on IP-related security signals.
- **Bot Detection:** Identify known crawler networks and automated traffic indicators.
- **Traffic Analytics:** Analyze visitor network types and proxy usage.

## Security considerations

- Only trust client IP headers supplied by a trusted reverse proxy or load balancer. Untrusted clients may spoof these headers.
- Configure your infrastructure to remove or overwrite untrusted incoming client IP headers.
- Remove the `test_ip` parameter when deploying to production.
- Store API keys securely using environment variables.
- Keep your local IP2Proxy database updated regularly.
- Use proxy detection as one of several risk signals rather than definitive evidence of malicious activity.
- Avoid exposing detailed lookup errors or sensitive network information in public production endpoints.

## Documentation and support

- [IP2Proxy Database](https://www.ip2location.com/databases/ip2proxy)
- [IP2Location LITE Database](https://www.ip2location.com/database/lite)
- [IP2Proxy Python Library](https://github.com/ip2location/ip2proxy-python)
- [IP2Location.io API Documentation](https://www.ip2location.io/ip2location-documentation)
- [IP2Location.io Pricing](https://www.ip2location.io/pricing)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyPI Package](https://pypi.org/project/fastapi-ip2proxy/)
- [GitHub Issues](https://github.com/ip2location/fastapi-ip2proxy/issues)

## License

Licensed under the MIT License. See [LICENSE](LICENSE.TXT).
