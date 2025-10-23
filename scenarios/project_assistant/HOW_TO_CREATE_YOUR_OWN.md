# How Project Assistant Was Created

**From idea to working tool using Amplifier's patterns**

## The Starting Point

The user described what they wanted:

> "I want to build a simple tool that will help me complete a project (for example renovate a kitchen, or lose weight).
>
> Step 1: Ask the human a series of questions to deeply understand the goals of the project.
>
> Step 2: AI should go do research and deep thinking to come back with proposal and work with the user to align on the plan.
>
> Step 3: AI should work alongside the user to clear action items and next steps and check-ins to make sure the project is completed."

That's it. No code, no technical specifications, just a description of what the tool should do.

## The Creation Process

### 1. Understanding the Pattern

The first step was recognizing this fits the amplifier CLI tool pattern:

**Why an amplifier tool?**
- Multi-phase workflow requiring state management
- Hybrid of structured process (phases, state) and AI intelligence (questions, research, coaching)
- Reusable across many project types
- Benefits from session persistence and resumability

**Key decisions:**
- State persistence needed (projects take days/weeks)
- Three clear phases with transitions
- AI for intelligence, code for structure

### 2. Architecture Design

Based on amplifier patterns, the architecture emerged:

```
scenarios/project_assistant/
├── state.py                 # Data models and persistence
├── main.py                  # Orchestration
├── discovery/agent.py       # Phase 1: Questioning
├── planning/agent.py        # Phase 2: Research & proposals
├── execution/agent.py       # Phase 3: Action tracking
├── README.md                # User documentation
└── HOW_TO_CREATE_YOUR_OWN.md  # This file
```

**Philosophy:**
- Ruthlessly simple: Three phases, clear transitions
- Code handles: State management, phase transitions, file I/O
- AI handles: Questions, understanding, research, proposals, coaching

### 3. State Management First

Started with data models (state.py):

- `ProjectState` - Overall project state
- `DiscoveryData` - Questions and answers
- `PlanningData` - Research and proposals
- `ExecutionData` - Actions and check-ins

**Key pattern:** Load/save to JSON for simple persistence

### 4. Building Each Phase

**Discovery Phase** (discovery/agent.py):
- `ask_next_question()` - Generate next question based on answers
- `synthesize_understanding()` - Create comprehensive document

**Metacognitive recipe:**
- Build on previous answers
- Assess understanding score
- Stop when sufficiently understood (85%+)

**Planning Phase** (planning/agent.py):
- `conduct_research()` - Gather relevant insights
- `generate_proposal()` - Create detailed plan with options
- `refine_proposal()` - Incorporate user feedback

**Metacognitive recipe:**
- Research before proposing
- Present multiple approaches
- Iterate until approved

**Execution Phase** (execution/agent.py):
- `generate_action_items()` - Break plan into tasks
- `conduct_check_in()` - Assess progress and encourage
- `suggest_plan_adjustment()` - Adapt plan to reality

**Metacognitive recipe:**
- Track concrete actions
- Regular encouraging check-ins
- Adapt when needed

### 5. Orchestration

main.py ties it all together:

- Load or create project state
- Run appropriate phase based on current state
- Handle user input and commands
- Save progress continuously

**Key patterns:**
- Resumability: Check state, continue from current phase
- Progress visibility: Show understanding scores, completion status
- Graceful interruption: Save on Ctrl+C

### 6. Integration

Added to Makefile:

```makefile
project-assist: ## Start or resume project with AI coaching
	uv run python -m scenarios.project_assistant --project "$(PROJECT)"
```

Simple invocation: `make project-assist PROJECT="Kitchen Renovation"`

### 7. Documentation

Created two docs:
- README.md - User-facing: problem, solution, usage
- HOW_TO_CREATE_YOUR_OWN.md - Developer-facing: how it was built

## What Makes This Work

### 1. Clear Metacognitive Recipes

Each phase has a clear thinking process:

**Discovery:** "Ask questions until you understand deeply"
**Planning:** "Research, propose, iterate until approved"
**Execution:** "Track actions, check in, adapt"

These recipes guide the AI on HOW to think about the problem.

### 2. Hybrid Code/AI Balance

**Code provides reliability:**
- Phase transitions always work
- State is always saved
- Files are always written

