describe("Shorten URL", () => {
    it("create a short url", () => {
        cy.visit("localhost:8000");
        cy.setLanguage("pt-br");
        const randomUrl = `https://example.com/test-${Date.now()}`;
        
        cy.get('input[name="original_url"]').first().type(randomUrl);
        cy.get('button[id="shorten_btn"]').first().click();
        
        cy.contains("URL encurtada:");

        cy.get('#shortUrlLink')
        .should('have.attr', 'href')
        .and('include', 'http');

        cy.get('#shortUrlLink').should('be.visible');
    });
});

describe("Change Language", () => {
    it("translate to english", () => {
        cy.visit("localhost:8000");
        cy.setLanguage("pt-br");
        cy.get('.cursor-pointer.flex.items-center.gap-1').first().realHover();

        cy.get('button[value="en"]').should('be.visible').first().click();
        cy.contains("Link Shortener");

        cy.setLanguage("pt-br");
    })
});

describe("Navitate to auth pages", () => {
    it("access login page", () => {
        cy.visit("localhost:8000");
        cy.setLanguage("pt-br"); // força português
        cy.get('a[href="/account/login/"]').first().click()
        cy.contains("Bem-vindo de volta!")
    })
    it("access register page", () => {
        cy.visit("localhost:8000");
        cy.setLanguage("pt-br"); // força português
        cy.get('a[href="/account/register/"]').first().click()
        cy.contains("Crie sua conta!")
    })
})

describe("Navitate to footer pages", () => {
    it("access privacy policy page", () => {
        cy.visit("localhost:8000");
        cy.setLanguage("pt-br");
        cy.get('a[href="/info/privacy-policy/"]').first().click()
        cy.contains("Política de Privacidade")
    })
    it("access home page", () => {
        cy.visit("localhost:8000");
        cy.setLanguage("pt-br");
        cy.get('a[href="/"]').first().click()
        cy.contains("Encurtador de Links")
    })
    it("access about us page", () => {
        cy.visit("localhost:8000");
        cy.setLanguage("pt-br");
        cy.get('a[href="/info/about-us/"]').first().click()
        cy.contains("Sobre a Shortly")
    })
})
