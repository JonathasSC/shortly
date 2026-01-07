document.addEventListener("DOMContentLoaded", () => {

    const modals = [...document.querySelectorAll(".announcement-modal")];
    let index = 0;

    if (modals.length === 0) return;


    showModal(0);

    function showModal(i) {
        modals.forEach(m => m.classList.add("hidden"));
        if (modals[i]) {
            modals[i].classList.remove("hidden");
            modals[i].classList.add("flex");
        }
    }

    function hideAll() {
        modals.forEach(m => {
            m.classList.add("hidden");
            m.classList.remove("flex");
        });
    }

    modals.forEach((modal, i) => {

        const continueBtn = modal.querySelector(".continue-btn");
        const closeBtn = modal.querySelector(".close-btn");
        const contentBox = modal.querySelector("div");

        continueBtn.addEventListener("click", () => {
            index++;
            if (index >= modals.length) hideAll();
            else showModal(index);
        });

        closeBtn.addEventListener("click", () => hideAll());

        modal.addEventListener("click", (e) => {
            if (!contentBox.contains(e.target)) hideAll();
        });
    });

});
