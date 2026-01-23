describe("Signin and Signup", () => {
  it("successfully signup", () => {
    cy.intercept("POST", "/account/register/", (req) => {
      req.headers["X-CYPRESS"] = "true";
    }).as("signup");

    cy.visit("http://localhost:8000/account/register");

    cy.get('input[name="username"]').type("cypress");
    cy.get('input[name="email"]').type("cypress@test.com");
    cy.get('input[name="password"]').type("Cypress@123456");
    cy.get('input[name="confirm_password"]').type("Cypress@123456");

    cy.get('button[type="submit"]')
      .contains(/Registrar|Signup/i)
      .click();

    cy.wait("@signup");
    cy.url().should("include", "/account/login");
    cy.contains(/Welcome back|Signin|Entrar/i).should("exist");

  })


  it("successfully signin", () => {
    cy.intercept("POST", "/account/login/", (req) => {
      req.headers["X-CYPRESS"] = "true";
    }).as("signin");

    cy.visit("http://localhost:8000/account/login");

    cy.get('input[name="username"]').first().type("cypress");
    cy.get('input[name="password"]').type("Cypress@123456");
    
    cy.get('button[type="submit"]')
      .contains(/Entrar|Signin/i)
      .click();
  });
});
