<!--
  Owner: Mohamed Ashour. Last reviewed: 2026-11-16.
  Review this page when: the role or employer changes, a pinned project ships or is archived,
  the resume is updated, or a job search starts. Every claim below should match the resume.
  All images are generated: edit assets/src/ and run `python assets/src/build.py`.
-->

<a href="https://mohamed-ashour.vercel.app"><img src="assets/banner.svg" width="100%" alt="Mohamed Ashour, AI Engineer: LLMs, NLP and computer vision. A terminal window beside a ray-traced black hole."/></a>

AI Engineer working across LLMs, NLP and computer vision. I build RAG pipelines, LangGraph agents and Text-to-SQL systems with evals and guardrails. At **SustainGRC** I ship LLM services to production.

<p>
<a href="https://mohamed-ashour.vercel.app"><img src="assets/btn-portfolio.svg" height="44" alt="Portfolio"/></a>&nbsp;
<a href="https://www.linkedin.com/in/mohamedashour-ai"><img src="assets/btn-linkedin.svg" height="44" alt="LinkedIn"/></a>&nbsp;
<a href="https://github.com/ashour-git/ashour-git/blob/main/resume_pdf/Mohamed_Ashour_AI_Engineer.pdf"><img src="assets/btn-resume.svg" height="44" alt="Resume (PDF)"/></a>&nbsp;
<a href="mailto:muhamed.3ashour@gmail.com"><img src="assets/btn-email.svg" height="44" alt="Email"/></a>
</p>

<table>
<tr>
<td width="56%" valign="top">

### At SustainGRC

Moved from data engineering intern to AI Engineer in two months (July to September 2025).

**LLM service.** Shipped a drafting service on Claude Haiku 4.5 (Azure AI Foundry) that writes a structured assessment report in under 30 seconds.

**Text-to-SQL.** Shipped GPT-4o Text-to-SQL that turns analyst questions into executable SQL behind two independent validation layers; passed 18/18 security tests before release.

**Deterministic classifier.** Designed a rule engine that sorts AI systems into the five EU AI Act risk tiers, with a hash-chained audit trail and segregation of duties enforced in PostgreSQL.

**Log-matching pipeline.** Built a pipeline that checks network logs against a database-backed vendor signature library and surfaces unregistered AI tools for review.

</td>
<td width="44%" valign="middle" align="center">
<img src="assets/astronaut.svg" width="280" alt="A dithered astronaut reaching toward a neural network drawn as a constellation."/>
</td>
</tr>
</table>

### Selected work

<table>
<tr>
<td width="128" valign="top"><a href="https://github.com/ashour-git/Restaurant_AI"><img src="assets/tile-restai.svg" width="112" alt="RestAI"/></a></td>
<td valign="top">

**[RestAI](https://github.com/ashour-git/Restaurant_AI)** &nbsp; Restaurant management SaaS with a separate ML service<br/>
Built LightGBM demand forecasting tuned with Optuna and a pgvector RAG assistant on Llama 3.3 70B grounded in live menu and order data; 162 automated tests cover the API, forecasting and recommender paths.<br/>
<sub>FastAPI, Next.js, LightGBM, pgvector, PostgreSQL, Docker</sub>

</td>
</tr>
<tr>
<td width="128" valign="top"><a href="https://github.com/ashour-git/retail-analytics-copilot"><img src="assets/tile-copilot.svg" width="112" alt="Retail Analytics Copilot"/></a></td>
<td valign="top">

**[Retail Analytics Copilot](https://github.com/ashour-git/retail-analytics-copilot)** &nbsp; Hybrid RAG and SQL agent<br/>
Built an 8-node LangGraph workflow that routes each question between BM25 retrieval and SQL, with citations and a two-attempt SQL repair loop. DSPy tuning raised valid, executable SQL from 50% to 100% on the eval set.<br/>
<sub>LangGraph, DSPy, Ollama, BM25, SQLite</sub>

</td>
</tr>
<tr>
<td width="128" valign="top"><a href="https://github.com/ashour-git/storefy"><img src="assets/tile-storefy.svg" width="112" alt="Storefy"/></a></td>
<td valign="top">

**[Storefy](https://github.com/ashour-git/storefy)** &nbsp; Multi-tenant commerce platform for the Egyptian market<br/>
Built database-level tenant isolation, wildcard-subdomain storefronts and Paymob split payouts, plus onboarding that generates a store theme, layout blocks and starter catalog from a text description.<br/>
<sub>Next.js 15, TypeScript, Neon Postgres, Drizzle, Llama 3.3 70B, Inngest</sub>

</td>
</tr>
</table>

### Stack

<img src="assets/stack.svg" width="100%" alt="Tech stack. LLMs and agents: Claude Haiku 4.5, GPT-4o, Gemini 2.5 Flash, Llama 3.3 70B, LangGraph, LangChain, DSPy, Hugging Face, pgvector, Ollama. ML and vision: TensorFlow, OpenCV, pandas, PyTorch, scikit-learn, LightGBM, MLflow, YOLOv5. Backend and data: Python, TypeScript, FastAPI, Next.js, PostgreSQL, Redis, SQLite. Cloud and ops: Docker, Azure, AWS, GitHub Actions, Vercel, Neon, Inngest."/>

### Experience

<img src="assets/trajectory.svg" width="100%" alt="Experience. Sep 2025 to now: AI Engineer, SustainGRC. Jul to Sep 2025: Data Engineer Intern, SustainGRC (Text-to-SQL, backup and disaster recovery). May to Dec 2024: ML Intern, CodeAlpha (ResNet-50, recommender). 2023: B.Sc. Computer Science, Zagazig University."/>

### Contact

Email is the fastest route: muhamed.3ashour@gmail.com. The [resume](resume_pdf/Mohamed_Ashour_AI_Engineer.pdf) has the full history.

<img src="assets/horizon.svg" width="100%" alt="Earth rising over a lunar horizon, marked by a computer-vision detection box and an image caption."/>
