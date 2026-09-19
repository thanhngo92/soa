# Frontend Architecture Specification

The Frontend subsystem is built using **React + Vite + Tailwind CSS + Shadcn UI + JavaScript**.

* **Core & Build Tool:** React + Vite
* **Styling & Design System:** Tailwind CSS + Shadcn UI Primitives
* **Icons:** Lucide React
* **Language:** JavaScript
* **Port:** `3659`
* **API Gateway Base URL:** `http://localhost:8877/api`

---

## 1. Data Flow

```text
page ──> component ──> utils ──> hooks ──> context ──> services ──> backend
```

### Data Flow Principles:
1. **`page`**: Top-level route view tied to URL paths, coordinating child layout components.
2. **`component`**: Receives props, renders user interface elements, and handles UI events (`onClick`, `onChange`, `onSubmit`).
3. **`utils`**: Pure functions for data formatting and input validation.
4. **`hooks`**: Encapsulates stateful logic, loading indicators (`isLoading`, `error`), and triggers services or context.
5. **`context`**: Manages global application state.
6. **`services`**: Executes HTTP requests via the centralized Axios client (`lib/api.js`) to the API Gateway.
7. **`backend`**: Distributed microservices handling business logic behind the API Gateway.

---

## 2. Directory Skeleton

```text
frontend/
├── index.html
├── vite.config.js               # Dev server port 3659, '@' alias mapping to '/src'
├── package.json
├── tailwind.config.js           # HSL design tokens & animation configuration
├── postcss.config.js
├── README.md
│
└── src/
    ├── main.jsx                 # Application entrypoint initializing React DOM
    ├── App.jsx                  # Root Component: Routing & Provider configuration
    ├── index.css                # Tailwind directives & CSS custom properties
    │
    ├── lib/                     # Infrastructure & shared utilities
    │   ├── api.js               # Axios instance
    │   └── utils.js             # ClassName merger utility cn (clsx + twMerge)
    │
    ├── utils/                   # Pure Helper Functions
    │   ├── formatters.js        # Currency and date formatting helpers
    │   └── validators.js        # Form and regex validation helpers
    │
    ├── services/                # API Communication Layer
    │   ├── authService.js       # Authentication endpoints
    │   ├── tuitionService.js    # Tuition query endpoints
    │   └── paymentService.js    # Payment initiation & confirmation endpoints
    │
    ├── context/                 # Global Application State
    │   └── AuthContext.jsx      # Authentication session & token storage
    │
    ├── hooks/                   # Custom React Hooks
    │   ├── useAuth.js           # AuthContext consumer
    │   └── useCountdown.js      # Countdown timer for OTP validity
    │
    ├── components/              # UI Components
    │   ├── Navbar.jsx           # Main navigation header
    │   ├── ProtectedRoute.jsx   # Route authentication guard
    │   ├── OtpModal.jsx         # 6-digit OTP modal dialog
    │   ├── ReceiptModal.jsx     # Payment receipt confirmation dialog
    │   │
    │   └── ui/                  # Shadcn Primitive Components
    │       ├── button.jsx       # Standard button variants
    │       ├── input.jsx        # Standard text input
    │       ├── card.jsx         # Card containers
    │       ├── badge.jsx        # Status badge indicator
    │       ├── dialog.jsx       # Radix dialog modal primitive
    │       └── separator.jsx    # Visual divider
    │
    └── pages/                   # Route-level Page Views
        ├── LoginPage.jsx        # Authentication view
        ├── TuitionPaymentPage.jsx # Tuition search & settlement view
        └── HistoryPage.jsx      # Transaction history view
```

---

## 3. Layer Responsibilities

| Layer / Folder | Responsibility | Constraints |
| :--- | :--- | :--- |
| **`lib/`** | Configures the HTTP client (`api.js`) and UI helper utilities (`utils.js`). | No React state or hooks dependencies. Contains no JSX. |
| **`components/ui/`** | Atomic UI primitives in Shadcn style (`button.jsx`, `input.jsx`, `card.jsx`, etc.). | Contains no domain business logic or API calls. Renders strictly from props. |
| **`components/`** | Shared composite application components (`Navbar`, `OtpModal`, `ProtectedRoute`). | Does not call `services/` directly; accepts handlers via props or custom hooks. |
| **`pages/`** | Route-level views managing child component layouts. | Does not call `api.js` directly; delegates data fetching to services. |
| **`utils/`** | Pure functions: formatters, validators, calculations. | No React hooks, no JSX. Same input always yields identical output. |
| **`hooks/`** | Manages component lifecycles, timers, and async operations. | No raw `fetch`/`axios` calls; returns logic state, not JSX. |
| **`context/`** | Holds and broadcasts global application state. | Handles no direct UI rendering. Pure state and dispatchers. |
| **`services/`** | Declares endpoints and executes requests via `lib/api.js`. | No React state (`useState`); errors are forwarded to caller. |

---

## 4. Routing & Layout Architecture Rules

1. **Centralized Routing (`src/App.jsx`):**
   - Implemented via `react-router-dom`.
   - `Public Route`: `/login`.
   - `Protected Routes`: `/` and `/history`, protected by `ProtectedRoute`.
   - Fallback route: Wildcard redirect to `/`.

2. **Route Guards (`ProtectedRoute.jsx`):**
   - Validates authentication state from `AuthContext`.
   - Unauthenticated requests to protected views are redirected to `/login`.

3. **Layout Composition:**
   - Unauthenticated views render standalone login card without navigation header.
   - Protected views render with global `Navbar` navigation.

---

## 5. Development Commands

```bash
# Install dependencies
npm install

# Start Vite dev server on port 3659
npm run dev

# Build production bundle
npm run build

# Preview production build
npm run preview
```
