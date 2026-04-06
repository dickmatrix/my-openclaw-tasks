from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LeWMConfig:
    capacity_scalar: float = 1.0
    feature_dim: int = field(init=False, default=8)
    action_dim: int = field(init=False, default=3)
    embed_dim: int = field(init=False, default=192)
    hidden_dim: int = field(init=False, default=256)
    depth: int = field(init=False, default=4)
    heads: int = field(init=False, default=4)
    mlp_dim: int = field(init=False, default=512)
    dropout: float = field(init=False, default=0.1)
    history_size: int = field(init=False, default=64)
    horizon: int = field(init=False, default=24)
    lambda_sigreg: float = field(init=False, default=0.05)

    def __post_init__(self) -> None:
        self.embed_dim = max(96, int(192 * self.capacity_scalar))
        self.hidden_dim = max(128, int(256 * self.capacity_scalar))
        self.mlp_dim = max(256, int(512 * self.capacity_scalar))
        self.depth = 4
        self.heads = 4
        self.dropout = 0.1
        self.history_size = 64
        self.horizon = 24
        self.lambda_sigreg = 0.05
