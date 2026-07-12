"""
Layer 1: Ingestion Pipeline

Per the project brief: "no live network scanning in v1... we will use
realistic mock data." Still true here — but the mock data generation is
now SEEDED BY THE TARGET STRING instead of using a fixed template.

Previously every target produced the identical topology (same 2 subdomains
behind a WAF, same IP assignment, CVE always hitting "vpn") — only the
domain labels differed. That made every graph, every chokepoint, and every
ROI score look the same regardless of what you typed in. Now each target
deterministically gets its own WAF assignment, IP mapping, and CVE target,
derived from a hash of the target string:
  - Same target => same graph every time (cache-friendly, reproducible demo)
  - Different target => genuinely different topology, not just relabeled

This is a stopgap for demo variety, NOT a substitute for live scanning —
see the module-level TODO for the actual path to v2 live data.
"""
import asyncio
import hashlib
import json
import random
import re
from typing import Any, Dict, List

SUBPROCESS_TIMEOUT_SEC = 30
_TARGET_RE = re.compile(r"^[a-zA-Z0-9.\-]+$")

_K8S_IP = "10.0.5.12"
_LEGACY_DB_IP = "192.168.1.50"
_ALL_SUBDOMAINS = ["api", "vpn", "staging", "dev-k8s", "jenkins-ci",
                    "admin-portal", "metrics"]

_KNOWN_CVES = [
    ("CVE-2024-Unauth-RCE", 9.8),
    ("CVE-2023-Broken-Auth", 8.1),
    ("CVE-2024-SSRF-Internal", 7.5),
    ("CVE-2022-Path-Traversal", 6.5),
]


def validate_target(target: str) -> str:
    if not target or not _TARGET_RE.match(target):
        raise ValueError(f"Refusing to scan invalid target: {target!r}")
    return target


def make_node_id(node_type: str, label: str) -> str:
    digest = hashlib.sha1(f"{node_type}:{label}".encode()).hexdigest()[:10]
    return f"{node_type}_{digest}"


def _seeded_rng(target: str) -> random.Random:
    """Deterministic per-target RNG: same target always reproduces the
    same graph, different targets diverge."""
    seed = int(hashlib.sha1(target.encode()).hexdigest()[:12], 16)
    return random.Random(seed)


# ==========================================
# Evasion & Jitter
# ==========================================
class EvasionConfig:
    def __init__(self, jitter_min_ms: int = 200, jitter_max_ms: int = 800):
        self.jitter_min_ms = jitter_min_ms
        self.jitter_max_ms = jitter_max_ms

    async def apply_jitter(self):
        jitter = random.uniform(self.jitter_min_ms, self.jitter_max_ms) / 1000.0
        await asyncio.sleep(jitter)


