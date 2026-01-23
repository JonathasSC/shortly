Cypress.Commands.add("login", () => {
  cy.request({
    method: "POST",
    url: "/login/",
    headers: { "X-CYPRESS": "true" },
  });
});
