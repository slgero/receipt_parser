"""Predict a category using a neural network."""
# pylint: skip-file
from typing import Dict, List
import youtokentome as yttm  # type: ignore
import torch
from torch import nn


class CategoryClassifier(nn.Module):
    """A simple perceptron baseline moedel."""

    def __init__(
        self, vocab_size: int, embed_dim: int, num_class: int, pad_idx: int = 0
    ):
        super(CategoryClassifier, self).__init__()
        self.pad_idx = pad_idx
        self.embedding = nn.EmbeddingBag(vocab_size, embed_dim)
        self.fc = nn.Linear(in_features=embed_dim, out_features=num_class)
        self.init_weights()

    def init_weights(self) -> None:
        """Init embedding and fc weights."""

        initrange = 0.5
        self.embedding.weight.data.uniform_(-initrange, initrange)
        self.fc.weight.data.uniform_(-initrange, initrange)
        self.fc.bias.data.zero_()

    def forward(
        self, x_in: torch.Tensor, offsets: torch.Tensor, apply_sigmoid: bool = False
    ) -> torch.Tensor:
        """
        The forward pass of the classifier.

        Parameters
        ----------
        x_in : torch.Tensor
            Input array.
        offsets : torch.Tensor
            Array with lenghts of input texts.
        apply_sigmoid : bool (default=False)
            Indicates whether to use `torch.sigmoid`.

        Returns
        -------
        torch.Tensor [batch_size x num_class]
        """

        embedded = self.embedding(x_in, offsets)
        y_out = self.fc(embedded)
        if apply_sigmoid:
            y_out = torch.sigmoid(y_out)
        return y_out


class PredictCategory:
    """Predict a category using a neural network."""

    def __init__(
        self, path_to_bpe: str, path_to_model: str, model_params: Dict[str, int]
    ):
        self.bpe_model = yttm.BPE(path_to_bpe)
        self.categories: List[str] = [
            "Алкоголь",
            "Бытовая техника",
            "Воды, соки, напитки",
            "Дача и гриль",
            "Другое",
            "Замороженные продукты",
            "Зоотовары",
            "Красота, гигиена, бытовая химия",
            "Макароны, крупы, специи",
            "Молоко, сыр, яйца",
            "Овощи, фрукты, ягоды",
            "Подборки и готовые блюда",
            "Постные продукты",
            "Посуда",
            "Птица, мясо, деликатесы",
            "Рыба, икра",
            "Соусы, орехи, консервы",
            "Товары для дома и дачи",
            "Товары для мам и детей",
            "Хлеб, сладости, снеки",
            "Чай, кофе, сахар",
        ]
        self.device = torch.device("cpu")
        self.model = CategoryClassifier(**model_params)
        self.model.load_state_dict(torch.load(path_to_model, map_location=self.device))
        self.model.eval()

    def predict(self, name_norm: str) -> str:
        """Predict category by name norm."""

        text = self.bpe_model.encode(name_norm)
        text = torch.tensor(text).to(self.device)
        output = self.model(text, torch.tensor([0]).to(self.device))
        return self.categories[output.argmax(1).item()]
