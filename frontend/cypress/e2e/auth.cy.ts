// frontend/cypress/e2e/auth.cy.ts

describe('Pineapple Authentication Flow', () => {
  beforeEach(() => {
    // Nettoyer l'état local avant chaque test
    cy.clearLocalStorage();
    cy.clearCookies();
  });

  it('should login successfully and redirect to the campus feed', () => {
    // Données factices pour le test
    const fakeTenantId = '11111111-1111-1111-1111-111111111111';
    const fakeUser = {
      id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      email: 'etudiant1@enspd.cm',
      first_name: 'Alice',
      last_name: 'Ndongo',
      matricule: 'ENSPD2026001',
      faculty: 'Génie Logiciel',
      filiere: 'Informatique',
      academic_year: '2026-2027',
      account_status: 'ACTIVE',
      verification_status: 'VERIFIED',
      academic_status: 'STUDENT',
      campus_status_display: 'Étudiant certifié',
    };
    const fakeToken = 'fake-jwt-token-abc123';

    // Intercepter l'appel de connexion et répondre avec un token
    cy.intercept('POST', '/api/v1/identity/login', {
      statusCode: 200,
      body: {
        access_token: fakeToken,
        token_type: 'bearer',
        user_id: fakeUser.id,
        tenant_id: fakeTenantId,
      },
    }).as('loginRequest');

    // Intercepter la récupération du profil après connexion
    cy.intercept('GET', '/api/v1/identity/me', {
      statusCode: 200,
      body: fakeUser,
    }).as('meRequest');

    // Visiter la page de connexion
    cy.visit('/login');

    // Vérifier que le formulaire est visible
    cy.contains('Connexion').should('be.visible');

    // Remplir le sélecteur de campus (code tenant)
    // Le select est un élément <select> avec options : ENSPD, UDo, ENS.
    cy.get('select').select('ENSPD');

    // Remplir l'email et le mot de passe
    cy.get('input[type="email"]').type(fakeUser.email);
    cy.get('input[type="password"]').type('Etudiant123!');

    // Soumettre le formulaire
    cy.get('button[type="submit"]').click();

    // Attendre que l'appel API de connexion soit effectué
    cy.wait('@loginRequest').its('request.body').should('deep.equal', {
      email: fakeUser.email,
      password: 'Etudiant123!',
    });

    // Attendre l'appel pour récupérer le profil
    cy.wait('@meRequest');

    // Vérifier que l'URL a changé vers la racine '/'
    cy.url().should('eq', Cypress.config().baseUrl + '/');

    // Vérifier que le nom de l'utilisateur apparaît dans le header ou le feed
    // On suppose que le header affiche l'avatar, mais le nom peut être dans un menu.
    // On peut vérifier la présence du prénom quelque part sur la page.
    cy.contains('Alice').should('exist');
    cy.contains('Étudiant certifié').should('exist');
  });

  it('should show an error message on invalid credentials', () => {
    // Stub de l'API pour retourner 401
    cy.intercept('POST', '/api/v1/identity/login', {
      statusCode: 401,
      body: { detail: 'Invalid email or password' },
    }).as('loginInvalid');

    cy.visit('/login');

    cy.get('select').select('ENSPD');
    cy.get('input[type="email"]').type('wrong@example.com');
    cy.get('input[type="password"]').type('wrongpass');
    cy.get('button[type="submit"]').click();

    cy.wait('@loginInvalid');

    // Vérifier que le message d'erreur s'affiche
    cy.contains('Identifiants invalides').should('be.visible');
    // L'URL doit rester /login
    cy.url().should('include', '/login');
  });
});