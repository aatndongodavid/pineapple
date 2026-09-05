// frontend/src/lib/api/endpoints.ts

export const API_ENDPOINTS = {
  identity: {
    register: '/api/v1/identity/register',
    login: '/api/v1/identity/login',
    me: '/api/v1/identity/me',
    certificationSubmit: '/api/v1/identity/certification/submit',
    certificationReview: '/api/v1/identity/certification/review',
  },
  community: {
    feed: '/api/v1/community/feed',
    posts: '/api/v1/community/posts',
    organizations: '/api/v1/community/organizations',
    rooms: '/api/v1/community/rooms',
    declareRoom: '/api/v1/community/rooms/declare',
  },
  democracy: {
    elections: '/api/v1/democracy/elections',
    vote: (electionId: string) => `/api/v1/democracy/elections/${electionId}/vote`,
    tally: (electionId: string) => `/api/v1/democracy/elections/${electionId}/tally`,
    audit: (electionId: string) => `/api/v1/democracy/elections/${electionId}/audit`,
  },
  academy: {
    library: '/api/v1/academy/library',
    upload: '/api/v1/academy/library/upload',
    purchase: '/api/v1/academy/premium/purchase',
    readerStream: (documentId: string) => `/api/v1/academy/reader/${documentId}/stream`,
  },
  campusLife: {
    marketplace: '/api/v1/campus-life/marketplace',
    rides: '/api/v1/campus-life/ride',
    bookRide: (rideId: string) => `/api/v1/campus-life/ride/${rideId}/book`,
    messages: (conversationId: string) => `/api/v1/campus-life/messages/${conversationId}`,
    sendMessage: '/api/v1/campus-life/messages',
  },
  opportunities: {
    list: '/api/v1/opportunities',
    create: '/api/v1/opportunities',
    apply: (opportunityId: string) => `/api/v1/opportunities/${opportunityId}/apply`,
  },
  monetization: {
    sponsoring: '/api/v1/monetization/sponsoring',
    licenseStatus: '/api/v1/monetization/license/status',
  },
  trustSafety: {
    report: '/api/v1/trust-safety/report',
    moderationReview: '/api/v1/trust-safety/moderation/review',
  },
};