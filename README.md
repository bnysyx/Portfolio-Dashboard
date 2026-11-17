# 👁️ Argus


> **Argus** is not just a financial analysis tool, but a proof of concept for how modern AI tools can be used to accelerate developer growth, while simultaneously creating robust, high-tech value for the open-source community.

## 📖 About the Project

Although **Argus** is in an active development phase, the project is characterized by its high architectural maturity and the resolution of real-world problems in the field of **Financial Data Engineering**. It demonstrates enterprise-level best practices that are highly demanded in the industry but rarely implemented in typical open-source portfolio projects:

### 1. AI-Assisted Learning (The Human Capital Multiplier)

This repository documents the active learning phase of a developer deeply engaging with data architectures. What sets Argus apart: **Artificial Intelligence is used strictly as a technical mentor, not as a code generator.** Instead of blindly copying ready-made snippets, AI is utilized to understand the *why* behind the code, the underlying mechanics, and industry best practices. This makes the project an honest and transparent proof of genuine competence building in Software Engineering. When technology sharpens human understanding rather than replacing it, the capabilities of developer and machine don't just add up – they multiply.

### 2. Democratization of Financial Analysis

Professional software applications for portfolio management and in-depth financial analysis are often costly or tied to expensive subscriptions. Argus aims to break down this barrier.

It makes a significant contribution by providing all users with open, free, and transparent access to their own financial and portfolio analysis. Users retain full data sovereignty (running locally via **PostgreSQL**) and receive enterprise-level analytics without a paywall.

### 3. Solid Foundation for the Community

Despite the initial focus on personal learning, the codebase is structured from day one so that other developers can seamlessly benefit from and build upon it.

* **Scalability & Robustness:** Argus consistently relies on **Object-Oriented Programming (OOP)**. The system is designed so that future extensions or new data sources can be integrated effortlessly. The ELT pipeline proves maximum robustness through a stateless Orchestrator with clean parameter passing.
* **Analytical Excellence:** On the analytical side, Argus solves complex quantitative challenges, such as converting irregular, sparse event data (trade logs) into dense, continuous time series (daily portfolio matrices). The code demonstrates advanced, high-performance data manipulation: Instead of falling back on inefficient for-loops, these transformations are solved elegantly and resource-efficiently through **Vectorization** and **MultiIndex operations in Pandas**.

---

## 🛠️ Tech Stack & Architecture

* **Language:** Python
* **Data Manipulation:** Pandas (Vectorization, MultiIndex, Cross Joins), Streamlit
* **Database:** Local CSV / PostgreSQL (accessed via SQLAlchemy)
