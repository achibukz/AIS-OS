# AIS-OS Intake

This is the source-of-truth file for your AIOS. Fill it in by typing, voice-pasting (Wispr Flow / OS dictation), or running `/onboard` for a guided conversation. Whichever mode, this file is what `/onboard` reads to scaffold your Day-1 setup.

**Hard cap: 7 questions.** Each answerable in under 60 seconds. Don't overthink — you can edit and re-run `/onboard` any time.

---

## Q1 — Who are you, what do you sell, who do you sell it to?

Identity, offer, ICP. One paragraph each is fine.

```
I'm Abram Aki R. Bukuhan — call me Aki. Third year BS CS (Software Technology) at DLSU-Manila. CGPA 3.029, expected graduation August 2027. I don't sell anything right now — I'm a student looking for internships and finishing my thesis (ML for short-form video engagement prediction).

What I'm "offering" the world right now: my time and skills to companies hiring CS interns. Strong QA background (Lead QA on GABAY, QA Engineer on UnboundMNL), full-stack work (AppToSync — Flask/SQLite/Gmail OAuth/Gemini+Groq), backend + distributed DB experience, and genuine AI/prompt-engineering fluency. I want healthcare-adjacent companies (J&J etc.) — using CS to actually help people, not just ship features.

My "ICP" = recruiters and engineering managers at internship programs that value QA depth, AI hands-on experience, and someone who understands the whole dev cycle from backlog to deployment.

This AIOS is meant to be the centralized control point across my repos:
- achiMem — Karpathy-style wiki for non-school general knowledge (underused so far)
- schoolMem — Karpathy-style wiki for school notes & coursework
- career-ops — main repo for internship application pipeline
- job-hub — old applications repo (still useful for personality.md voice baseline)
- sfv-thesis — thesis repo (ML engagement prediction)

Secondary goal: this repo should also hold project templates so when I say "spin up a new project with X stack," you pull from the templates here instead of starting from scratch.
```

---

## Q2 — Paste 1-2 things you've written recently. Don't edit them.

An email, a LinkedIn post, a DM, a doc — anything that sounds like you when you're not trying. **Paste verbatim.** Do not type these mid-conversation with Claude — chat-shaped samples are worse than no samples (voice contamination).

**Sample 1 — Conversational/interview register (from `job-hub/applications/Johnson&Johnson-Business Operations Intern/answers.md`, "Who are you?" + "Why are you interested in this company?")**

```
I am Aki Bukuhan. I am a third year Computer Science student at La Salle majoring in Software Technology. Right now I am focused on my thesis where I am using machine learning to predict engagement for short-form videos. It is a lot of data processing and model training, which has taught me how to find real insights from large datasets. I also have experience as a QA Lead in a Scrum team. That role taught me to look at the entire development cycle and make sure everything is running efficiently before it goes live. I am someone who genuinely enjoys figuring out how systems work and finding ways to make them better, which is exactly why I wanted to apply for this business operations role at J&J.

Since I started CS, I have always wanted to use it in a way that actually helps people. Not just build apps, but contribute to something that matters in someone's life. Healthcare kept coming back as the answer. J&J specifically felt right because of the scale and the mission. This is not a tech company that happens to touch healthcare. This is a company where everything they do ties back to patient outcomes and human wellbeing. Reading the Credo made that even clearer. The idea that the first responsibility is to the people who use their products, not to shareholders, is not something you see everywhere. That kind of values-first thinking is the environment I want to learn in. I also liked that this internship is on the operations side, because it means I will see how a company this large actually makes things work. That combination of meaningful mission and hands-on operational learning is exactly what I was looking for.
```

**Sample 2 — Formal academic register (thesis abstract, from `sfv-thesis/thesis/6/1/26/abstract-english.tex`)**

