# Alokit_Onebox: Real-Time Email Synchronization Service

**Assignment for: Associate Backend Engineer @ ReachInbox**

---

## Overview

This project is a robust backend service designed to provide real-time, two-way synchronization with an email account using the IMAP protocol. It continuously listens for new emails, fetches historical messages, and is built to be scalable and resilient. This document covers the first functional requirement (FR-1), focusing on email synchronization.

---

## FR-1: Real-Time Email Synchronization

This is the core feature of the application, enabling seamless integration with any IMAP-based email server like Gmail.

### Key Features

-   **Secure IMAP Connection**: Establishes a secure and stable connection to the user's email server using `node-imap`.
-   **Historical Email Sync**: On initial startup, the service fetches all emails from the last 30 days to build a complete inbox view.
-   **Real-Time Email Detection**: Utilizes the **IMAP IDLE** command to listen for new emails in real-time, ensuring the application is updated within seconds of an email's arrival.
-   **Robust Error Handling & Reconnection**: Includes an automatic reconnection manager that attempts to re-establish a connection in case of network failures or timeouts, ensuring high availability.
-   **Safe Configuration**: Manages sensitive credentials securely using a `.env` file, which is excluded from version control via `.gitignore`.

### Architecture & Data Flow

The following diagram illustrates the flow of data from the IMAP server to the service.

```mermaid
graph TD
    subgraph "Email Provider"
        A[IMAP Server e.g., Gmail]
    end

    subgraph "Onebox Aggregator Service"
        B[IMAP Service]
        C[Sync Manager]
        D[Idle Manager]
        E[Logger]
    end

    subgraph "Future Implementation"
        F[Elasticsearch]
    end

    A -- 1. Establishes Connection --> B;
    B -- 2. Opens Mailbox --> A;
    B -- 3. Initiates Historical Sync --> C;
    C -- 4. Fetches Last 30 Days of Emails --> A;
    C -- 5. Parses and Logs Emails --> E;
    B -- 6. Enters IDLE Mode --> D;
    D -- 7. Listens for New Mail Events --> A;
    A -- 8. Pushes New Email Notification --> D;
    D -- 9. Triggers New Email Fetch --> C;

    C -- "Indexes Email (FR-2)" -.-> F
```

---

## Tech Stack

-   **Backend**: Node.js
-   **Language**: TypeScript
-   **IMAP Communication**: `node-imap`
-   **Environment Management**: `dotenv`
-   **Logging**: `winston`
-   **Development**: `nodemon`, `ts-node`

---

## Setup and Installation

Follow these steps to get the project running on your local machine.

### Prerequisites

-   Node.js (v18 or higher)
-   npm

### 1. Clone the Repository

```bash
git clone https://github.com/ALOK-Yeager/Alokit_Onebox.git
cd onebox_aggregator
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

Create a `.env` file in the root of the project by copying the example file:

```bash
# For Windows (Command Prompt)
copy .env.example .env

# For Windows (PowerShell)
cp .env.example .env

# For macOS/Linux
cp .env.example .env
```

Now, open the `.env` file and fill in your IMAP server details.

```properties
# Your email provider's IMAP server (e.g., imap.gmail.com)
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993

# Your email address and password
# IMPORTANT: For Gmail, you must generate an "App Password".
# See: https://support.google.com/accounts/answer/185833
IMAP_USER=your-email@example.com
IMAP_PASSWORD=your-app-password

# Enable TLS (recommended)
IMAP_TLS=true
```

---

## Running the Application

### Development Mode

To run the application with hot-reloading, use the `dev` script. This will automatically restart the server when you make changes to the code.

```bash
npm run dev
```

### Build for Production

To compile the TypeScript code into JavaScript, run the build command:

```bash
npm run build
```

The compiled output will be in the `dist/` directory.

### Running in Production

After building the project, you can run the compiled code directly with Node.js:

```bash
node dist/main.js
```

---

## FR-2: Searchable Storage with Elasticsearch

*(This section will be updated upon completion of the second functional requirement.)*

