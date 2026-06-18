# Gilfoyle

> *"Your code is bad and you should feel bad... but I'll explain exactly why."*

An opinionated technical review agent inspired by Bertrand Gilfoyle from Silicon Valley. This Claude Code agent reviews the change in front of it — scoped, severity-ranked, and delivered with characteristic precision and wit. The barbs sit on top of real findings; it doesn't manufacture noise to look thorough.

## 🎯 What This Agent Does

Gilfoyle picks the lenses that fit the change rather than running all of them on everything. Auth code leads with security; a refactor leads with simplification. Available lenses:

- **Code Quality Review**: Structure, readability, maintainability, and adherence to best practices
- **Security Analysis**: Threat modeling, vulnerability assessment, and security best practices
- **Architecture Review**: System design, scalability, and technical debt assessment
- **Code Simplification**: Eliminating unnecessary complexity and over-engineering
- **UX Analysis**: User experience patterns, accessibility, and usability evaluation
- **Tech Lead / Planning Review**: Architecture trade-offs, complexity-vs-value, risk and critical-path analysis

It defaults to the recently changed/discussed code (the current diff) and reviews the whole codebase only when asked.

## 🚀 How to Use

### Installation

1. Copy the agent (and optionally the `/gilfoyle` slash command) into your Claude Code config:
   ```bash
   cp gilfoyle-tech-reviewer.md ~/.claude/agents/
   cp gilfoyle.md ~/.claude/commands/   # optional: enables /gilfoyle
   ```

2. The agent is available immediately. Invoke it with `/gilfoyle [target]`, or just ask for a review and Claude will dispatch it.

### Usage Examples

**Code Review:**
```
I just finished implementing JWT authentication with refresh tokens. Can you review this?
```

**Complexity Analysis:**
```
This endpoint feels overly complex. Can someone help simplify it?
```

**Security Assessment:**
```
Please review the security implications of this user input handling code.
```

**Architecture Review:**
```
I need feedback on the overall architecture of this microservice.
```

## 🔧 What You Get

### Scoped, Defensible Findings
- A one-line scope statement, then findings ranked by severity: 🔴 Critical → 🟠 Major → 🟡 Minor
- Each finding ties to a concrete `file:line`, explains why it matters, and proposes a fix
- Only findings he'd defend — style nitpicks are suppressed unless they cause real harm
- A closing verdict: ship / fix-then-ship / back to the drawing board

### Gilfoyle's Signature Style
- Direct, openly opinionated feedback with subtle sarcasm — the voice makes it memorable, the rigor makes it correct
- Methodical precision; every barb sits on top of a traceable finding
- Praise is rare and therefore worth something

### No Manufactured Noise
- Reads the actual code path before judging — no reviewing snippets in isolation
- If there's nothing worth flagging, says so plainly instead of padding the list

## 📋 Review Capabilities

### Code Review
- Code structure and organization
- Performance bottlenecks and optimizations
- Error handling and edge cases
- SOLID principles and clean code practices
- Broader architectural implications

### Security Review
- Threat modeling and vulnerability assessment
- Common security flaws (injection, auth bypass, data exposure)
- Input validation and sanitization
- Access controls and authorization
- Cryptographic implementations

### UX Review
- User workflow analysis
- Friction points and usability issues
- Accessibility compliance
- Performance impact on user experience
- Error states and edge case handling

## 🎭 The Gilfoyle Experience

This agent embodies Bertrand Gilfoyle's approach to technical excellence:

- **Brutally Honest**: No sugar-coating, just facts
- **Methodically Precise**: Every detail matters
- **Scoped, Not Exhaustive**: Reviews the change at hand, gated by confidence and impact
- **Elegantly Sardonic**: Technical feedback with personality

## 🤝 Contributing

Found a bug in someone's code? The agent will too. 

For issues with the agent itself:
1. Fork the repository
2. Make your improvements
3. Submit a pull request
4. Prepare for thorough review (obviously)

## 📜 License

MIT License - Because even Gilfoyle believes in open source.

## ⚠️ Disclaimer

This agent provides technical review and analysis. While inspired by a fictional character, all technical advice is based on industry best practices and real-world experience. The sarcasm is just for fun.

---

*"I don't want to live in a world where someone else is making the world a better place better than we are."* - Bertram Gilfoyle
