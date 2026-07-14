# 50-HACK2SKILL-competition-rules

---
### Source: `30-hack2skill-rules.md`
---

---
trigger: inactive
---

# Hack2Skill Challenge Rules & Instructions

This master rule document governs the entire repository, directly echoing the official Hack2Skill Challenge instructions. All agentic workflows, architecture designs, and development processes must align with these mandates.

## 1. Before You Begin
Make sure the following prerequisites are completed:
- The AI platform that you are going to use is downloaded and set up on your system
- Git is installed and configured
- You have an active GitHub account
- You are able to create and manage public repositories

## 2. Important Rules
- Maximum 3 attempts allowed.
- The repository size must be less than 10 MB.
- The GitHub repository must be public.
- The repository MUST contain only one branch.
- Failure to follow these rules may result in your submission not being evaluated.

## 3. Challenge Expectations
Your solution MUST demonstrate:
- Ability to build a smart, dynamic assistant.
- Logical decision making based on user context.
- Practical and real-world usability.
- Clean and maintainable code.
Participants must choose one of the provided challenge verticals and design their solution around that persona and logic.

## 4. How to Work on Your Project
- Create a new repository on GitHub.
- Ensure the repository is set to public.
- Open your AI platform.
- Clone your repository inside the AI platform.
- Build your solution through prompting and coding.
- Regularly commit and push your progress.
- Keep all work within a single branch.

## 5. Score Multiplier Guidelines
To reward efficiency, a time-dependent Score Multiplier will be applied to your submissions. The earlier you submit, the higher your final score.
- **Rules & Mechanics**:
  - Time-Dependent Decay: The multiplier starts at a maximum value when submissions open. It decreases at regular intervals over the submission duration window, dropping to a minimum value by the final tier.
  - Per-Attempt Application: You have a maximum of 3 submission attempts. The multiplier active at the exact timestamp of your submission applies to that specific attempt, overwriting the previous score.
- **Strategy Notes**: A lower base score submitted early can outrank a perfect base score submitted near the deadline due to the decay penalty.

## 6. What to Submit
Your submission must include:
- A public GitHub repository link
- Complete project code inside the repository
- A README explaining:
  - Your chosen vertical
  - Approach and logic
  - How the solution works
  - Any assumptions made

## 7. Evaluation Focus Areas
Submissions will be reviewed on:
- **Code Quality** – structure, readability, maintainability
- **Security** – safe and responsible implementation
- **Efficiency** – optimal use of resources
- **Testing** – validation of functionality
- **Accessibility** – inclusive and usable design

---
### Source: `00-strict-constraints.md`
---

# Hack2Skill PromptWars: Strict Agent Constraints

The following rules are NON-NEGOTIABLE and dictate the boundaries of this repository. If you violate these, the project will be disqualified.

## 1. Git & Version Control (The Single-Branch Rule)
* **CRITICAL:** You are strictly forbidden from creating, suggesting, or checking out new Git branches. 
* All commits must be made directly to the `main` branch. 
* Do not generate complex merge/rebase workflows. Keep it strictly linear.

## 2. Storage & Asset Management (< 10MB Limit)
* The entire repository MUST stay under 10 MB.
* **No Bloat:** Do not suggest installing heavy dependencies.
* **Data Handling:** Do not generate or save large mock CSV/JSON files in the tracked repository. All database files (`.duckdb`), raw telemetry, and large datasets MUST be explicitly added to `.gitignore`.

## 3. The README.md Contract (Submission Requirements)
When asked to generate or update the `README.md`, you MUST include these exact sections prominently at the top:
1. **Vertical/Persona:** State clearly that this is the "Sustainability / Enterprise ESG" vertical built for an "Enterprise Sustainability Officer".
2. **Approach & Logic:** Explain the Bronze -> Silver -> Gold DuckDB pipeline.
3. **Assumptions Made:** List any technical or business assumptions we made during the hackathon sprint.

## 4. Evaluation Criteria (Code Standards)
All generated code must pass these quality gates:
* **Efficiency:** Use vectorized operations (PyArrow/DuckDB) over standard Python loops.
* **Testing:** Ensure components are modular and testable.
* **Accessibility:** Any frontend UI (HTML/React) must include semantic tags, ARIA labels, and proper contrast for enterprise accessibility standards.