```
Short-form video (SFV) platforms like TikTok, YouTube Shorts, and Instagram Reels have transformed digital content creation. However, content creators face uncertainty in predicting audience engagement before publishing. Significantly, early engagement often determines visibility, yet newly uploaded videos can lack interaction data, making pre-publication decisions challenging. Prior research has focused on platform-centered models using multimodal video features—visual, audio, and textual—while largely neglecting creator-related and contextual factors. As a result, no existing model directly enables individual creators to estimate their own video's engagement potential before uploading. This study develops a creator-oriented engagement prediction model that integrates multimodal content signals with creator characteristics, such as follower count and posting history, and contextual factors, including posting time and audience activity patterns. The model aims to estimate potential engagement before posting, enabling data-informed creative decisions. To achieve this, the study constructs a dataset through voluntary data donation from TikTok creators, combining raw video files with official creator analytics. An ensemble of Large Multimodal Models—VideoLLaMA2, Qwen2.5-VL, and InternVideo2—is trained to jointly predict engagement by fusing multimodal content embeddings with structured creator and contextual metadata. By bridging content, creator, and context, this research contributes to human-centered predictive analytics, supports strategic resource allocation in the creator economy, and may foster a more diverse and sustainable digital content ecosystem.
```

---

## Q3 — What are your 2-3 biggest priorities for the next 90 days?

Quarterly priorities. Not yearly aspirations. Things that, if not done by July, would make you say "I wasted Q2."

```
1. Land an internship by August 2026 (start date target — likely tied to J&J/healthcare-adjacent CS internship cycle)
2. Finish thesis (ML engagement prediction for short-form video — sfv-thesis)
3. Build a reusable set of project templates I can pull from for personal projects and client work (lives in AIS-OS)
```

---

## Q4 — Where does revenue actually land, and where is it tracked?

Multiple answers OK. Stripe? Skool? GoHighLevel? QuickBooks? A spreadsheet?

```
No business revenue yet — student. Income source is allowance. Money is tracked in a money manager app on phone (specific app TBD — fill in when wiring connection on Day 2). Future client work from Priority #3 (templates for clients) will need a real revenue tracker; revisit then.
```

---

## Q5 — Where do you talk to customers, your team, and the outside world day-to-day?

Email (which one — Gmail / Outlook)? Slack? Teams? DMs (Skool / Discord / iMessage)? Phone?

```
Primary email (personal / career / recruiters): akibukzwork@gmail.com (Gmail)
Secondary email (school): abram_bukuhan@dlsu.edu.ph (Gmail / Google Workspace)
DMs (thesis): Discord
DMs (school groups, friends, family): Facebook Messenger group chats
Calendar (inferred from Gmail): Google Calendar
```

---

## Q6 — Where do meeting recordings, notes, and important docs live?

Granola? Otter? Fireflies? Google Drive? Notion? Dropbox? A folder on your desktop you keep meaning to organize?

```
Two Obsidian vaults (Karpathy-style wikis):
- schoolMem (~/Documents/Obsidian/schoolMem) — primary; school is most of life right now. Structure: raw/ holds unprocessed source files (Zoom transcripts, lecture material), wiki/ holds ingested/processed notes, plus notes/ and output/ folders.
- achiMem (~/Documents/Obsidian/achiMem) — general/non-school wiki. Same wiki/raw pattern. Underused so far.

CV + application docs: handled by career-ops repo (per-role/per-company CV generation via LaTeX templates + scripts like build-cv-latex.mjs, generate-cover-letter.mjs).

Project specs + templates + planning for future projects: handled HERE in AIS-OS — Aki refers to this repo personally as "achiOS". This is the centralized planning hub.

Meeting recordings: thesis meetings are F2F (Tuesdays w/ Dr. Andrew); class recordings flow into schoolMem/raw.
```

---

## Q7 — What's the one task that eats your week, and where do you currently track work?

The single biggest time-suck or recurring drudgery. Plus where tasks/projects live (ClickUp / Asana / Linear / Notion / a notebook).

```
Top pain (mild — already partially solved): tracking internship applications. career-ops handles most of this — just needs to be called. No urgent automation candidate right now.

Task tracker: no centralized one. School work tracked directly in Canvas (DLSU LMS). Considering moving general tasks into achiMem as a single source of truth. Open question for /level-up Day 14: should achiOS host the master task list instead of achiMem? (achiOS is the planning hub; tasks may belong here.)
```

---

When this file is filled, run `/onboard` (or re-run it) and the wizard will scaffold your Day-1 file set: `context/`, `references/voice.md`, populated `connections.md`, and a filled `CLAUDE.md`.
