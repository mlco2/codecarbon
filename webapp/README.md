# Next.js Code Carbon Web Application Project

Welcome to the Code Carbon Next.js Project! This README will guide you through the process of setting up and running the project on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- Node.js (version 14 or later)
- npm (usually comes with Node.js)
- Git

## Getting Started

Follow these steps to get the project up and running on your local machine:

1. **Open a terminal and go to the /webapp folder**

   ```bash
   cd webapp
   ```

2. **Install dependencies**

   ```bash
   npm install
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
   npm run dev
   ```

   The application should now be running on [http://localhost:3000](http://localhost:3000).

## Available Scripts

In the project directory, you can run:

- `npm run dev`: Runs the app in development mode
- `npm run build`: Builds the app for production
- `npm start`: Runs the built app in production mode
- `npm run lint`: Runs the linter to check for code style issues

## Learn More

To learn more about Next.js, check out the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

