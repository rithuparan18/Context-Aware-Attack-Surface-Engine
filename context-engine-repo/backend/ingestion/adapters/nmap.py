# NOT WIRED INTO THE LIVE PIPELINE.
# Real Nmap XML parser (reads -oX output from disk).
#
# ingestion.py (in the parent dir) is the file actually on the request
# path — it owns Layer 1 end-to-end and emits GraphEngine's schema
# directly, mocked data included, so nothing here is currently called
# by api/server.py.
#
# This is the v2 path from the architecture doc's Section 5
# ('Live scanning...the Evasion Config becomes an active middleware
# around real HTTP adapters'): once you want ingestion.py's mocked
# nmap/amass/gitleaks calls replaced with real tool output read from
# disk, this is where that logic lives. Wire it in by having
# InfrastructureRecon / SecretsRecon in ingestion.py call these
# parsers on real tool output instead of returning the mocked lists,
# then map their RawEntity shape onto GraphEngine's node schema
# (id/type/label/source_tool/attributes) at the call site.

import os
import xml.etree.ElementTree as ET

def parse_nmap(file_path: str) -> list[dict]:
    if not os.path.exists(file_path):
        return []

    entities = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        for host in root.findall("host"):
            addr_elem = host.find("address")
            ip_address = addr_elem.get("addr") if addr_elem is not None else "unknown"
            
            hostname_elem = host.find("hostnames/hostname")
            hostname = hostname_elem.get("name") if hostname_elem is not None else None
            
            for port in host.findall("ports/port"):
                state_elem = port.find("state")
                if state_elem is not None and state_elem.get("state") == "open":
                    port_id = port.get("portid")
                    service_elem = port.find("service")
                    service_name = service_elem.get("name") if service_elem is not None else "unknown"
                    
                    entities.append({
                        "type": "network_service",
                        "extracted_value": f"{hostname or ip_address}:{port_id}",
                        "metadata": {
                            "ip_address": ip_address,
                            "hostname": hostname,
                            "port": int(port_id),
                            "service_name": service_name,
                            "internet_facing": True
                        }
                    })
    except ET.ParseError:
        pass  
        
    return entities
