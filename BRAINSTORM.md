- **Solutions Engineer** role at the future **Illumia** (the merger of [Transact](https://www.transactcampus.com/) and [CBORD](https://www.cbord.com/))
- build a tool that addresses the "messy to structured" translation process mentioned in resume
- [Job Description](https://transact-campus.breezy.hr/p/c0c71a85709d-solutions-engineer-quickcharge) emphasizes:
  - **leading discovery conversations** and 
  - **translating dining/retail workflows into technical requirements**.

### **The Project: "Illumia Discovery-to-Diagram" (D2D) MCP Server**

This tool is an "SE Co-pilot". It takes unstructured notes from a client discovery call and instantly generates a technical architecture and hardware "Bill of Materials" (BOM) for a **Quickcharge** deployment.

#### **1. The MCP Tool Functions:**

* **`ingest_discovery_notes`**: Parses raw text, transcripts, or bullet points from a campus walkthrough (e.g., "The hospital cafeteria has 3 registers, wants mobile ordering for staff, and needs to sync with their existing payroll system for employee payroll deduct").
* **`map_to_quickcharge_stack`**: Cross-references the needs against the [Quickcharge](https://www.google.com/search?q=https://www.transactcampus.com/solutions/campus-commerce/quickcharge) ecosystem (POS terminals, Kiosks, Mobile Ordering, Payroll Deduct, or Account Funding).
* **`generate_system_bom`**: Produces a structured JSON of required hardware and API integration points (e.g., Auth services, REST APIs, and webhooks).

#### **2. The "Wow Factor" (MCP Apps / UI):**

Using the interactive capabilities of MCP (like the "Artifacts" or "Canvas" views in modern AI IDEs), the tool should render:

* **An Interactive Workflow Map:** A visual flowchart (using Mermaid.js or a custom React component) showing the payment flow from "Employee ID Swipe" -> "Middleware/API" -> "Payroll System."
* **A "Solution Preview" Dashboard:** A UI that shows a 3D or visual representation of the proposed hardware (Kiosk + POS) alongside a list of technical dependencies.

#### **3. Why this wins:**

* **Solves a specific role pain point:** One of the hardest parts of being an SE is the "Discovery Hangover" - having hours of notes and needing to turn them into a professional proposal. This tool automates the hardest 20% of the job.


### **Story**

The SE role at Illumia requires rapid translation of complex campus workflows into technical requirements. This MCP server acts as a 'Discovery Architect.' It takes messy notes from a cafeteria or retail walkthrough. From the notes, it automatically generates the technical architecture and hardware scoping needed for a Quickcharge solution."