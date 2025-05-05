# Fly.io Deployment

This document outlines the process for deploying and updating the agent on Fly.io.

## Prerequisites

1.  **Fly.io Account:** Ensure you have an account at [fly.io](https://fly.io/).
2.  **Fly CLI:** Install the Fly command-line interface. Instructions can be found [here](https://fly.io/docs/hands-on/install-flyctl/).
3.  **Logged In:** Make sure you are logged into the Fly CLI using `fly auth login`.
4.  **Project Setup:** This project should already be configured with a `fly.toml` and `Dockerfile`.
5.  **Secrets:** Ensure required environment variables (like LiveKit keys) are set as secrets in Fly.io using `fly secrets set VAR1=value1 VAR2=value2 ...` or `fly secrets set $(cat .env)`.

## Updating the Deployment

To deploy the latest version of your code to the configured Fly.io app (`agent1` in this case):

1.  **Navigate to Project Directory:** Open your terminal and change to the project's root directory:
    ```bash
    cd /path/to/your/agent1/project
    ```
2.  **(Optional) Commit Changes:** It's good practice to commit your latest code changes to version control:
    ```bash
    git add .
    git commit -m "Prepare for fly deployment"
    git push # Optional, depending on your workflow
    ```
3.  **Deploy:** Run the deploy command. Fly.io will use the `fly.toml` and `Dockerfile` in the current directory to build and deploy your application.
    ```bash
    fly deploy
    ```

Fly.io will build the Docker image, push it to its registry, and then deploy the new version according to the strategy defined in `fly.toml` (e.g., bluegreen). You can monitor the deployment progress in your terminal.


