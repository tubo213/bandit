from typing import Optional

import numpy as np
import torch
import torch.nn as nn

from src.utils import concat_context_and_action_context, set_seed


class BanditEnv:
    def __init__(
        self,
        n_actions: int,
        dim_context: int,
        action_context: Optional[np.ndarray] = None,
        random_state: int = 11111,
    ):
        self.n_actions = n_actions
        self.dim_context = dim_context
        self.action_context = (
            action_context if action_context is not None else np.identity(n_actions)
        )
        self.dim_action_context = self.action_context.shape[1]
        self.model = MLP(dim_context + self.dim_action_context).train()
        set_seed(random_state)

    def get_context(self, n: int) -> np.ndarray:
        return np.random.uniform(-1, 1, size=(n, self.dim_context))

    def get_reward(self, context: np.ndarray) -> np.ndarray:
        reward_list = []
        for i in range(self.n_actions):
            x_i = concat_context_and_action_context(context, self.action_context[[i]])
            x_i = torch.from_numpy(x_i).float()
            with torch.no_grad():
                reward = self.model(x_i).detach().numpy().flatten()
            reward_list.append(reward)
        reward = np.stack(reward_list, axis=1)

        return reward


class MLP(nn.Module):
    def __init__(self, dim: int, dim_hidden: int = 16, n_hidden: int = 2, dim_output: int = 1):
        super().__init__()
        module_list = [nn.Linear(dim, dim_hidden), nn.SELU()]

        if n_hidden > 2:
            for _ in range(n_hidden - 2):
                module_list.append(nn.Linear(dim_hidden, dim_hidden))
                module_list.append(nn.SELU())

        module_list.append(nn.Linear(dim_hidden, dim_output))
        self.fc = nn.ModuleList(module_list)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for layer in self.fc:
            x = layer(x)
        return x


def generate_action_context(
    n_actions: int, dim_action_context: int, random_state: int = 11111
) -> np.ndarray:
    np.random.seed(random_state)
    action_context = (
        np.random.uniform(-1, 1, size=(n_actions, dim_action_context)).cumsum(axis=1) ** 2
    )
    action_context = (action_context - action_context.mean(axis=0)) / action_context.std(axis=0)

    return action_context
