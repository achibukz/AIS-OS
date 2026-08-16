# Agentic AI Cheat Sheet

```
Achi Note: Hi Guys, This is my cheat sheet/my actual workflow or sht that I researched on how I use Agentic AI or just claude code. BWAHHAHA

Literally just message me if you have questions and I will answer fast. Trust. BWHAHAHAHHA hihih enjoy
```

---

## 0. Start here (the boring foundation)

**`CLAUDE.md` — your global one at `~/.claude/CLAUDE.md`**
The single highest leverage file in your whole setup. It's the instructions your agent reads every session, in every project. Who you are, how you want responses, your coding standards, your tooling rules.

Two rules:
- Update it the moment the agent makes a mistake you don't want repeated. That mistake is a missing line in this file.
- Update it when something becomes necessary, not preemptively. Bloat costs tokens every single turn.


**Project-level `CLAUDE.md`**
Same idea but per repo. Architecture, conventions, where things live, what not to touch. Keeps the agent from re-deriving your codebase every session.

```
Achi Note: Literally make this your habit to have this in your project. This will make everything feel smooth every time. I swear. If there is a problem in ur project its probably because of ur Claude.md
```

**`uv`**
Python package manager. Stop using `pip install`. It's faster, handles envs properly, and doesn't wreck your system Python.
https://docs.astral.sh/uv/

**Warp — my terminal**
Asked about this a lot. I use it because I can organize tabs and panes so I can see everything at once. Running three agents plus logs plus a dev server without alt-tabbing.
https://warp.dev

```
Achi Note: Use this guys. Extra aura in larping.
```

**ccstatusline**
Status bar for Claude Code. Shows model, token usage, context left, cost. You stop guessing how much room you have.
https://github.com/sirmalloc/ccstatusline

**claude-notifications-go**
Desktop notification with sound when Claude Code finishes a turn. https://github.com/777genius/claude-notifications-go

```
Achi Note: this is my claude notifications so that when you leave it be while you alt tab. you can have a notification with sound that lets you know that your claude is done doing its sht
```

---

## 1. Skills (the real unlock)

Skills are reusable instruction packages your agent loads on demand. This is where you go from "chatbot" to "system".

**skill-creator (by Anthropic)**
The meta-skill. Use it to build your own skills instead of hand-writing them.

> **TAKE NOTE: don't use the optimization step.** Skills work fine as-is. The optimization loop burns a lot of tokens for marginal gain.

```
Achi Note: Actual best way to make your own skills. IDK if there are better skill-creators but from the skills that i made with this. i dont have a problem with it naman. Just make sure you say what input, output you want and make it detailed.
```

**superpowers**
Big collection of process skills: brainstorming, TDD, systematic debugging, writing plans, executing plans, code review. It forces the agent to pick an approach before it starts typing, which is most of the value.

```
Achi Note: Actually carrying me in everything. Learn how to use this as a whole or just the skills it provides. It will literally one shot MCOs and projects for you. Obviously reiterate and reiterate till you have a good product.
```

**karpathy skills**
Add these to your global `CLAUDE.md` so they're always available, not just in one project.

```
Achi Note: A simple copy paste in global claude will help you a lot.
```

**usage-limit-reducer**
Skill that diagnoses your session and tells you where tokens are going. If you're constantly hitting limits, this is the fix.
Video: https://www.youtube.com/watch?v=2f7ZkImNHFo

``` 
Achi Note: I havent really used this since I think i learned how to be more optimized na by myself to the point i just use opus for everything lol.
```

**message-writer**
Skill that writes in *your* voice. Emails, LinkedIn messages, DMs, replies. You feed it your past messages and examples as reference, and it stops sounding like an AI. Build one for yourself, the generic version isn't worth it.

```
Achi Note: My latest addition: this sht so fun and makes it easy to copy paste if you say the skill to automatically copy to clipboard so you can paste it instantly and the formatting is correct.
```

**grill-me**
Makes the agent interview you about your plan until every branch of the decision tree is resolved. Use it before you build anything. It catches the "oh I never thought about that" stuff while it's still cheap.

```
Achi Note: Actually one of the best things to know and do all the time. As much as possible even in normal prompts you can just ask "Ask me questions for clarifications or if you dont get something". This will help you super.
```

**to-prd**
Turns the conversation you just had into an actual PRD.
Both covered here: https://www.youtube.com/watch?v=-QFHIoCo-Ko&t=2220s

```
Achi Note: I havent used this too much since i just let ai do the prd. But lowkey try this out and tell me but in general lowkey dapat talaga binabasa ng super yung prd ah.
```

**`/insights`**
Makes the agent learn from your own conversations. Surfaces patterns in how you work.

---

## 2. Design and frontend

**impeccable**
Design and redesign skill. UX review, visual hierarchy, accessibility, typography, motion. Good for turning a bland UI into something intentional.

