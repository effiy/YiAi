[InfoQ Homepage](/ "InfoQ Homepage") [News](/news "News") Ramp Builds Internal Coding Agent That Powers 30% of Engineering Pull Requests

[Development](/development/ "Development")

[QCon London (March 16-19, 2026): Learn proven architectural practices to scale your systems faster.](https://qconlondon.com/?utm_source=infoq&utm_medium=referral&utm_campaign=infoqyellowbox_qlondon26 )

Log in to listen to this article

Loading audio

 Your browser does not support the audio element.

0:00

0:00

Ramp has [shared](https://builders.ramp.com/post/why-we-built-our-background-agent) the architecture of Inspect. This internal coding agent has quickly reached about 30% adoption for merged pull requests in the company’s frontend and backend repositories. The fintech company shared a detailed technical specification. It explains how they created a system that gives AI agents the same access to the development environment as human engineers.

Giving coding agents full access to all of Ramp's engineering tools is what makes Inspect truly innovative. Instead of only letting agents write basic code, Ramp's system runs in sandboxed virtual machines on Modal. It works seamlessly with databases, CI/CD pipelines, monitoring tools like Sentry and Datadog, feature flags, and communication platforms such as Slack and GitHub. Agents can write code and ensure it works by using the same testing and validation processes that engineers use every day.

Ramp's engineering team says this verification loop marks a major change from old code generation tools. The agent can run tests, check monitoring dashboards, query databases for validation, and join code reviews. This helps close what they call the verification gap that affects many AI coding assistants.

Ramp's decision to build on Modal's infrastructure proves central to Inspect's performance characteristics. The platform starts sessions almost instantly and supports unlimited concurrent sessions. This lets multiple engineers work with separate agent instances at the same time without competing for resources. Modal’s sandboxing features and file system snapshots keep code execution safe. This also allows for quick iteration cycles.

The architecture uses Cloudflare Durable Objects for state management. This keeps the conversation context and development session state steady across interactions. This stateful design helps agents keep track of their work. It’s like how human engineers remember the codebase while they develop.

Ramp implemented several client interfaces to make Inspect accessible across different workflows. Engineers can interact with the agent using many tools: a Slack bot for quick chats, a web interface for detailed tasks, and a Chrome extension made for editing visual React components. This multi-modal approach recognizes that different tasks benefit from different interaction patterns.

The system lets team members work together. They can watch and guide the agent's actions at the same time. This feature tackles a common worry about autonomous coding tools. It keeps human oversight in place, so we still benefit from the efficiency of automation.

Ramp makes an explicit case for building rather than purchasing off-the-shelf coding agent solutions. The engineering team believes that owning the tooling allows for much stronger integration than commercial products. This is mainly because internal tools can connect deeply with proprietary systems, databases, and workflows that external vendors can't reach.

The company acknowledges this approach requires substantial engineering investment. To inspire others, Ramp shared detailed implementation specs. These include execution environments, agent integration patterns, state management, and client implementation details. This transparency shows confidence that a competitive edge comes from execution, not from hiding architectural details.

Perhaps most striking about Inspect's deployment is that Ramp did not mandate its use. The jump to 30% of merged pull requests happened as engineers chose to adopt the agent. They found tasks that matched manual coding in quality, speed, or convenience. The continued growth trajectory indicates expanding comfort with the system's capabilities and limitations.

The team also points out that Inspect makes code contribution easier. It gives non-engineers access to the same tools that professional developers use. This shows that the agent might let product managers, designers, and others add code directly. This could change how cross-functional teams work together.

Ramp's engineering team knows that session speed and quality are still mainly held back by the model's intelligence. Even with the best tools and setup, coding agents are limited by today’s language models. These models still make mistakes, hallucinate, struggle with complex reasoning, and need human oversight.

The company knows that their build-versus-buy recommendation might not apply to every organization. To implement a similar system, you require strong AI infrastructure skills and engineering resources. Smaller teams or different organizations might not have these or find them justifiable.

As coding agents evolve, Ramp's technical specs and adoption metrics offer clear data points. This helps organizations assess their automation strategies. Inspect shows that with the right context, tools, and verification, AI coding agents can greatly boost engineering productivity on a large scale.

## About the Author

[![](https://cdn.infoq.com/statics_s2_20260113082446/images/profiles/etZJL5qwf5xbcRUA3NKv4QZMRINLUnDB.jpeg)](/profile/Claudio-Masolo/)

#### **Claudio Masolo**

Claudio is a Senior DevOps Engineer at Nearform. In his spare time, he likes running, reading, and playing old video games.

Show moreShow less

-   -   ##### [Tracking and Controlling Data Flows at Scale in GenAI: Meta’s Privacy-Aware Infrastructure](/news/2026/01/meta-pai-genai-data-flows/)
        
    -   ##### [TanStack Releases Framework Agnostic AI Toolkit](/news/2026/01/tanstack-ai-sdk/)
        
    -   ##### [How Developers in Southeast Asia and India are Really Using AI in 2025](/news/2025/12/ai-developers-apac/)
        
    -   ##### [Agentic AI Expands into SecOps to Ease Human Workloads](/news/2025/09/secops-ai/)
        
    -   ##### [DoorDash Applies AI to Safety Across Chat and Calls, Cutting Incidents by 50%](/news/2026/01/doordash-safechat-ai-safety/)
        
    
-   -   ##### [Scalable Enterprise Java for the Cloud - Download the eBook](/url/f/ad5bf784-85e1-4593-b2eb-7ead05f29ab8/?ha=Y2xpY2s=&ha=a2V5ZG93bg==)
        
    -   ##### [Why APIs Can’t Trust Clients—and How to Bridge the Gap](/vendorcontent/show.action?vcr=e5a614eb-9916-4d68-af80-816adb90b385&primaryTopicId=2497&vcrPlace=BOTTOM&pageType=NEWS_PAGE&vcrReferrer=https%3A%2F%2Fwww.infoq.com%2Fnews%2F2026%2F01%2Framp-coding-agent-platform%2F&ha=Y2xpY2s=&ha=a2V5ZG93bg==)
        
    -   ##### [Observability-First Development: Staying in Flow While Shipping AI-Assisted Software (Live Webinar Feb 10, 2026) - Save Your Seat](/vendorcontent/show.action?vcr=2547476a-a531-43df-bf70-3c8795b9c5c1&primaryTopicId=2497&vcrPlace=BOTTOM&pageType=NEWS_PAGE&vcrReferrer=https%3A%2F%2Fwww.infoq.com%2Fnews%2F2026%2F01%2Framp-coding-agent-platform%2F&ha=Y2xpY2s=&ha=a2V5ZG93bg==)
        
    -   ##### [Orchestrating Production-Ready AI Workflows with Apache Airflow (Live Webinar March 5, 2026) - Save Your Seat](/vendorcontent/show.action?vcr=bde3e4c5-e91d-4ea1-b501-b2a2c901376d&primaryTopicId=2497&vcrPlace=BOTTOM&pageType=NEWS_PAGE&vcrReferrer=https%3A%2F%2Fwww.infoq.com%2Fnews%2F2026%2F01%2Framp-coding-agent-platform%2F&ha=Y2xpY2s=&ha=a2V5ZG93bg==)
        
    -   ##### [Cutting Java Costs in 2026 Without Slowing Delivery](/vendorcontent/show.action?vcr=87743dd9-e2a2-4ef6-b20e-d99f70eadc42&primaryTopicId=2497&vcrPlace=BOTTOM&pageType=NEWS_PAGE&vcrReferrer=https%3A%2F%2Fwww.infoq.com%2Fnews%2F2026%2F01%2Framp-coding-agent-platform%2F&ha=Y2xpY2s=&ha=a2V5ZG93bg==)
        
-   [![Related sponsor icon](https://imgopt.infoq.com//fit-in/218x500/filters:quality(100)/filters:no_upscale()/sponsorship/topic/5aab5793-1aa2-43a6-9086-318627c6365a/PayaraLogo-1763716038782.png)](/url/f/a30a7dce-63d3-462b-9160-dbe2672b779e/?ha=Y2xpY2s=&ha=a2V5ZG93bg==)
    
    Move from complexity to control. Run and scale your Jakarta EE, Spring, and Quarkus applications on a unified platform that replaces infrastructure chaos with deployment simplicity and total autonomy. [**Learn More**](/url/f/522e1507-e184-49f1-b584-c0c023dcf6f9/?ha=Y2xpY2s=&ha=a2V5ZG93bg==).