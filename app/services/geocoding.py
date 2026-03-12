import asyncio
import logging

from geopy.geocoders import Nominatim

from app.schemas.user import Address, Coordinates

logger = logging.getLogger(__name__)

geolocator = Nominatim(user_agent="homebanking-api")


async def geocode_address(address: Address) -> Coordinates | None:
    """Resolve an address to lat/lng coordinates via OpenStreetMap Nominatim.

    The synchronous geopy call is wrapped in :func:`asyncio.to_thread` to
    avoid blocking the event loop.

    :param address: Structured address to geocode.
    :returns: Coordinates if resolved, or ``None`` if the lookup fails or
        returns no results.
    """
    parts = [address.street, address.city]
    if address.state:
        parts.append(address.state)
    parts.extend([address.postal_code, address.country])
    query = ", ".join(parts)

    try:
        location = await asyncio.to_thread(geolocator.geocode, query)
        if location:
            return Coordinates(
                latitude=location.latitude,
                longitude=location.longitude,
            )
        logger.warning("Geocoding returned no results for: %s", query)
        return None
    except Exception:
        logger.exception("Geocoding failed for: %s", query)
        return None
