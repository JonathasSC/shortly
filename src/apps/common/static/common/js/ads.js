(function () {
    const queue = [];
    let isLoading = false;

    function loadNext() {
        if (isLoading || queue.length === 0) return;
        isLoading = true;

        const { container, key, height, width } = queue.shift();

        window.atOptions = {
            key,
            format: 'iframe',
            height,
            width,
            params: {},
        };

        const script = document.createElement('script');
        script.onload = script.onerror = () => {
            isLoading = false;
            loadNext();
        };
        script.src = `https://www.highperformanceformat.com/${key}/invoke.js`;
        container.appendChild(script);
    }

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                observer.unobserve(entry.target);

                const el = entry.target;
                queue.push({
                    container: el,
                    key: el.dataset.adKey,
                    height: Number(el.dataset.adHeight),
                    width: Number(el.dataset.adWidth),
                });
            });
            loadNext();
        },
        { rootMargin: '200px' }
    );

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-ad-key]').forEach((el) => observer.observe(el));
    });
})();
