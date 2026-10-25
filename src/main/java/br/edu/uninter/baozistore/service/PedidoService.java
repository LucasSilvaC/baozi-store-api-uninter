package br.edu.uninter.baozistore.service;

import br.edu.uninter.baozistore.dto.PedidoRequest;
import br.edu.uninter.baozistore.dto.PedidoResponse;
import br.edu.uninter.baozistore.model.Cliente;
import br.edu.uninter.baozistore.model.Pedido;
import br.edu.uninter.baozistore.model.Produto;
import br.edu.uninter.baozistore.repository.ClienteRepository;
import br.edu.uninter.baozistore.repository.PedidoRepository;
import br.edu.uninter.baozistore.repository.ProdutoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class PedidoService {

    private final PedidoRepository pedidoRepository;
    private final ClienteRepository clienteRepository;
    private final ProdutoRepository produtoRepository;

    public PedidoService(PedidoRepository pedidoRepository,
                         ClienteRepository clienteRepository,
                         ProdutoRepository produtoRepository) {
        this.pedidoRepository = pedidoRepository;
        this.clienteRepository = clienteRepository;
        this.produtoRepository = produtoRepository;
    }

    @Transactional
    public PedidoResponse criar(PedidoRequest dados) {
        Pedido pedido = new Pedido();
        aplicarDados(pedido, dados);
        return paraResposta(pedidoRepository.save(pedido));
    }

    @Transactional(readOnly = true)
    public List<PedidoResponse> listarTodos() {
        return pedidoRepository.findAll().stream().map(this::paraResposta).toList();
    }

    @Transactional(readOnly = true)
    public PedidoResponse buscarPorId(Long id) {
        return paraResposta(buscarPedido(id));
    }

    @Transactional
    public PedidoResponse atualizar(Long id, PedidoRequest dados) {
        Pedido pedido = buscarPedido(id);
        aplicarDados(pedido, dados);
        return paraResposta(pedidoRepository.save(pedido));
    }

    @Transactional
    public void excluir(Long id) {
        pedidoRepository.delete(buscarPedido(id));
    }

    private Pedido buscarPedido(Long id) {
        return pedidoRepository.findById(id)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Pedido " + id + " não encontrado."));
    }

    private void aplicarDados(Pedido pedido, PedidoRequest dados) {
        Cliente cliente = clienteRepository.findById(dados.clienteId())
                .orElseThrow(() -> new RecursoNaoEncontradoException(
                        "Cliente " + dados.clienteId() + " não encontrado."));
        Produto produto = produtoRepository.findById(dados.produtoId())
                .orElseThrow(() -> new RecursoNaoEncontradoException(
                        "Produto " + dados.produtoId() + " não encontrado."));

        if (!Boolean.TRUE.equals(produto.getEstoque())) {
            throw new RegraDeNegocioException("O produto selecionado está sem estoque.");
        }

        pedido.setCliente(cliente);
        pedido.setProduto(produto);
        pedido.setQuantidade(dados.quantidade());
    }

    private PedidoResponse paraResposta(Pedido pedido) {
        return new PedidoResponse(
                pedido.getId(),
                pedido.getCliente().getId(),
                pedido.getProduto().getId(),
                pedido.getQuantidade()
        );
    }
}