**frontend-design**
Builds actual production frontend code that doesn't look like default AI slop.

**open-design**
Free alternative to Claude Design.

**uiux-promax**
Another good ass design skill to use. Usually i use this more now. I use this with front-end design then use impeccable to judge.

```
Achi Note: With frontend, i havent researched that much but you can research more about:

1. Vibe Code templates - You can search prompts specifically to find what you want like how to do this kind of button and etc.
2. Design Templates/Design Examples - To research more on how design works.
```

---

## 3. Browser control

**Playwright CLI / MCP**
You can do basically anything with Chrome programmatically. Scraping, form filling, testing, screenshots, session auth. The scriptable option.

**Claude in Chrome**
Extension that lets the agent drive your actual browser session, with your logins already there. Different use case from Playwright: this is for "do this thing in my browser right now", Playwright is for "build a repeatable automation".

**gws CLI**
Google Workspace CLI. Gmail, Calendar, Drive from the terminal. Multi-account support. This is how you stop context-switching to a browser tab just to check when your next meeting is.

---

## 4. Memory and knowledge

**karpathy wiki**
Data gathering and collection, Claude plus Obsidian. Learn to adapt this to whichever wiki you're building: school notes, second brain, or personal. The structure changes depending on what the wiki is for. Don't copy someone else's schema wholesale.

```
Achi Note: Do proper indexing, logging, and make sure to follow and create good hallucination protocols for your claude.md
```


``` 
Achi Note: To make a good llm wiki made for you. You gotta personalize your claude.md and play and chat with opus on how to make it better.
```

**claude-mem**
Persistent cross-session memory. The agent remembers what you did last week instead of starting cold every time.

**agentic OS**
One hub that holds all your connections: email, calendar, files, notes, task tracking, project repos. The point is that the agent has one place to look instead of you re-explaining your life each session. Mine is called achiOS.

```
Achi Note: Im trying to create my actual achiOS that is connected to achiMem which is my whole second brain so will upd u on this. Lets see if it will make me more efficient with life.
```

---

## 5. Project workflow

**`prd.md`, `design.md`, `architecture.md`**
Learn how to use these if you're building anything real.

- `prd.md` — what you're building and why. Requirements, scope, success criteria.
- `design.md` — how it looks and behaves. UX flows, states, edge cases.
- `architecture.md` — how it's built. Components, data flow, key decisions and their tradeoffs.

Write them before you code. The agent reads them and stops guessing. This is the difference between an agent that builds what you wanted and one that builds something plausible.

```
Achi Note: Also claude.md, dont forget this + this is the foundation when creating a new project. and dont forget to gitignore the docs folder if you dont wanna let people see the ai md files esp superpowers BWHAHAHHAH
```

**career-ops**
Job maxxing. Application pipeline, CV and cover letter generation, follow-up cadence. Turns job hunting from a memory game into a tracked system.

```
Achi Note: HOLY SHIT. Actually carrying me in life right now. I havent really even utilized this that much. and i think i got like almost 80% interviews. but like lol hirap parin in this market lowkey.

rn i just do:
1. Create my resume specific for the role and company
2. Interview prep - Researches the company, how it does interviews, and creates specific scripts and questions.
```

```
Achi Note: For the create resume, make sure to use the latex to pdf version rather than md to pdf. It gives the harvard format vibe and make sure to say to limit it to only One page and say its a strict rule.

This my format as of now:
  1. Header — Name, then a two-line contact block: Location • Email • Phone, then LinkedIn • GitHub
  2. Education
  3. Experience
  4. Technical Projects
  5. Certifications
  6. Skills — 8 category lines (Languages & Core, Web & Mobile, Data & Storage, Cloud & DevOps, QA & Testing, AI & Data,
  Practices, Leadership, spoken languages)
```

---

## 6. People to follow

**Nate Herk**
The 3Ms of AI framework: Mindset (how to think), Method (how to decide), Machine (how to build). It's the mental model I use for deciding what to automate next.

> The Three Ms of AI™ is a trademark of Nate Herk.

---

## If you only do four things

```
Achi Note: If you want a simple answer on how to do agentic AI
1. Research on the sht that you have problems with then check the topics in ai that could help you with it
2. Learn how to use claude.md properly and use Claude Code not Chat pls. AI aint just a chatbot
3. Learn how to use Skills and how to create Skills. Actual MUST
4. Chat with your AI. Like ask them how do i reorganize this better? what suggestions can you give? You know they are literally an AI, meaning they know a lot more than you do. Use that to your advantage


Extra: Actually just try to love learning a lot everyday and always think that you will be behind so just keep learning new sht. I would say i still dk a lot of sht pa and i can still minmaxx more so give me sources and just send me new sht you learn. hehe ty
```
