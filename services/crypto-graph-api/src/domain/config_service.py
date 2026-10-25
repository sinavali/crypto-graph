"""
Comprehensive System Configuration Service.
Persists and manages all configurable aspects of the platform:
RPC endpoint lists, circuit thresholds, heuristic clustering weights, graph rendering rules, and security policies.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Tuple
from libs.blockchain_contracts.config_models import ConfigCategory, SystemConfigItem
from libs.blockchain_contracts.models import ChainEcosystem
from ..infrastructure.rpc_rotator import FREE_RPC_POOLS


# Initial enterprise defaults
DEFAULT_CONFIGS: Dict[str, Tuple[str, ConfigCategory, str]] = {
    # RPC configurations
    "rpc.endpoints": (
        json.dumps({chain.value: urls for chain, urls in FREE_RPC_POOLS.items()}),
        ConfigCategory.RPC,
        "Active multi-chain RPC endpoint pools per ecosystem (JSON format)",
    ),
    "rpc.timeout_seconds": ("4.0", ConfigCategory.RPC, "Network HTTP request timeout in seconds"),
    "rpc.max_retries": ("3", ConfigCategory.RPC, "Maximum round-robin retry attempts per query"),
    "rpc.circuit_threshold": ("3", ConfigCategory.RPC, "Consecutive failures before tripping circuit breaker"),
    "rpc.circuit_cooldown": ("15.0", ConfigCategory.RPC, "Cooldown seconds before attempting circuit half-open probe"),
    "rpc.offline_mode": ("false", ConfigCategory.RPC, "Force deterministic offline fixtures replay mode"),
    "rpc.rate_limit_per_second": ("10", ConfigCategory.RPC, "Client-side maximum rate limit in requests per second"),
    "rpc.enable_fallback_fixtures": ("true", ConfigCategory.RPC, "Fallback to fixtures when public RPC nodes are unavailable"),
    "rpc.user_agent": ("crypto-graph-engine/1.0", ConfigCategory.RPC, "Custom User-Agent header for RPC requests"),

    # Heuristic weights & thresholds
    "heuristics.cex_deposit_weight": ("0.85", ConfigCategory.HEURISTICS, "Confidence weight for shared CEX deposit reuse"),
    "heuristics.bridge_correlation_weight": ("0.80", ConfigCategory.HEURISTICS, "Confidence weight for cross-chain bridge transfer match"),
    "heuristics.co_funding_weight": ("0.70", ConfigCategory.HEURISTICS, "Confidence weight for direct co-funding temporal coordination"),
    "heuristics.utxo_common_spend_weight": ("0.90", ConfigCategory.HEURISTICS, "Confidence weight for UTXO multi-input common spend"),
    "heuristics.co_funding_max_value": ("1.0", ConfigCategory.HEURISTICS, "Maximum ETH/native value to classify as seed funding"),
    "heuristics.temporal_window_minutes": ("30", ConfigCategory.HEURISTICS, "Time proximity correlation window for bridge events (mins)"),
    "heuristics.min_confidence_threshold": ("0.20", ConfigCategory.HEURISTICS, "Minimum confidence threshold to include wallet in persona"),
    "heuristics.standalone_baseline_confidence": ("0.50", ConfigCategory.HEURISTICS, "Baseline confidence score for standalone single-address persona"),

    # Graph visualization
    "graph.default_layout": ("cose", ConfigCategory.GRAPH, "Default network layout algorithm (cose, concentric, circle)"),
    "graph.max_nodes_render": ("150", ConfigCategory.GRAPH, "Maximum nodes rendered on initial canvas"),
    "graph.min_edge_volume_filter": ("0.0", ConfigCategory.GRAPH, "Threshold volume to hide minor noise edges"),
    "graph.enable_animations": ("true", ConfigCategory.GRAPH, "Enable directional flow animation on edges"),
    "graph.node_size_scale": ("1.0", ConfigCategory.GRAPH, "Node size scaling multiplier on canvas"),
    "graph.edge_arrow_scale": ("0.9", ConfigCategory.GRAPH, "Edge arrow size scaling multiplier"),
    "graph.color_target": ("#38bdf8", ConfigCategory.GRAPH, "Hex highlight color for target queried address"),
    "graph.color_bridge": ("#a855f7", ConfigCategory.GRAPH, "Hex highlight color for cross-chain bridge contracts"),
    "graph.color_exchange": ("#f59e0b", ConfigCategory.GRAPH, "Hex highlight color for exchange hot/deposit wallets"),
    "graph.color_counterparty": ("#4b5563", ConfigCategory.GRAPH, "Hex color for regular counterparty wallets"),
    "graph.animation_duration_ms": ("800", ConfigCategory.GRAPH, "Canvas layout animation duration in milliseconds"),

    # Security & Authentication
    "auth.captcha_enabled": ("true", ConfigCategory.SECURITY, "Require built-in SVG captcha on signup/login"),
    "auth.captcha_ttl_seconds": ("300", ConfigCategory.SECURITY, "Time-to-live for captcha challenge before expiration (seconds)"),
    "auth.session_hours": ("24", ConfigCategory.SECURITY, "Session cookie validity window in hours"),
    "auth.password_min_length": ("6", ConfigCategory.SECURITY, "Minimum password length required for registration"),
    "auth.max_failed_attempts": ("5", ConfigCategory.SECURITY, "Maximum failed login attempts before temporary lockout"),

    # Tenancy & Storage
    "tenancy.max_watchlist_items": ("100", ConfigCategory.TENANCY, "Maximum tracked addresses per tenant"),
    "tenancy.max_saved_investigations": ("50", ConfigCategory.TENANCY, "Maximum saved investigation graphs per tenant"),
    "tenancy.max_search_history": ("20", ConfigCategory.TENANCY, "Maximum recent search history records retained per tenant"),
    "tenancy.allow_public_registration": ("true", ConfigCategory.TENANCY, "Allow public visitor signup without prior invitation"),
}


class ConfigService:
    def __init__(self, storage_port):
        self.storage = storage_port
        self._init_defaults()

    def _init_defaults(self) -> None:
        """Seed default configs into datastore if not already set."""
        for key, (val, cat, desc) in DEFAULT_CONFIGS.items():
            existing = self.storage.get_config(key)
            if existing is None:
                self.storage.set_config(
                    SystemConfigItem(
                        config_key=key,
                        config_value=val,
                        category=cat,
                        description=desc,
                    )
                )

    def get(self, key: str, default: Optional[str] = None) -> str:
        item = self.storage.get_config(key)
        if item:
            return item.config_value
        if key in DEFAULT_CONFIGS:
            return DEFAULT_CONFIGS[key][0]
        return default or ""

    def get_float(self, key: str, default: float = 0.0) -> float:
        try:
            return float(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self.get(key, "true" if default else "false").lower()
        return val in ("true", "1", "yes")

    def get_json(self, key: str, default: Optional[Any] = None) -> Any:
        try:
            return json.loads(self.get(key, "{}"))
        except Exception:
            return default or {}

    def set(self, key: str, value: str, category: Optional[ConfigCategory] = None, description: str = "") -> None:
        cat = category or (DEFAULT_CONFIGS.get(key, (None, ConfigCategory.RPC, ""))[1])
        desc = description or (DEFAULT_CONFIGS.get(key, (None, None, ""))[2])
        self.storage.set_config(
            SystemConfigItem(
                config_key=key,
                config_value=str(value),
                category=cat,
                description=desc,
                updated_at_utc=datetime.now(timezone.utc),
            )
        )

    def get_all_by_category(self) -> Dict[str, List[SystemConfigItem]]:
        all_items = self.storage.get_all_configs()
        grouped: Dict[str, List[SystemConfigItem]] = {}
        for item in all_items:
            grouped.setdefault(item.category.value, []).append(item)
        return grouped
