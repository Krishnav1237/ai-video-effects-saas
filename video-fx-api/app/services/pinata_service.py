"""IPFS pinning service via Pinata for decentralized video storage."""

import os
import httpx

PINATA_API_KEY = os.getenv("PINATA_API_KEY", "")
PINATA_SECRET_KEY = os.getenv("PINATA_SECRET_KEY", "")
PINATA_JWT = os.getenv("PINATA_JWT", "")
PINATA_GATEWAY = os.getenv("PINATA_GATEWAY", "https://gateway.pinata.cloud/ipfs")

PINATA_API_URL = "https://api.pinata.cloud"


def _get_headers() -> dict[str, str]:
    """Get authentication headers for Pinata API."""
    if PINATA_JWT:
        return {"Authorization": f"Bearer {PINATA_JWT}"}
    return {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_KEY,
    }


async def pin_file(file_path: str, name: str | None = None) -> dict:
    """Pin a file to IPFS via Pinata."""
    if not PINATA_JWT and not PINATA_API_KEY:
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        demo_cid = f"QmDemo{os.path.basename(file_path).replace('.', '')[:20]}xyz"
        return {
            "status": "demo_mode",
            "message": "Pinata credentials not configured. Returning demo response.",
            "IpfsHash": demo_cid,
            "PinSize": file_size,
            "Timestamp": "2026-01-01T00:00:00.000Z",
            "ipfs_url": f"{PINATA_GATEWAY}/{demo_cid}",
        }

    headers = _get_headers()
    metadata = {"name": name or os.path.basename(file_path)}

    async with httpx.AsyncClient(timeout=300.0) as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                f"{PINATA_API_URL}/pinning/pinFileToIPFS",
                headers=headers,
                files={"file": (os.path.basename(file_path), f)},
                data={"pinataMetadata": str(metadata)},
            )

        if response.status_code == 200:
            data = response.json()
            data["ipfs_url"] = f"{PINATA_GATEWAY}/{data['IpfsHash']}"
            return data
        return {
            "status": "error",
            "error": f"Pinata API returned {response.status_code}: {response.text}",
        }


async def get_pin_info(cid: str) -> dict:
    """Get information about a pinned file."""
    if not PINATA_JWT and not PINATA_API_KEY:
        return {
            "status": "demo_mode",
            "cid": cid,
            "ipfs_url": f"{PINATA_GATEWAY}/{cid}",
            "pin_status": "pinned",
            "size_bytes": 0,
        }

    headers = _get_headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{PINATA_API_URL}/data/pinList?hashContains={cid}",
            headers=headers,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("rows"):
                pin = data["rows"][0]
                return {
                    "cid": cid,
                    "ipfs_url": f"{PINATA_GATEWAY}/{cid}",
                    "pin_status": "pinned",
                    "size_bytes": pin.get("size", 0),
                    "date_pinned": pin.get("date_pinned"),
                    "metadata": pin.get("metadata"),
                }
            return {"cid": cid, "pin_status": "not_found"}
        return {"status": "error", "error": f"API returned {response.status_code}"}


async def unpin_file(cid: str) -> dict:
    """Unpin a file from IPFS."""
    if not PINATA_JWT and not PINATA_API_KEY:
        return {"status": "demo_mode", "message": "File unpinned (demo)", "cid": cid}

    headers = _get_headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.delete(
            f"{PINATA_API_URL}/pinning/unpin/{cid}",
            headers=headers,
        )
        if response.status_code == 200:
            return {"status": "unpinned", "cid": cid}
        return {"status": "error", "error": f"API returned {response.status_code}"}


async def test_connection() -> dict:
    """Test Pinata API connection."""
    if not PINATA_JWT and not PINATA_API_KEY:
        return {
            "status": "demo_mode",
            "message": "Pinata credentials not configured. Running in demo mode.",
        }

    headers = _get_headers()
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{PINATA_API_URL}/data/testAuthentication",
            headers=headers,
        )
        if response.status_code == 200:
            return {"status": "connected", "data": response.json()}
        return {"status": "error", "error": f"API returned {response.status_code}"}
