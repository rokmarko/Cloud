#!/usr/bin/env python3
"""
NOTAM retrieval and parsing system for KanardiaCloud.
Based on the external notam.py script, adapted for Flask application integration.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ICAO Q-code dictionary for NOTAM codes
Q_CODE_DICT = {
    "QMRLC": "Runway closed",
    "QMRHW": "Runway holding position light unserviceable",
    "QMRDV": "Runway surface damaged",
    "QMRSL": "Runway surface slippery",
    "QMRLD": "Runway length reduced",
    "QMRXX": "Runway restriction (other)",
    "QMXLC": "Taxiway closed",
    "QMXLS": "Taxiway surface poor",
    "QMXHW": "Taxiway holding position light unserviceable",
    "QNXLC": "Apron closed",
    "QNXLS": "Apron surface poor",
    "QLRLC": "Lighting system unserviceable",
    "QLRLI": "Lighting intensity reduced",
    "QLRDL": "Approach lights unserviceable",
    "QOBCE": "Obstacle – electricity pylon",
    "QOBCL": "Obstacle – crane",
    "QOBCT": "Obstacle – tower",
    "QOBST": "Obstacle (general)",
    "QRRCA": "Restricted area activated",
    "QRDCA": "Danger area activated",
    "QRTCA": "Temporary reserved area active",
    "QRACA": "Airspace restriction activated",
    "QFAXX": "Flight information service limitation",
    "QFPLT": "Flight plan service unavailable",
    "QSEXX": "Surveillance (radar) service limitation",
    "QNBAS": "NDB unserviceable",
    "QDVAS": "VOR unserviceable",
    "QTRAS": "DME unserviceable",
    "QILAS": "ILS unserviceable",
    "QILRW": "ILS runway unserviceable",
    "QILGS": "ILS glide path unserviceable",
    "QILLZ": "ILS localizer unserviceable",
    "QLPAS": "PAPI unserviceable",
    "QCMAS": "COM facility unserviceable",
    "QWAUW": "Volcanic ash",
    "QWELW": "Obstacle – crane",
    "QWCLW": "Obstacle – tower (lighting issue)",
    "QTZCA": "Temporary segregated area active",
    "QWSLW": "Warning — hazardous substance / gas release",
    "QRNCA": "Navigation aid service unavailable",
    "QPWXX": "Power failure",
    "QRHCA": "Radio/navigation hazard area",
    "QOBWE": "Obstacle – wire",
    "QOBWX": "Obstacle – unspecified",
    "QOBSE": "Obstacle – ski lift",
    "QOBBR": "Obstacle – bird activity",
    "QAWXX": "Airspace warning",
    "QDICA": "Danger area deactivated",
    "QINTC": "Intermediate frequency failure",
    "QCICX": "Circuit interruption",
    "QILIC": "ILS intercept critical",
    "QIAA": "Airport action advised",
    "QRICA": "Restricted area deactivated",
    "QFRPT": "Fuel report unavailable",
    "QXXXX": "NOTAM code unspecified"
}


def fetch_notams(icao_code: str) -> List[str]:
    """
    Fetch NOTAMs from FAA website for a given ICAO code.
    
    Args:
        icao_code: 4-letter ICAO airport/FIR code
        
    Returns:
        List of raw NOTAM text strings
        
    Raises:
        requests.RequestException: If the request fails
    """
    try:
        url = "https://www.notams.faa.gov/dinsQueryWeb/queryRetrievalMapAction.do"
        params = {
            "actionType": "notamRetrievalbyICAOs",
            "reportType": "Raw",
            "retrieveLocId": icao_code
        }
        
        logger.info(f"Fetching NOTAMs for {icao_code}")
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        pre_tags = soup.find_all("pre")
        notams = []
        
        for pre in pre_tags:
            text = pre.get_text().strip()
            if text:
                # entries are typically separated by blank lines
                for block in re.split(r"\n\s*\n", text.strip()):
                    b = block.strip()
                    if b:
                        notams.append(b)
        
        logger.info(f"Retrieved {len(notams)} NOTAMs for {icao_code}")
        return notams
        
    except Exception as e:
        logger.error(f"Error fetching NOTAMs for {icao_code}: {str(e)}")
        raise


def parse_coords(coords_radius: str) -> Dict[str, Any]:
    """
    Parse coordinate and radius from Q-line format.
    
    Args:
        coords_radius: String like "5117N01210E001"
        
    Returns:
        Dictionary with parsed coordinates and radius
    """
    m = re.match(r"^\s*(\d{2})(\d{2})([NS])(\d{3})(\d{2})([EW])(\d{3})\s*$", coords_radius)
    if not m:
        return {"raw": coords_radius}
    
    lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir, radius = m.groups()
    lat = int(lat_deg) + int(lat_min)/60.0
    if lat_dir == "S":
        lat = -lat
    lon = int(lon_deg) + int(lon_min)/60.0
    if lon_dir == "W":
        lon = -lon
    
    return {
        "raw": coords_radius,
        "latitude": lat,
        "longitude": lon,
        "radius_nm": int(radius)
    }


def parse_alt_code(limit: str) -> Dict[str, Any]:
    """
    Parse altitude code from Q-line (hundreds of feet; 999 = UNL).
    
    Args:
        limit: 3-digit altitude code like "000", "050", "999"
        
    Returns:
        Dictionary with parsed altitude information
    """
    limit = limit.strip()
    if limit == "000":
        return {"raw": limit, "feet": 0, "flight_level": "FL000"}
    if limit == "999":
        return {"raw": limit, "feet": None, "flight_level": "UNL"}
    if re.fullmatch(r"\d{3}", limit):
        feet = int(limit) * 100
        return {"raw": limit, "feet": feet, "flight_level": f"FL{limit}"}
    return {"raw": limit}


def parse_alt_text(text: str) -> Dict[str, Any]:
    """
    Parse F)/G) altitude text forms like:
      - GND / SFC
      - FL100 / FL045
      - 3500FT AMSL, 1000FT AGL
      - 500M AGL/AMSL
      - UNL / UNLIMITED
    
    Args:
        text: Raw altitude text
        
    Returns:
        Dictionary with normalized altitude fields
    """
    raw = text.strip().upper()
    out = {"raw": text.strip()}

    if any(x in raw for x in ["GND", "SFC"]):
        out.update({"type": "SFC", "feet": 0, "reference": "SFC"})
        return out

    if "UNL" in raw or "UNLIMIT" in raw:
        out.update({"type": "UNL", "feet": None, "flight_level": "UNL"})
        return out

    m = re.search(r"\bFL\s*?(\d{2,3})\b", raw)
    if m:
        fl = m.group(1).zfill(3)
        out.update({"flight_level": f"FL{fl}", "feet": int(fl) * 100})
        return out

    m = re.search(r"\b(\d{1,5})\s*FT\b", raw)
    if m:
        feet = int(m.group(1))
        ref = None
        if "AMSL" in raw:
            ref = "AMSL"
        elif "AGL" in raw:
            ref = "AGL"
        out.update({"feet": feet, "reference": ref})
        return out

    m = re.search(r"\b(\d{1,4})\s*M\b", raw)
    if m:
        meters = int(m.group(1))
        feet = round(meters * 3.28084)
        ref = None
        if "AMSL" in raw:
            ref = "AMSL"
        elif "AGL" in raw:
            ref = "AGL"
        out.update({"meters": meters, "feet": feet, "reference": ref})
        return out

    return out  # fallback: just the raw string


def parse_q_line(q_line_raw: str) -> Dict[str, Any]:
    """
    Robust Q) parsing:
    - keep full raw (including odd spacing),
    - normalize spaces and drop empty segments before splitting,
    - require at least 8 tokens to decode fully.
    
    Args:
        q_line_raw: Raw Q-line text
        
    Returns:
        Dictionary with parsed Q-line components
    """
    # capture raw and a normalized copy for splitting
    raw = q_line_raw.rstrip()
    # collapse internal multiple spaces but keep slashes
    # then split by '/', trim each, and drop empties
    tokens = [seg.strip().replace(" ", "") for seg in raw.split("/") if seg.strip() != ""]

    # Expect: [FIR, CODE, TRAFFIC, PURPOSE, SCOPE, LOWER, UPPER, COORDSRAD]
    q = {"raw": raw}
    if len(tokens) >= 8:
        fir, code, traffic, purpose, scope, lower, upper, coords = tokens[:8]
        q.update({
            "fir": fir,
            "code": code,
            "code_meaning": Q_CODE_DICT.get(code, "Unknown code"),
            "traffic": traffic,
            "purpose": purpose,
            "scope": scope,
            "lower_limit": parse_alt_code(lower),
            "upper_limit": parse_alt_code(upper),
            "coords": parse_coords(coords)
        })
    return q


def parse_notam(notam_text: str) -> Dict[str, Any]:
    """
    Parse a single NOTAM from raw text into structured data.
    
    Args:
        notam_text: Raw NOTAM text
        
    Returns:
        Dictionary with parsed NOTAM data
    """
    data = {"raw": notam_text}

    # ID at start: e.g. D2932/25, A1234/25, etc.
    m = re.match(r"\b([A-Z]\d{3,4}/\d{2})\b", notam_text)
    if m:
        data["id"] = m.group(1)

    # Full Q) line until newline (allow spaces)
    m = re.search(r"(?m)^Q\)\s*([^\r\n]+)", notam_text)
    if m:
        data["q_line"] = parse_q_line(m.group(1))

    # A) location
    m = re.search(r"(?m)^A\)\s*([A-Z]{4})", notam_text)
    if m:
        data["location"] = m.group(1)

    # B)/C) validity (YYMMDDHHMM) - can be on same line as A) or separate lines
    m = re.search(r"B\)\s*(\d{10})", notam_text)
    if m:
        try:
            data["valid_from"] = datetime.strptime(m.group(1), "%y%m%d%H%M").replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            data["valid_from"] = m.group(1)

    m = re.search(r"C\)\s*(\d{10}|PERM)", notam_text)
    if m:
        val = m.group(1)
        if val == "PERM":
            data["valid_until"] = "PERMANENT"
        else:
            try:
                data["valid_until"] = datetime.strptime(val, "%y%m%d%H%M").replace(tzinfo=timezone.utc).isoformat()
            except Exception:
                data["valid_until"] = val

    # E) body until F)/G)/CREATED/SOURCE or end
    m = re.search(r"E\)\s*(.+?)(?=\nF\)|\nG\)|\nCREATED:|\nSOURCE:|\Z)", notam_text, re.DOTALL | re.IGNORECASE)
    if m:
        data["body"] = m.group(1).strip()

    # F) and G) altitude lines
    m = re.search(r"(?mi)^\s*F\)\s*([^\r\n]+)", notam_text)
    if m:
        data["f_limit"] = parse_alt_text(m.group(1))
    m = re.search(r"(?mi)^\s*G\)\s*([^\r\n]+)", notam_text)
    if m:
        data["g_limit"] = parse_alt_text(m.group(1))

    # Optional CREATED and SOURCE
    m = re.search(r"(?mi)^\s*CREATED:\s*([^\r\n]+)", notam_text)
    if m:
        created_raw = m.group(1).strip()
        data["created"] = {"raw": created_raw}
        # Try parse "22 Aug 2025 05:55:00"
        try:
            data["created"]["iso"] = datetime.strptime(created_raw, "%d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            pass

    m = re.search(r"(?mi)^\s*SOURCE:\s*([^\r\n]+)", notam_text)
    if m:
        data["source"] = m.group(1).strip()

    return data


def fetch_and_parse_notams(icao_code: str) -> Dict[str, Any]:
    """
    Fetch and parse NOTAMs for a given ICAO code.
    
    Args:
        icao_code: 4-letter ICAO airport/FIR code
        
    Returns:
        Dictionary with statistics and parsed NOTAMs
    """
    try:
        raw_notams = fetch_notams(icao_code)
        structured = [parse_notam(n) for n in raw_notams]

        # Generate statistics
        q_codes = [
            n.get("q_line", {}).get("code")
            for n in structured
            if isinstance(n.get("q_line"), dict) and n["q_line"].get("code")
        ]
        
        per_code = {
            code: {"count": cnt, "meaning": Q_CODE_DICT.get(code, "Unknown code")}
            for code, cnt in Counter(q_codes).items()
        }

        output = {
            "statistics": {
                "icao": icao_code,
                "count_total": len(raw_notams),
                "count_parsed": sum(1 for n in structured if "id" in n),
                "per_code": per_code,
                "last_updated": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
            },
            "notams": structured
        }

        return output
        
    except Exception as e:
        logger.error(f"Error processing NOTAMs for {icao_code}: {str(e)}")
        raise


if __name__ == "__main__":
    # Test with LJLA
    icao = "LJLA"
    try:
        result = fetch_and_parse_notams(icao)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
