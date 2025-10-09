const copyToClipboard = (linkId) => {
    const textElement = document.getElementById(`shortCode-${linkId}`);
    const iconElement = document.getElementById(`copyIcon-${linkId}`);
    console.log(textElement)

    if (!textElement || !iconElement) return;

    navigator.clipboard.writeText(textElement.textContent.trim()).then(() => {
        iconElement.textContent = "check";

        setTimeout(() => {
            iconElement.textContent = "content_copy";
            iconElement.classList.remove("text-green-600");
        }, 1500);
    }).catch(err => {
        console.error("Erro ao copiar:", err);
    });
}