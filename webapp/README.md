# Code Carbon Web Application Project

Welcome to the Code Carbon Project! This README will guide you through the process of setting up and running the project on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

-   Node.js 24 or later
-   pnpm — run `corepack enable` (bundled with Node 24) to get the exact version
    pinned in `package.json`, or see https://pnpm.io/installation
-   Git

## Getting Started

> Contributing with an AI agent? Read [AGENTS.md](./AGENTS.md) first — it holds
> the webapp's conventions and the expected workflow.

Follow these steps to get the project up and running on your local machine:

1. **Open a terminal and go to the /webapp folder**

    ```bash
    cd webapp
    ```

2. **Install dependencies**

    ```bash
    pnpm install
    ```

3. **Set up environment variables**

    This project uses environment variables for configuration. You need to create a `.env` file in the root directory of the project.

    - Copy the `.env.example` file and rename it to `.env`:

        ```bash
        cp .env.example .env
        ```

    - Open the `.env` file and fill in the necessary values for your local environment.

4. **Run the development server**

    ```bash
    pnpm dev
    ```

    The application should now be running on [http://localhost:3000](http://localhost:3000).

## Available Scripts

In the project directory, you can run:

-   `pnpm dev`: Runs the app in development mode
-   `pnpm build`: Builds the app for production
-   `pnpm preview`: Serves the production build locally
-   `pnpm lint`: Runs the linter to check for code style issues
-   `pnpm test:run`: Runs the unit tests once

## Dependencies

We use pnpm rather than npm for its supply-chain safeguards, set in
`pnpm-workspace.yaml`: dependencies may not run install scripts unless
allow-listed, and versions published less than 7 days ago are not installed.

`pnpm-lock.yaml` is the only lockfile — commit it with every dependency change
and never add a `package-lock.json`. CI and the production build (Clever Cloud,
see the contributing guide) both install with
`pnpm install --frozen-lockfile`, which fails if the lockfile is out of date.
