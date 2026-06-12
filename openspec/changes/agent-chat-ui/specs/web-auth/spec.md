# web-auth

## ADDED Requirements

### Requirement: Self-signup enabled on the user pool
The Lapwise Cognito User Pool SHALL allow self-signup with email as the sign-in alias and automatic email verification. The app client SHALL enable the SRP auth flow.

#### Scenario: Infra supports public registration
- **WHEN** the updated `infra/` stack is deployed
- **THEN** the User Pool has `selfSignUpEnabled: true` with email auto-verification and the app client allows `USER_SRP_AUTH`

### Requirement: Signup with email verification
The app SHALL provide a signup page collecting email and password, registering the user via the Cognito SDK, then routing to a verification page where the user enters the emailed code. Successful verification SHALL route to signin (or sign the user in directly).

#### Scenario: Successful signup and verification
- **WHEN** a new user submits a valid email and password, then enters the correct verification code
- **THEN** their account is confirmed and they can sign in

#### Scenario: Signup errors are surfaced
- **WHEN** signup fails (existing email, weak password per pool policy)
- **THEN** the specific Cognito error is shown inline next to the relevant field, not as a raw exception or generic failure

#### Scenario: Resend verification code
- **WHEN** a user on the verify page requests a new code
- **THEN** Cognito resends the code and the UI confirms it was sent

### Requirement: Signin and session establishment
The app SHALL provide a signin page authenticating via SRP and establishing a Cognito session (ID, access, refresh tokens) cached by the SDK. Failed signin SHALL show the specific error; unconfirmed users SHALL be routed to the verification page.

#### Scenario: Successful signin
- **WHEN** a confirmed user submits correct credentials
- **THEN** a session is established and the user lands on the chat page

#### Scenario: Unconfirmed user is routed to verification
- **WHEN** a user who never completed email verification attempts signin
- **THEN** they are routed to the verify page for their email

### Requirement: Token usage and refresh
The app SHALL send the Cognito ID token as the bearer token to the AgentCore runtime and the access token to the Lapwise HTTP API, refreshing expired tokens transparently via the refresh token before each request. When refresh fails, the user SHALL be signed out and redirected to `/signin`.

#### Scenario: Expired token is refreshed transparently
- **WHEN** a request is initiated after the access/ID token has expired but the refresh token is valid
- **THEN** the token is refreshed automatically and the request succeeds without user interaction

#### Scenario: Invalid session forces re-authentication
- **WHEN** token refresh fails
- **THEN** local session state is cleared and the user is redirected to `/signin`

### Requirement: Signout
The app SHALL provide a signout control that clears the Cognito session and all local conversation state, returning to `/signin`.

#### Scenario: Signout clears session
- **WHEN** the user clicks sign out
- **THEN** tokens are cleared, in-memory conversation state is reset, and the app shows `/signin`
