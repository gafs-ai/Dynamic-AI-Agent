# Dynamic AI Agent

Dynamic AI Agent is still under development and is planning the release of the first stable version in 2026.
The following sections describe our key concepts, but many of the features are still under development.


## Key Concepts

1. Flexible: Suitable for Various Tasks
    - With all the fundamental functionality of AI agents built into the platform, *Dynamic AI Agent* is suitable for a wide range of tasks, including personal use, office work, engineering tasks, customer support, and more.

2. Dynamic: Self-Configurable at Runtime
    - *Dynamic AI Agent* can receive the workflow you design, and then automatically adjust the execution plan for your specific task. It can also observe the outcome of each step and adjust subsequent tasks to achieve the desired results.
        - NOTE: If you want the agent to strictly follow your pre-designed workflow, you can configure it to do so.

3. Cooperative: "Human in the Loop" — Cooperation of Humans and AI Agent
    - You can define when the AI Agent should ask you to review work products, or you can assign tasks to yourself within the workflow. This allows you to review intermediate or final deliverables, or handle sensitive tasks yourself, ensuring the quality of the collaborative work.

4. Trustworthy: Enterprise Confidentiality Control
    - You can define the confidentiality level of your inputs and knowledge base entries, as well as the trust level of each model deployment. This gives you full control over where your data can be sent.

5. Open: No AI Provider Lock-in
    - AI is advancing rapidly, and the best model for a given task can change frequently. As a result, you may need to switch to models from different providers. Dynamic AI Agent eliminates dependency on any specific AI provider and supports open setups, including local environments.

6. Easy to Use
    - Many AI agent platforms are designed for AI professionals, but Dynamic AI Agent is built for non-specialists — it includes a user interface and is designed for ease of use and setup. We acknowledge that some programming knowledge is still needed for initial setup, but we believe our product is much easier to use than most open-source alternatives.


## Key Features

1. Flexible Planner
    - Pre-defined Execution Plans (Workflows)
    - Flexible Planning Capability to adjust pre-defined plans to specific tasks
    - Reflection (Observation) capability to monitor and adjust plans during execution

2. Models and Deployments
    - Model Catalogues to manage models and deployments
    - Dynamic Model Selection at Runtime
    - Multi-Deployment Support
        - Cloud AI
        - Remote AI (AI on a server in your local network)
        - Local AI (AI on your device)
    - Trust Level Management
    - Supports Various Types of Models
        - Text Completion
        - Chat Completion
        - Speech-to-Text
        - Text-to-Speech
        - Image Generation
        - Text Embedding
        - and more

3. Knowledge Base
    - Knowledge Catalogue to manage available knowledge sources and embedding capabilities
    - Supports various types of search methods
        - Vector Search
        - Full Text Search
        - Graph Search
        - and more
    - Knowledge Version Management (Knowledge Lifecycle Management)
    - Confidentiality Management
    - Supports both unstructured and structured knowledge
        - Dispersed Knowledge (not structured as a document or a spreadsheet)
        - Document Style Knowledge
        - Spreadsheet Style Knowledge

4. Skills
    - Skill Catalogues to manage skills of the agent
        - Prompting
        - Tool Calling
        - MCP
        - Multi Agent
    - Skills Version Management
    - Secure Function Calling Environment

5. Security
    - Security Components can be attached as a form of Skills and can intercept input or output to ensure security.

6. Self-Improvement
    - With Skills and Planner functionalities, realizes progressive self-improvement capabilities.

7. History and Memory Management
    - With Skills, Planner, and Knowledge capabilities, realizes history & memory management and allows the agent to utilize stored memories.

8. User Interface & Easy Setup
    - You just need to bring your API keys (AI providers) and run the installer for a quick & easy setup.
    - Platform with UI: No need to use CLI or an IDE
    - Modern and elegant user interface — no need to read through documentation.

9. Other Features
    - Secret Manager to store encrypted credentials and manage them for external connections, including model calling and tool calling.
    - Share the same environment among multiple devices (requires a remote database)


## Who Are We?

**GAFS Inc.** is located in Aichi, Japan, with more than 10 years of engineering and consulting experience, mainly in the automotive industry.

**GAFS AI Team** has provided support for AI implementation, mainly in automotive engineering, since 2024.
