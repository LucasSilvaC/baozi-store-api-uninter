package br.edu.uninter.baozistore.dto;

public record PedidoResponse(Long id, Long clienteId, Long produtoId, Integer quantidade) {
}
