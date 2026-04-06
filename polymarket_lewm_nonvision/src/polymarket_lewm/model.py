from __future__ import annotations

from dataclasses import asdict

import torch
import torch.nn.functional as F
from torch import nn

from polymarket_lewm.model_config import LeWMConfig


class SIGReg(nn.Module):
    def __init__(self, knots: int = 17, num_proj: int = 256) -> None:
        super().__init__()
        t = torch.linspace(0, 3, knots, dtype=torch.float32)
        dt = 3 / (knots - 1)
        weights = torch.full((knots,), 2 * dt, dtype=torch.float32)
        weights[[0, -1]] = dt
        window = torch.exp(-t.square() / 2.0)
        self.num_proj = num_proj
        self.register_buffer("t", t)
        self.register_buffer("phi", window)
        self.register_buffer("weights", weights * window)

    def forward(self, proj: torch.Tensor) -> torch.Tensor:
        basis = torch.randn(proj.size(-1), self.num_proj, device=proj.device)
        basis = basis / basis.norm(p=2, dim=0, keepdim=True)
        x_t = (proj @ basis).unsqueeze(-1) * self.t
        err = (x_t.cos().mean(-3) - self.phi).square() + x_t.sin().mean(-3).square()
        statistic = (err @ self.weights) * proj.size(-2)
        return statistic.mean()


class TimeSeriesEncoder(nn.Module):
    def __init__(self, config: LeWMConfig) -> None:
        super().__init__()
        self.input_proj = nn.Linear(config.feature_dim, config.hidden_dim)
        layer = nn.TransformerEncoderLayer(
            d_model=config.hidden_dim,
            nhead=config.heads,
            dim_feedforward=config.mlp_dim,
            dropout=config.dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=config.depth)
        self.output_proj = nn.Linear(config.hidden_dim, config.embed_dim)
        self.position = nn.Parameter(torch.randn(1, config.history_size + config.horizon + 1, config.hidden_dim) * 0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        hidden = self.input_proj(x) + self.position[:, : x.size(1)]
        hidden = self.encoder(hidden)
        return self.output_proj(hidden)


class ActionEncoder(nn.Module):
    def __init__(self, config: LeWMConfig) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(config.action_dim, config.embed_dim),
            nn.GELU(),
            nn.Linear(config.embed_dim, config.embed_dim),
        )

    def forward(self, action: torch.Tensor) -> torch.Tensor:
        return self.net(action)


class Predictor(nn.Module):
    def __init__(self, config: LeWMConfig) -> None:
        super().__init__()
        layer = nn.TransformerEncoderLayer(
            d_model=config.embed_dim,
            nhead=config.heads,
            dim_feedforward=config.mlp_dim,
            dropout=config.dropout,
            batch_first=True,
            activation="gelu",
        )
        self.position = nn.Parameter(torch.randn(1, config.history_size + 1, config.embed_dim) * 0.02)
        self.predictor = nn.TransformerEncoder(layer, num_layers=config.depth)
        self.out = nn.Linear(config.embed_dim, config.embed_dim)

    def forward(self, emb: torch.Tensor, act_emb: torch.Tensor) -> torch.Tensor:
        hidden = emb + act_emb + self.position[:, : emb.size(1)]
        return self.out(self.predictor(hidden))


class ProbabilityHead(nn.Module):
    def __init__(self, config: LeWMConfig) -> None:
        super().__init__()
        self.logit = nn.Linear(config.embed_dim, 1)
        self.confidence = nn.Linear(config.embed_dim, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        prob = torch.sigmoid(self.logit(x))
        confidence = torch.sigmoid(self.confidence(x))
        return prob.squeeze(-1), confidence.squeeze(-1)


class NonVisualLeWorldModel(nn.Module):
    def __init__(self, config: LeWMConfig) -> None:
        super().__init__()
        self.config = config
        self.encoder = TimeSeriesEncoder(config)
        self.action_encoder = ActionEncoder(config)
        self.predictor = Predictor(config)
        self.projector = nn.Sequential(nn.Linear(config.embed_dim, config.embed_dim), nn.GELU(), nn.Linear(config.embed_dim, config.embed_dim))
        self.pred_proj = nn.Sequential(nn.Linear(config.embed_dim, config.embed_dim), nn.GELU(), nn.Linear(config.embed_dim, config.embed_dim))
        self.probability_head = ProbabilityHead(config)
        self.sigreg = SIGReg()

    def encode(self, features: torch.Tensor) -> torch.Tensor:
        return self.projector(self.encoder(features))

    def predict_embeddings(self, features: torch.Tensor, actions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        emb = self.encode(features)
        act = self.action_encoder(actions)
        pred = self.pred_proj(self.predictor(emb[:, :-1], act[:, :-1]))
        target = emb[:, 1:]
        return pred, target

    def forward(self, features: torch.Tensor, actions: torch.Tensor) -> dict[str, torch.Tensor]:
        pred, target = self.predict_embeddings(features, actions)
        pred_loss = F.mse_loss(pred, target)
        sigreg_loss = self.sigreg(target.transpose(0, 1))
        total = pred_loss + self.config.lambda_sigreg * sigreg_loss
        prob, confidence = self.probability_head(pred[:, -1])
        return {
            "loss": total,
            "pred_loss": pred_loss,
            "sigreg_loss": sigreg_loss,
            "probability": prob,
            "confidence": confidence,
        }

    def infer(self, features: torch.Tensor, actions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        with torch.no_grad():
            pred, _ = self.predict_embeddings(features, actions)
            return self.probability_head(pred[:, -1])

    def summary(self) -> dict[str, int]:
        params = sum(p.numel() for p in self.parameters())
        return {"params": params, "trainable": sum(p.numel() for p in self.parameters() if p.requires_grad)}

    def export_config(self) -> dict[str, int | float]:
        return asdict(self.config)
