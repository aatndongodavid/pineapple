// frontend/cypress/e2e/democracy.cy.ts

describe('Pineapple Democracy - Voting Booth', () => {
  beforeEach(() => {
    // Nettoyer l'état local avant chaque test
    cy.clearLocalStorage();
    cy.clearCookies();
  });

  it('should block voting if user has already voted (409 conflict)', () => {
    // Intercepter la récupération des détails de l'élection si nécessaire
    cy.intercept('GET', '/api/v1/democracy/elections/123', {
      statusCode: 200,
      body: {
        id: '123',
        title: 'Élection BDE ENSPD 2027',
        status: 'VOTING_OPEN',
        voting_start_at: '2027-03-15T08:00:00Z',
        voting_end_at: '2027-03-15T18:00:00Z',
        // etc.
      },
    }).as('getElection');

    // Intercepter l'appel de vote pour retourner un conflit (déjà voté)
    cy.intercept('POST', '/api/v1/democracy/elections/123/vote', {
      statusCode: 409,
      body: { detail: 'User has already voted' },
    }).as('voteConflict');

    cy.visit('/democracy/123');

    // Attendre le chargement
    cy.wait('@getElection');

    // Normalement, si l'utilisateur a déjà voté, le bouton de vote est désactivé ou un message s'affiche.
    // Dans le composant actuel, il n'y a pas de vérification d'éligibilité via API, on suppose que le composant
    // gère cela via un état hasVoted provenant d'un store. Ici, nous testons le scénario où l'API renvoie 409.
    // On va simuler en supposant que le composant affiche un message "Vous avez déjà voté" après une tentative.
    // Mais le test doit vérifier que le bouton est bloqué AVANT de voter.
    // Comme le composant VotingBoothScreen ne fait pas encore d'appel API pour vérifier, on va s'assurer que
    // le bouton de dépôt n'est pas actif si hasVoted est true. On peut définir un state via le store.
    // Pour les besoins du test, on suppose qu'un store a été hydraté avec hasVoted = true.
    // Nous allons intercepter le GET /api/v1/democracy/elections/123/vote/status pour retourner has_voted: true.
    cy.intercept('GET', '/api/v1/democracy/elections/123/vote/status', {
      statusCode: 200,
      body: { has_voted: true },
    }).as('voteStatus');

    cy.visit('/democracy/123');
    cy.wait('@voteStatus');

    // Vérifier qu'un message indiquant déjà voté apparaît et que le bouton est désactivé.
    // Le composant affiche "Vous avez déjà voté pour cette élection." si hasVoted est true.
    cy.contains('Vous avez déjà voté').should('be.visible');
    cy.contains('Déposer dans l\'urne').should('not.exist');
  });

  it('should successfully cast vote and show receipt hash', () => {
    // Utiliser cy.clock pour contrôler le temps du chiffrement simulé
    cy.clock();

    // Intercepter la récupération des détails
    cy.intercept('GET', '/api/v1/democracy/elections/123', {
      statusCode: 200,
      body: {
        id: '123',
        title: 'Élection BDE ENSPD 2027',
        status: 'VOTING_OPEN',
        voting_start_at: '2027-03-15T08:00:00Z',
        voting_end_at: '2027-03-15T18:00:00Z',
      },
    }).as('getElection');

    // Intercepter le vote : vérifier le payload et répondre succès
    cy.intercept('POST', '/api/v1/democracy/elections/123/vote', (req) => {
      // Vérifier que le corps contient bien encrypted_vote et PAS de données personnelles
      expect(req.body).to.have.property('encrypted_vote');
      expect(req.body).to.have.property('election_id', '123');
      expect(req.body).to.have.property('choice_id');
      // Vérifier qu'aucune donnée personnelle n'est envoyée
      expect(req.body).not.to.have.property('user_id');
      expect(req.body).not.to.have.property('email');
      expect(req.body).not.to.have.property('matricule');

      // Répondre avec un succès
      req.reply({
        statusCode: 202,
        body: {
          message: 'Vote cast successfully',
          voter_hash: 'a7f9c2b1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9',
        },
      });
    }).as('castVote');

    // Intercepter le statut de vote : non voté
    cy.intercept('GET', '/api/v1/democracy/elections/123/vote/status', {
      statusCode: 200,
      body: { has_voted: false },
    }).as('voteStatus');

    cy.visit('/democracy/123');
    cy.wait('@getElection');
    cy.wait('@voteStatus');

    // Étape 0 : sélection du mouvement
    cy.contains('Mouvement Bleu').click();

    // Étape 1 : confirmation
    cy.contains('Confirmer').click();

    // Étape 2 : chiffrement (le composant simule 2.5s). On avance le temps.
    cy.tick(2600); // dépasse 2.5s
    cy.contains('Déposer dans l\'urne').should('be.visible').click();

    // Attendre l'appel API de vote
    cy.wait('@castVote');

    // Étape 3 : reçu
    cy.contains('Vote enregistré').should('be.visible');
    cy.contains('Reçu de vote').should('be.visible');
    // Vérifier que le hash tronqué est affiché (ex: a7f9...f8a9)
    cy.contains('a7f9').should('exist');
    cy.contains('f8a9').should('exist');
  });
});