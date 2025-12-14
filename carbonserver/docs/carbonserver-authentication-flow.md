# CodeCarbon Server Authentication Flow

This diagram illustrates the authentication flow in the CodeCarbon API server (carbonserver).

## Authentication Methods

The server supports three authentication methods:

1. **OAuth2/Cookie-based (Web Browser)**: For web dashboard access using Fief OAuth
2. **Bearer Token (CLI/API)**: For programmatic access using JWT tokens
3. **API Key/Project Tokens**: For automated data submission using project-specific tokens

## Flow Diagram

```mermaid
flowchart TD
    Start([User/Client Requests API]) --> CheckAuthType{Authentication Type?}
    
    %% OAuth2 / Cookie-based Web Flow
    CheckAuthType -->|Web Browser| WebFlow[Web Access]
    WebFlow --> HasCookie{Has Session Cookie?}
    
    HasCookie -->|No Cookie| RedirectLogin[Redirect to /auth/login]
    RedirectLogin --> FiefAuth[Redirect to Fief OAuth Server]
    FiefAuth --> UserAuth[User Authenticates<br/>at Fief]
    UserAuth --> AuthCode[Fief Returns Auth Code]
    AuthCode --> ExchangeToken[POST to Fief /api/token<br/>with auth code]
    ExchangeToken --> GetTokens[Receive Access Token<br/>& ID Token]
    GetTokens --> CheckUserDB{User Exists<br/>in DB?}
    CheckUserDB -->|No| CreateUser[SignUpService.check_jwt_user<br/>creates user]
    CheckUserDB -->|Yes| UserExists[User Found]
    CreateUser --> SetCookie[Set user_session Cookie<br/>with access token]
    UserExists --> SetCookie
    SetCookie --> RedirectApp[Redirect to Frontend<br/>with credentials]
    RedirectApp --> Authorized[Access Granted]
    
    HasCookie -->|Has Cookie| DecodeCookie[Decode JWT from Cookie]
    DecodeCookie --> GetUserDB[Get User from DB<br/>by JWT 'sub' claim]
    GetUserDB --> CheckUserExists{User Found?}
    CheckUserExists -->|Yes| Authorized
    CheckUserExists -->|No| Unauthorized[401 Unauthorized]
    
    %% Bearer Token Flow (CLI/API)
    CheckAuthType -->|Bearer Token| BearerFlow[API/CLI Access]
    BearerFlow --> ValidateBearer{Environment?}
    ValidateBearer -->|Production| ValidateFief[fief.validate_access_token]
    ValidateBearer -->|Development| SkipValidation[Skip Validation<br/>or use JWT_KEY]
    ValidateFief --> TokenValid{Token Valid?}
    TokenValid -->|No| Unauthorized
    TokenValid -->|Yes| DecodeBearer[Decode JWT Token]
    SkipValidation --> DecodeBearer
    DecodeBearer --> GetUserBearer[Get User from DB<br/>by JWT 'sub' claim]
    GetUserBearer --> CheckUserBearer{User Found?}
    CheckUserBearer -->|Yes| Authorized
    CheckUserBearer -->|No| Unauthorized
    
    %% API Key Flow (Project Tokens)
    CheckAuthType -->|x-api-token Header| APIKeyFlow[Project Token Access]
    APIKeyFlow --> ExtractToken[Extract x-api-token<br/>from Header]
    ExtractToken --> GenerateLookup[Generate Lookup Value<br/>SHA256 first 8 chars]
    GenerateLookup --> FindTokens[Find Tokens by Lookup<br/>in project_tokens table]
    FindTokens --> VerifyHash[Verify API Key with bcrypt<br/>against stored hash]
    VerifyHash --> TokenMatches{Token Valid?}
    TokenMatches -->|No| Unauthorized
    TokenMatches -->|Yes| CheckAccess{Check Access Level}
    CheckAccess -->|READ/WRITE| CheckScope{Check Scope}
    CheckScope -->|run_id| ValidateRun[Validate token has<br/>access to run]
    CheckScope -->|experiment_id| ValidateExp[Validate token has<br/>access to experiment]
    CheckScope -->|project_id| ValidateProj[Validate token has<br/>access to project]
    ValidateRun --> AccessValid{Access Valid?}
    ValidateExp --> AccessValid
    ValidateProj --> AccessValid
    AccessValid -->|Yes| Authorized
    AccessValid -->|No| Unauthorized
    
    %% Final States
    Authorized --> ProcessRequest[Process API Request]
    ProcessRequest --> Response([Return Response])
    Unauthorized --> ErrorResponse([Return 401 Error])
    
    %% Styling - Dark mode friendly colors
    classDef successClass fill:#2d5016,stroke:#4ade80,stroke-width:3px,color:#fff
    classDef errorClass fill:#5c1a1a,stroke:#f87171,stroke-width:3px,color:#fff
    classDef processClass fill:#1e3a5f,stroke:#60a5fa,stroke-width:3px,color:#fff
    classDef decisionClass fill:#5c3a00,stroke:#fbbf24,stroke-width:3px,color:#fff
    
    class Authorized,ProcessRequest,Response successClass
    class Unauthorized,ErrorResponse errorClass
    class WebFlow,BearerFlow,APIKeyFlow,DecodeCookie,DecodeBearer,ExtractToken,ValidateFief processClass
    class CheckAuthType,HasCookie,CheckUserDB,CheckUserExists,ValidateBearer,TokenValid,CheckUserBearer,TokenMatches,CheckAccess,CheckScope,AccessValid decisionClass
```

## Key Components

### OAuth2 Web Flow
- Uses **Fief** as the OAuth2 provider
- Cookie name: `user_session`
- Auto-creates users in local DB on first login
- Scopes: `openid`, `email`, `profile`

### Bearer Token (CLI/API)
- JWT tokens validated via Fief in production
- Development mode allows test tokens with `JWT_KEY`
- Used by the `codecarbon` CLI tool

### Project Tokens (API Keys)
- Prefix: `cpt_` (codecarbon project token)
- Hashed with bcrypt for secure storage
- SHA256 lookup optimization (first 8 chars)
- Scoped to specific projects/experiments/runs
- Access levels: READ, WRITE

## Key Files

- `carbonserver/api/routers/authenticate.py` - Authentication routes
- `carbonserver/api/services/auth_service.py` - Auth dependency injection
- `carbonserver/api/services/signup_service.py` - User creation logic
- `carbonserver/api/infra/api_key_utils.py` - API key generation/verification
