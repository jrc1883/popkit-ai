#!/usr/bin/env python3
"""
Cloudflare API Client

Client for Cloudflare API - Workers, Pages, DNS management.
Part of PopKit Issue #222 (Cloudflare Integration Skills).
"""

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

# =============================================================================
# CONFIGURATION
# =============================================================================

CLOUDFLARE_API_URL = "https://api.cloudflare.com/client/v4"

# Rate limiting (Cloudflare API limits: 1200 requests per 5 minutes)
MAX_REQUESTS_PER_MINUTE = 200
REQUEST_COOLDOWN = 0.3  # seconds between requests


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Zone:
    """Cloudflare Zone (domain)."""

    id: str
    name: str
    status: str
    account_id: str
    plan: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Zone":
        return cls(
            id=data["id"],
            name=data["name"],
            status=data["status"],
            account_id=data.get("account", {}).get("id", ""),
            plan=data.get("plan", {}),
        )


@dataclass
class DNSRecord:
    """Cloudflare DNS Record."""

    id: str
    zone_id: str
    name: str
    type: str
    content: str
    proxied: bool = False
    ttl: int = 1  # 1 = automatic
    comment: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DNSRecord":
        return cls(
            id=data["id"],
            zone_id=data.get("zone_id", ""),
            name=data["name"],
            type=data["type"],
            content=data["content"],
            proxied=data.get("proxied", False),
            ttl=data.get("ttl", 1),
            comment=data.get("comment"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to API request format."""
        result = {
            "type": self.type,
            "name": self.name,
            "content": self.content,
            "proxied": self.proxied,
            "ttl": self.ttl,
        }
        if self.comment:
            result["comment"] = self.comment
        return result


@dataclass
class Worker:
    """Cloudflare Worker."""

    id: str
    name: str
    created_on: str
    modified_on: str
    routes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Worker":
        return cls(
            id=data.get("id", data.get("name", "")),
            name=data.get("name", ""),
            created_on=data.get("created_on", ""),
            modified_on=data.get("modified_on", ""),
            routes=data.get("routes", []),
        )


@dataclass
class Deployment:
    """Cloudflare Worker Deployment."""

    id: str
    version_id: str
    source: str
    created_on: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Deployment":
        return cls(
            id=data.get("id", ""),
            version_id=data.get("version_id", ""),
            source=data.get("source", ""),
            created_on=data.get("created_on", ""),
        )


@dataclass
class APIResponse:
    """Generic Cloudflare API response."""

    success: bool
    result: Any
    errors: list[dict[str, Any]] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)


# =============================================================================
# CLOUDFLARE CLIENT
# =============================================================================


class CloudflareClient:
    """
    Client for Cloudflare API.

    Features:
    - Automatic API key from environment
    - Zone management (list, get)
    - DNS record CRUD
    - Worker management
    - Rate limiting
    - Retry with backoff
    """

    def __init__(self, api_token: str | None = None, account_id: str | None = None):
        """
        Initialize Cloudflare client.

        Args:
            api_token: Cloudflare API token (defaults to CLOUDFLARE_API_TOKEN env var)
            account_id: Cloudflare account ID (defaults to CLOUDFLARE_ACCOUNT_ID env var)
        """
        self.api_token = api_token or os.environ.get("CLOUDFLARE_API_TOKEN")
        self.account_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        self._last_request_time = 0.0
        self._request_count = 0
        self._request_reset_time = time.time()

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def is_available(self) -> bool:
        """Check if API token is configured."""
        return bool(self.api_token)

    # =========================================================================
    # ZONE MANAGEMENT
    # =========================================================================

    def list_zones(self) -> list[Zone]:
        """
        List all zones (domains) in the account.

        Returns:
            List of Zone objects
        """
        response = self._request("GET", "/zones")
        return [Zone.from_dict(z) for z in response.result]

    def get_zone(self, zone_id: str) -> Zone:
        """
        Get a specific zone by ID.

        Args:
            zone_id: Zone ID

        Returns:
            Zone object
        """
        response = self._request("GET", f"/zones/{zone_id}")
        return Zone.from_dict(response.result)

    def get_zone_by_name(self, domain: str) -> Zone | None:
        """
        Find a zone by domain name.

        Args:
            domain: Domain name (e.g., "example.com")

        Returns:
            Zone object or None if not found
        """
        response = self._request("GET", f"/zones?name={domain}")
        if response.result:
            return Zone.from_dict(response.result[0])
        return None

    # =========================================================================
    # DNS MANAGEMENT
    # =========================================================================

    def list_dns_records(
        self, zone_id: str, record_type: str | None = None, name: str | None = None
    ) -> list[DNSRecord]:
        """
        List DNS records for a zone.

        Args:
            zone_id: Zone ID
            record_type: Filter by type (A, CNAME, TXT, etc.)
            name: Filter by record name

        Returns:
            List of DNSRecord objects
        """
        params = []
        if record_type:
            params.append(f"type={record_type}")
        if name:
            params.append(f"name={name}")

        query = f"?{'&'.join(params)}" if params else ""
        response = self._request("GET", f"/zones/{zone_id}/dns_records{query}")
        return [DNSRecord.from_dict(r) for r in response.result]

    def get_dns_record(self, zone_id: str, record_id: str) -> DNSRecord:
        """
        Get a specific DNS record.

        Args:
            zone_id: Zone ID
            record_id: DNS record ID

        Returns:
            DNSRecord object
        """
        response = self._request("GET", f"/zones/{zone_id}/dns_records/{record_id}")
        return DNSRecord.from_dict(response.result)

    def create_dns_record(
        self,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        proxied: bool = True,
        ttl: int = 1,
        comment: str | None = None,
    ) -> DNSRecord:
        """
        Create a DNS record.

        Args:
            zone_id: Zone ID
            record_type: Record type (A, CNAME, TXT, MX, etc.)
            name: Record name (subdomain or @ for root)
            content: Record content (IP, domain, text)
            proxied: Enable Cloudflare proxy (orange cloud)
            ttl: TTL in seconds (1 = automatic)
            comment: Optional comment

        Returns:
            Created DNSRecord object
        """
        data = {
            "type": record_type,
            "name": name,
            "content": content,
            "proxied": proxied,
            "ttl": ttl,
        }
        if comment:
            data["comment"] = comment

        response = self._request("POST", f"/zones/{zone_id}/dns_records", data)
        return DNSRecord.from_dict(response.result)

    def update_dns_record(
        self,
        zone_id: str,
        record_id: str,
        record_type: str | None = None,
        name: str | None = None,
        content: str | None = None,
        proxied: bool | None = None,
        ttl: int | None = None,
        comment: str | None = None,
    ) -> DNSRecord:
        """
        Update a DNS record.

        Args:
            zone_id: Zone ID
            record_id: DNS record ID
            record_type: New type (optional)
            name: New name (optional)
            content: New content (optional)
            proxied: New proxy status (optional)
            ttl: New TTL (optional)
            comment: New comment (optional)

        Returns:
            Updated DNSRecord object
        """
        # Get existing record to preserve unchanged fields
        existing = self.get_dns_record(zone_id, record_id)

        data = {
            "type": record_type or existing.type,
            "name": name or existing.name,
            "content": content or existing.content,
            "proxied": proxied if proxied is not None else existing.proxied,
            "ttl": ttl if ttl is not None else existing.ttl,
        }
        if comment is not None:
            data["comment"] = comment
        elif existing.comment:
            data["comment"] = existing.comment

        response = self._request("PUT", f"/zones/{zone_id}/dns_records/{record_id}", data)
        return DNSRecord.from_dict(response.result)

    def delete_dns_record(self, zone_id: str, record_id: str) -> bool:
        """
        Delete a DNS record.

        Args:
            zone_id: Zone ID
            record_id: DNS record ID

        Returns:
            True if deleted successfully
        """
        response = self._request("DELETE", f"/zones/{zone_id}/dns_records/{record_id}")
        return response.success

    # =========================================================================
    # WORKER MANAGEMENT
    # =========================================================================

    def list_workers(self) -> list[Worker]:
        """
        List all Workers in the account.

        Returns:
            List of Worker objects
        """
        if not self.account_id:
            raise ValueError("CLOUDFLARE_ACCOUNT_ID required for Worker operations")

        response = self._request("GET", f"/accounts/{self.account_id}/workers/scripts")
        return [Worker.from_dict(w) for w in response.result]

    def get_worker(self, worker_name: str) -> Worker:
        """
        Get a specific Worker.

        Args:
            worker_name: Worker script name

        Returns:
            Worker object
        """
        if not self.account_id:
            raise ValueError("CLOUDFLARE_ACCOUNT_ID required for Worker operations")

        response = self._request(
            "GET", f"/accounts/{self.account_id}/workers/scripts/{worker_name}"
        )
        return Worker.from_dict(response.result)

    def get_worker_deployments(self, worker_name: str) -> list[Deployment]:
        """
        Get deployment history for a Worker.

        Args:
            worker_name: Worker script name

        Returns:
            List of Deployment objects
        """
        if not self.account_id:
            raise ValueError("CLOUDFLARE_ACCOUNT_ID required for Worker operations")

        response = self._request(
            "GET", f"/accounts/{self.account_id}/workers/scripts/{worker_name}/deployments"
        )
        return [Deployment.from_dict(d) for d in response.result.get("deployments", [])]

    # =========================================================================
    # VERIFICATION
    # =========================================================================

    def verify_token(self) -> tuple[bool, str]:
        """
        Verify API token is valid.

        Returns:
            (success, message) tuple
        """
        try:
            response = self._request("GET", "/user/tokens/verify")
            return response.success, "Token is valid"
        except RuntimeError as e:
            return False, str(e)

    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================

    def _request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> APIResponse:
        """
        Make API request to Cloudflare.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/zones")
            data: Request body for POST/PUT

        Returns:
            APIResponse object

        Raises:
            ValueError: If API token not set
            RuntimeError: If API call fails
        """
        if not self.api_token:
            raise ValueError(
                "CLOUDFLARE_API_TOKEN not set. "
                "Set environment variable or pass api_token to constructor."
            )

        # Rate limiting
        self._wait_for_rate_limit()

        url = f"{CLOUDFLARE_API_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}

        body = json.dumps(data).encode("utf-8") if data else None

        request = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return APIResponse(
                    success=result.get("success", True),
                    result=result.get("result"),
                    errors=result.get("errors", []),
                    messages=result.get("messages", []),
                )
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8") if e.fp else ""
            try:
                error_data = json.loads(body_text)
                errors = error_data.get("errors", [])
                error_msg = errors[0].get("message") if errors else e.reason
            except json.JSONDecodeError:
                error_msg = e.reason

            raise RuntimeError(f"Cloudflare API error {e.code}: {error_msg}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")

    def _wait_for_rate_limit(self) -> None:
        """Wait if rate limit would be exceeded."""
        now = time.time()

        # Reset counter every minute
        if now - self._request_reset_time > 60:
            self._request_count = 0
            self._request_reset_time = now

        # Check rate limit
        if self._request_count >= MAX_REQUESTS_PER_MINUTE:
            wait_time = 60 - (now - self._request_reset_time)
            if wait_time > 0:
                time.sleep(wait_time)
            self._request_count = 0
            self._request_reset_time = time.time()

        # Enforce cooldown between requests
        elapsed = now - self._last_request_time
        if elapsed < REQUEST_COOLDOWN:
            time.sleep(REQUEST_COOLDOWN - elapsed)

        self._last_request_time = time.time()
        self._request_count += 1


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

_client: CloudflareClient | None = None


def get_client() -> CloudflareClient:
    """Get or create the singleton Cloudflare client."""
    global _client
    if _client is None:
        _client = CloudflareClient()
    return _client


def list_zones() -> list[Zone]:
    """List all zones."""
    return get_client().list_zones()


def get_zone_by_name(domain: str) -> Zone | None:
    """Get zone by domain name."""
    return get_client().get_zone_by_name(domain)


def list_dns_records(zone_id: str, record_type: str | None = None) -> list[DNSRecord]:
    """List DNS records for a zone."""
    return get_client().list_dns_records(zone_id, record_type)


def create_dns_record(
    zone_id: str,
    record_type: str,
    name: str,
    content: str,
    proxied: bool = True,
    comment: str | None = None,
) -> DNSRecord:
    """Create a DNS record."""
    return get_client().create_dns_record(
        zone_id, record_type, name, content, proxied, comment=comment
    )


def delete_dns_record(zone_id: str, record_id: str) -> bool:
    """Delete a DNS record."""
    return get_client().delete_dns_record(zone_id, record_id)


def list_workers() -> list[Worker]:
    """List all Workers."""
    return get_client().list_workers()


def is_available() -> bool:
    """Check if Cloudflare API is available."""
    return get_client().is_available


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys

    print("Cloudflare Client Test")
    print("=" * 40)

    client = CloudflareClient()

    from popkit_shared.utils.secure_logger import secure_print

    if not client.is_available:
        secure_print("ERROR: CLOUDFLARE_API_TOKEN not set")
        secure_print("Set: export CLOUDFLARE_API_TOKEN=your-token-here")
        sys.exit(1)

    secure_print("API Token: [REDACTED]")

    # Verify token
    secure_print("\nVerifying token...")
    valid, message = client.verify_token()
    print(f"Valid: {valid} - {message}")

    if not valid:
        sys.exit(1)

    # List zones
    print("\nListing zones...")
    zones = client.list_zones()
    for zone in zones:
        print(f"  - {zone.name} (ID: {zone.id})")

    if zones:
        # List DNS records for first zone
        zone = zones[0]
        print(f"\nDNS records for {zone.name}...")
        records = client.list_dns_records(zone.id)
        for record in records[:5]:  # Show first 5
            proxy_icon = "(proxied)" if record.proxied else ""
            print(f"  - {record.type:6} {record.name:40} {record.content} {proxy_icon}")

    print("\nAll tests passed!")
