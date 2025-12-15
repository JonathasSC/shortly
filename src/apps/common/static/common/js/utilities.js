const copyToClipboard = (source, icon = null) => {
    const textElement = typeof source === "string" 
        ? document.getElementById(source) 
        : source;

    if (!textElement) {
        console.error("Elemento de texto não encontrado:", source);
        return;
    }

    const text = textElement.textContent.trim();

    navigator.clipboard.writeText(text).then(() => {
        if (icon) {
            const iconElement = typeof icon === "string"
                ? document.getElementById(icon)
                : icon;

            if (iconElement) {
                iconElement.textContent = "check";

                setTimeout(() => {
                    iconElement.textContent = "content_copy";
                    iconElement.classList.remove("text-green-600");
                }, 1500);
            }
        }
    }).catch((err) => {
        console.error("Erro ao copiar:", err);
    });
}

const isValidUrl = (string) => {
  try {
    const url = new URL(string);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch (_) {
    return false;
  }
}
