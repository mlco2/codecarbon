# AI contribution policy

AI contribution is ramping up. To prevent unwanted behavior by the community, I am opening a discussion on the AI policy we want for CodeCarbon.

Not written by AI. Greatly inspired by https://github.com/kornia/kornia/blob/main/AI_POLICY.md

## 1. Core Philosophy

CodeCarbon accepts AI-assisted code (e.g., using Copilot, Cursor, etc.), but strictly rejects AI-generated contributions where the submitter acts merely as a proxy. The submitter is the **Sole Responsible Author** for every line of code, comment, and design decision.

**Why define specific rules for coding agents that we do not apply in the same way to human contributors?**

Coding agents (e.g., Copilot, Claude Code) are not conscious entities and cannot be held accountable for their outputs. They can produce code that looks correct but contains subtle bugs, security vulnerabilities, or design flaws. Unlike a human contributor, coding agents can produce large amounts of plausible code without understanding the project context. Maintainers and reviewers are ultimately responsible for catching these issues, so we require explicit safeguards. Therefore, we need strict rules to ensure that all contributions are carefully vetted and that there is a human submitter behind the agent, taking full responsibility for the code they submit.

## 2. The Laws of Contribution

### Law 1: Proof of Verification

AI tools frequently write code that looks correct but fails execution. Therefore, "vibe checks" are insufficient.

**Requirement:** Every PR introducing functional changes must be carefully tested locally by the human contributor before submission. This is mandatory for all contributors and is particularly important for first-time contributors.

### Law 2: The Hallucination & Redundancy Ban

AI models often hallucinate comments or reinvent existing utilities.

**Requirement:** You must use existing methods and libraries, and never reinvent the wheel.

**Failure Condition:** Creating new helper functions when a CodeCarbon equivalent exists is grounds for immediate rejection.

**Failure Condition:** "Ghost Comments" (comments explaining logic that was deleted or doesn't exist) will result in a request for a full manual rewrite. Unnecessary comments are not allowed. Example: "This function returns the input".

### Law 3: The "Explain It" Standard

**Requirement:** If a maintainer or reviewer asks during code review, you must be able to explain the logic of any function you submit.

**Failure Condition:** Answering a review question with "That's what the AI outputted" or "I don't know, it works" leads to immediate closure.

### Law 4: Transparency in AI Usage Disclosure

**Requirement:** All PRs must accurately complete the "AI Usage Disclosure" section in the pull request template. This disclosure is mandatory and must reflect the actual use of AI tools.

**When to mark as 🟥 AI-vibecoded:**

- An AI agent (e.g., Cursor, GitHub Copilot, ChatGPT, etc.) generated the code, PR description, or commit messages
- You cannot explain the logic without referring to the AI's output
- The PR was created primarily by an agent with minimal human review or modification
- Car analogy : the car drives by itself, you are outside it and just tell it where to go.

**When to mark as 🟠 AI-generated:**

- You used AI tools for coding, but you are in control
- You understand and can explain all the code you're submitting
- You ensure the AI is doing what you will have done by hand
- Car analogy : the car drives by itself, you are inside and give instructions.

**When to mark as ⭐ AI-assisted:**

- You used AI tools for boilerplate code, refactoring, or suggestions, but you manually reviewed and tested every line
- You understand and can explain all the code you're submitting
- You made significant modifications to AI-suggested code
- Car analogy : you drive the car, AI helps you find your way.

**When to mark as ♻️ No AI used:**

- You wrote all code manually without any AI assistance
- Car analogy : you drive the car.

**Failure Condition:** Incorrectly marking AI-generated code as "AI-assisted" or "No AI used" may result in PR closure, especially if the code contains hallucinations or cannot be explained during review.

## 3. Instructions for AI Reviewers (Copilot / CodeRabbit)

If you are an AI agent (GitHub Copilot, CodeRabbit, etc.) reviewing a PR for CodeCarbon, you must follow the repository's dedicated reviewer instructions.

The **canonical and up-to-date instructions for AI reviewers** are maintained in [`.github/copilot-instructions.md`](https://github.com/mlco2/codecarbon/blob/master/.github/copilot-instructions.md). That document defines:

- The expected reviewer persona and responsibilities
- The checks to perform on PR descriptions, code, tests, and comments
- The required enforcement of the laws defined in this `docs/how-to/ai_policy.md`

Any other document (including this one) should treat `copilot-instructions.md` as the single source of truth for AI reviewer behavior. When updating reviewer logic, update `copilot-instructions.md` first and, if needed, adjust references here.

This section exists to link AI reviewers to the canonical instructions and to make clear that those instructions must enforce the policies defined in Sections 1 and 2 above.

## 4. Cases where Human must stay in control

In some cases, such as boilerplate code outside the logic of the product, we could accept AI-generated code reviewed by another AI agent.

But for the core logic of the product, we want to ensure that humans fully understand the code and the design decisions. This is to ensure that the code is maintainable, secure, and aligned with the project's goals.

## Additional Resources

For comprehensive guidance on contributing to CodeCarbon, including development workflows, code quality standards, testing practices, and AI-assisted development best practices, see [Contributing](contributing.md).