# ==========================================
# Infrastructure OSINT (nmap, amass)
# ==========================================
class InfrastructureRecon:
    def __init__(self, evasion_config: EvasionConfig):
        self.evasion = evasion_config

    async def _run_exec(self, *args: str) -> bytes:
        """v2 hookup point for live scanning. Not called anywhere in v1."""
        process = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, _ = await asyncio.wait_for(
                process.communicate(), timeout=SUBPROCESS_TIMEOUT_SEC
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise
        return stdout

    async def run_nmap(self, target: str) -> List[Dict]:
        target = validate_target(target)
        await self.evasion.apply_jitter()
        rng = _seeded_rng(target)

        cve_label, cvss = rng.choice(_KNOWN_CVES)
        affected = rng.choice(_ALL_SUBDOMAINS)

        return [
            {"id": make_node_id("ip", _K8S_IP), "type": "ip",
             "label": f"{_K8S_IP} (K8s Node)", "source_tool": "nmap",
             "attributes": {"ports": [443, 6443], "internet_facing": False}},
            {"id": make_node_id("ip", _LEGACY_DB_IP), "type": "ip",
             "label": f"{_LEGACY_DB_IP} (Legacy DB)", "source_tool": "nmap",
             "attributes": {"ports": [3306, 22], "internet_facing": False}},
            {
                "id": make_node_id("vulnerability", f"{cve_label}:{target}"),
                "type": "vulnerability",
                "label": cve_label,
                "source_tool": "nuclei",
                "attributes": {"cvss": cvss, "affected_asset": affected},
            },
        ]

    async def run_amass(self, target: str) -> List[Dict]:
        target = validate_target(target)
        await self.evasion.apply_jitter()
        try:
            await asyncio.wait_for(asyncio.sleep(1.5), timeout=SUBPROCESS_TIMEOUT_SEC)
        except asyncio.TimeoutError as e:
            print(f"[AMASS ERROR] {e}")
            return []
        return self._build_domains(target)

    def _build_domains(self, target: str) -> List[Dict]:
        rng = _seeded_rng(target)

        # Randomized-but-deterministic per target: 2-3 subdomains sit
        # behind a WAF, and every subdomain gets one of the two IPs.
        waf_count = rng.randint(2, 3)
        waf_subdomains = set(rng.sample(_ALL_SUBDOMAINS, waf_count))

        nodes = []
        for sub in _ALL_SUBDOMAINS:
            domain = f"{sub}.{target}"
            resolved_ip = rng.choice([_K8S_IP, _LEGACY_DB_IP])
            nodes.append({
                "id": make_node_id("domain", domain),
                "type": "domain",
                "label": domain,
                "source_tool": "amass",
                "attributes": {
                    "internet_facing": True,
                    "behind_waf": sub in waf_subdomains,
                    "resolved_ip": resolved_ip,
                },
            })
            if sub == "jenkins-ci":
                nodes.append({
                    "id": make_node_id("service", f"Jenkins Master:{target}"),
                    "type": "service",
                    "label": "Jenkins Master Build Server",
                    "source_tool": "nmap",
                    "attributes": {},
                })
        return nodes


# ==========================================
# Secrets Recon (gitleaks)
# ==========================================
class SecretsRecon:
    def __init__(self, evasion_config: EvasionConfig):
        self.evasion = evasion_config

    async def run_gitleaks(self, repo_path: str, target: str) -> List[Dict]:
        await self.evasion.apply_jitter()
        try:
            await asyncio.wait_for(asyncio.sleep(0.5), timeout=SUBPROCESS_TIMEOUT_SEC)
        except asyncio.TimeoutError as e:
            print(f"[GITLEAKS ERROR] {e}")
            return []
        return self._build_leaks(target)

    def _build_leaks(self, target: str) -> List[Dict]:
        rng = _seeded_rng(target)
        leak_kinds = [
            ("AWS IAM Admin Key", "config/prod.yml"),
            ("DB Admin Password", "docker-compose.yml"),
            ("Staging VPN Cert", "infra/vpn.conf"),
            ("Slack Webhook Token", ".env.local"),
        ]
        # 2-3 leaks, each tied to a randomly (but deterministically) chosen
        # subdomain from THIS target's actual subdomain list.
        n_leaks = rng.randint(2, 3)
        chosen = rng.sample(leak_kinds, n_leaks)
        subdomain_choices = rng.sample(_ALL_SUBDOMAINS, n_leaks)

        nodes = []
        for (label, file_path), sub in zip(chosen, subdomain_choices):
            associated_domain = f"{sub}.{target}"
            nodes.append({
                "id": make_node_id("credential", f"{label}:{target}"),
                "type": "credential",
                "label": label,
                "source_tool": "gitleaks",
                "attributes": {"file": file_path, "associated_domain": associated_domain},
            })
        return nodes


# ==========================================
# Orchestrator
# ==========================================
class IngestionPipeline:
    def __init__(self):
        self.evasion = EvasionConfig()
        self.infra_module = InfrastructureRecon(self.evasion)
        self.secrets_module = SecretsRecon(self.evasion)

    async def execute(self, target_domain: str, local_repo: str) -> List[Dict[str, Any]]:
        print(f"[*] Igniting Ingestion Pipeline against {target_domain}...")
        results = await asyncio.gather(
            self.infra_module.run_nmap(target_domain),
            self.infra_module.run_amass(target_domain),
            self.secrets_module.run_gitleaks(local_repo, target_domain),
            return_exceptions=True,
        )
        nodes: List[Dict[str, Any]] = []
        for result in results:
            if isinstance(result, Exception):
                print(f"[!] Adapter failed: {result}")
                continue
            nodes.extend(result)
        print(f"[*] Ingestion complete. {len(nodes)} nodes ready for correlation.")
        return nodes


if __name__ == "__main__":
    pipeline = IngestionPipeline()
    out = asyncio.run(pipeline.execute("bank.local", "./context-engine-repo"))
    print(json.dumps(out, indent=2))
