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
