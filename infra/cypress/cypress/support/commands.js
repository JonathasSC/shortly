Cypress.Commands.add("login", () => {
  cy.request({
    method: "POST",
    url: "/login/",
    headers: { "X-CYPRESS": "true" },
  });
});

Cypress.Commands.add("setLanguage", (lang) => {
    cy.get('.cursor-pointer.flex.items-center.gap-1').first().realHover();
    cy.get(`button[value="${lang}"]`).first().click();
});