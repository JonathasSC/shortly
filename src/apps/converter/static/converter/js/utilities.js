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

class UrlUtils {
    delayRedirect(delayMs, redirectUrl){
        setTimeout(() => {
            window.location.href = redirectUrl;
        }, delayMs);
    }
}

class TimerUtils {
    secondTimer(timerSeconds, counterElement) {
        const interval = setInterval(() => {
            timerSeconds -= 1;
            counterElement.innerText = timerSeconds;

            if (timerSeconds <= 0) {
                clearInterval(interval);
            }
        }, 1000);
    }
}


