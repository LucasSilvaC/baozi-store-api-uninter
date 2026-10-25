package br.edu.uninter.baozistore.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record PedidoRequest(
        @NotNull(message = "O ID do cliente é obrigatório.") Long clienteId,
        @NotNull(message = "O ID do produto é obrigatório.") Long produtoId,
        @NotNull(message = "A quantidade é obrigatória.") @Positive(message = "A quantidade deve ser maior que zero.") Integer quantidade
) {
}
