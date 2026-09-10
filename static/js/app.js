// Interações client-side do Sistema de Chamados EQS.
document.addEventListener('DOMContentLoaded', function () {
    // Confirmação antes de alterar o status de um chamado/projeto.
    document.querySelectorAll('form[data-confirm-status]').forEach(function (form) {
        var select = form.querySelector('select[name="status"]');
        if (!select) return;
        var valorAtual = select.value;
        select.addEventListener('change', function () {
            var novoValor = select.value;
            var confirmado = window.confirm(
                'Alterar o status de "' + valorAtual + '" para "' + novoValor + '"?'
            );
            if (confirmado) {
                form.submit();
            } else {
                select.value = valorAtual;
            }
        });
    });

    // Contador de caracteres para o título do chamado (limite sugerido de 150).
    var tituloChamado = document.querySelector('#id_titulo');
    var contador = document.querySelector('#contador-titulo');
    if (tituloChamado && contador) {
        var atualizarContador = function () {
            var restante = 150 - tituloChamado.value.length;
            contador.textContent = restante + ' caracteres restantes';
            contador.classList.toggle('text-danger', restante < 0);
        };
        tituloChamado.addEventListener('input', atualizarContador);
        atualizarContador();
    }

    // Evita duplo envio de formulários (desabilita o botão após o submit).
    document.querySelectorAll('form.js-single-submit').forEach(function (form) {
        form.addEventListener('submit', function () {
            var botao = form.querySelector('button[type="submit"]');
            if (botao) {
                botao.disabled = true;
                botao.textContent = 'Enviando...';
            }
        });
    });

    // Fecha mensagens de feedback automaticamente após alguns segundos.
    document.querySelectorAll('[data-auto-dismiss]').forEach(function (item) {
        setTimeout(function () {
            item.style.transition = 'opacity 0.5s';
            item.style.opacity = '0';
            setTimeout(function () { item.remove(); }, 500);
        }, 6000);
    });
});
