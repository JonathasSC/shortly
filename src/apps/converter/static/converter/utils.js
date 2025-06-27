class TextUtils {
    copyText(targetId) {
        const element = document.getElementById(targetId);
        if (!element) return console.error(`Elemento #${targetId} não encontrado`);

        const text = element.href || element.textContent;
        navigator.clipboard.writeText(text)
            .then(() => console.log('Copiado:', text))
            .catch(err => console.error('Erro ao copiar:', err));
    }
}