**AI provides intelligence:**
- Questions adapt to answers
- Research is relevant
- Proposals are thoughtful
- Coaching is encouraging

### 3. Progressive Complexity

Start simple:
- Discovery: Just Q&A
- Planning: Add research and proposals
- Execution: Add action tracking

Each phase builds on the previous, but is independently functional.

### 4. Session Persistence

All progress is saved:
- Resume at any time
- Complete project history
- No progress lost

This matches how real projects work - over days/weeks, not one session.

## Key Learnings

### What Worked Well

**Clear phase separation:**
- Each phase has one job
- Transitions are explicit
- Easy to understand and maintain

**State persistence:**
- JSON for simplicity
- Save after every change
- Resume from any point

**User-centered design:**
- Adapts to user's pace
- No judgment, only support
- Realistic about challenges

**AI for intelligence, code for structure:**
- Code handles the process
- AI handles the thinking
- Clean separation of concerns

### What Could Be Improved

**Text-only interaction:**
- GUI would be more engaging
- Visual progress tracking
- Calendar integration

**Single user:**
- Team projects need collaboration
- Shared accountability
- Progress visibility for others

**Manual progress:**
- Could auto-track some actions
- Integration with task management
- Automated reminders

## How to Create Your Own Tool Like This

### 1. Start with the Problem

What specific problem are you solving?
- Be concrete: "X takes too long" or "Y is inconsistent"
- Focus on a real need, not "wouldn't it be cool if..."

### 2. Identify the Metacognitive Recipe

How should the AI think about this problem?
- What's the step-by-step thinking process?
- Where does AI intelligence add value?
- What needs code structure?

### 3. Design for Phases

Break complex workflows into clear phases:
- Each phase has one primary goal
- Phases build on each other
- Transitions are explicit

### 4. Code for Structure, AI for Intelligence

**Use code when you need:**
- Reliable iteration (loops, batches)
- State management
- File I/O
- Error recovery
- Progress tracking

**Use AI when you need:**
- Understanding and synthesis
- Adaptive decision-making
- Natural language generation
- Research and analysis
- Creative problem-solving

### 5. Make It Resumable

Long-running processes need:
- State persistence (JSON is simple)
- Save after every significant step
- Load state on start
- Handle interruption gracefully

### 6. Document Both Sides

**User documentation (README):**
- What problem does this solve?
- How do I use it?
- What does success look like?

**Developer documentation (HOW_TO):**
- How was this built?
- What patterns does it use?
- How can I create similar tools?

## Tools and Patterns Used

### Amplifier Patterns

- **ccsdk_toolkit**: Claude Code SDK integration
- **Defensive utilities**: Retry logic, JSON parsing
- **State management**: Load/save patterns
- **Progressive disclosure**: Show complexity gradually

### Python Patterns

- **Dataclasses**: Clean data modeling
- **Async/await**: AI calls without blocking
- **Click**: CLI argument handling
- **Path**: File operations

### AI Patterns

- **System prompts**: Define agent expertise
- **Context building**: Accumulate relevant information
- **Defensive parsing**: Handle LLM output variability
- **Iterative refinement**: Multi-pass improvement

## Next Steps

Want to create a similar tool? Consider:

**Personal productivity:**
- Habit tracking with AI coaching
- Goal setting and achievement
- Time management optimization
- Decision-making support

**Professional development:**
- Skill learning pathways
- Career planning and transitions
- Portfolio development
- Interview preparation

**Creative projects:**
- Book writing coach
- Art/music project guidance
- Content creation planning
- Creative skill development

**Health and wellness:**
- Fitness program design
- Nutrition planning
- Sleep optimization
- Stress management

The pattern is the same:
1. Understand deeply (Discovery)
2. Plan thoughtfully (Planning)
3. Execute consistently (Execution)

Just adapt the questions, research, and actions to your domain.

## Conclusion

Creating amplifier tools isn't about writing lots of code. It's about:

1. **Understanding the problem** - What specific need exists?
2. **Defining the thinking process** - How should AI approach it?
3. **Balancing code and AI** - What needs structure vs intelligence?
4. **Making it usable** - How do users interact with it?
5. **Documenting well** - How do others learn from it?

The Project Assistant demonstrates these principles. Study its structure, adapt its patterns, and create tools that solve YOUR specific problems.

**The best tool is the one you actually use.**
