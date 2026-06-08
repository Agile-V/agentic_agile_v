# Contributions & Attribution

This document provides a comprehensive list of all academic papers, open-source repositories, documentation, standards, and other resources that have contributed to the **Agentic Agile-V** project.

---

## 📚 Academic Research

### ArXiv Papers

1. **pcbGPT: Automatic PCB Schematic Synthesis from Natural Language Requirements**
   - **Authors**: Research paper on PCB synthesis using LLMs
   - **URL**: https://arxiv.org/pdf/2606.01188
   - **Contribution**: Core inspiration for the Circuit IR approach and PCB development integration
   - **Referenced in**:
     - `src/agilev/pcb/circuit_ir.py:11`
     - `PCB_IMPLEMENTATION_SUMMARY.md:17`
     - `docs/pcb-development.md:365`

---

## 🐙 GitHub Repositories

### Core Agile-V Ecosystem

1. **Agile-V/agentic_agile_v** (This Repository)
   - **URL**: https://github.com/Agile-V/agentic_agile_v
   - **License**: Proprietary / Agile-V™
   - **Purpose**: Main implementation repository for Agentic Agile-V framework

2. **Agile-V/agile_v_skills**
   - **URL**: https://github.com/Agile-V/agile_v_skills
   - **License**: CC-BY-SA-4.0
   - **Purpose**: Skills library for AI agents
   - **Version**: 3.3.2
   - **Integration**: Provides domain skills, behavioral guidelines, and orchestration patterns

### Configuration & Plugin Repositories

3. **Agile-V/agile_v_cursor_plugin**
   - **URL**: https://github.com/Agile-V/agile_v_cursor_plugin
   - **Purpose**: Cursor editor integration
   - **Referenced in**: `.github/workflows/sync-to-plugin-repo.yml`

4. **Agile-V/agile_v_cursor_config**
   - **Purpose**: Cursor IDE setup and configuration
   - **Referenced in**: `AGENTS.md`

5. **Agile-V/agile_v_continue_config**
   - **Purpose**: VS Code + Continue setup
   - **Referenced in**: `AGENTS.md`

6. **Agile-V/agile_v_windsurf_config**
   - **Purpose**: Windsurf IDE configuration
   - **Referenced in**: `AGENTS.md`

7. **Agile-V/agile_v_cline_config**
   - **Purpose**: Cline agent configuration
   - **Referenced in**: `AGENTS.md`

### Major Framework Integrations

8. **All-Hands-AI/OpenHands**
   - **URL**: https://github.com/All-Hands-AI/OpenHands
   - **License**: MIT License
   - **Purpose**: Autonomous code generation execution backend
   - **Integration Status**: MVP Complete (Phases 0-4 of 12-phase roadmap)
   - **Version**: Compatible with v0.9+
   - **Contribution**: Provides sandbox execution, autonomous coding, and verification capabilities
   - **Referenced in**:
     - `README.md:68`
     - `OPENHANDS_USER_GUIDE.md:117,416`
     - `WHATS_NEXT.md:27`
     - 1,085+ matches across codebase

9. **Lum1104/Understand-Anything**
   - **URL**: https://github.com/Lum1104/Understand-Anything
   - **License**: MIT License
   - **Purpose**: Codebase comprehension via knowledge graph generation
   - **Contribution**: Adds system context understanding, impact analysis, graph-based traceability, and regression-test selection
   - **Referenced in**:
     - `README.md:116`
     - `integrations/understand-anything/README.md:5`
     - 185+ matches across integration code and docs

### Upstream Pattern Sources

10. **gsd-build/get-shit-done** (GSD)
    - **URL**: https://github.com/gsd-build/get-shit-done
    - **Author**: Lex Christopherson
    - **License**: MIT License
    - **Copyright**: © 2025 Lex Christopherson
    - **Version**: v1.2 patterns
    - **Contribution**: Source of context engineering, orchestration pipeline, and state persistence patterns
    - **Adapted Patterns**:
      - Context Engineering
      - Orchestration Pipeline
      - State Persistence
      - Post-Verification Feedback
    - **Referenced in**:
      - Multiple skill files in agile_v_skills integration
      - Pipeline and orchestration architecture

11. **forrestchang/andrej-karpathy-skills**
    - **URL**: https://github.com/forrestchang/andrej-karpathy-skills
    - **License**: MIT License
    - **Version**: v1.3 principles
    - **Contribution**: Behavioral principles for AI agent interactions, accessibility, and distribution best practices
    - **Referenced in**:
      - Behavioral skill integration
      - Agent interaction patterns

12. **Kadajett/agent-nestjs-skills**
    - **URL**: https://github.com/Kadajett/agent-nestjs-skills
    - **Author**: Kadajett
    - **License**: MIT License
    - **Version**: 1.1.0
    - **Contribution**: NestJS-specific build patterns and best practices
    - **Referenced in**:
      - NestJS integration planning documents
      - Domain-specific build agents

### Evaluated Frameworks (Future Consideration)

13. **langchain-ai/langgraph**
    - **URL**: https://github.com/langchain-ai/langgraph
    - **Documentation**: https://docs.langchain.com/oss/python/langgraph/overview
    - **Status**: Evaluated for potential integration
    - **Referenced in**: `agile_v_skills_repo_improvement_plan.md:813`

14. **openai/openai-agents-python**
    - **URL**: https://github.com/openai/openai-agents-python
    - **Documentation**: https://openai.github.io/openai-agents-python/
    - **Status**: Evaluated for potential integration
    - **Referenced in**: `agile_v_skills_repo_improvement_plan.md:814`

15. **microsoft/autogen**
    - **URL**: https://github.com/microsoft/autogen
    - **Documentation**: https://microsoft.github.io/autogen/stable/index.html
    - **Status**: Evaluated for potential integration
    - **Referenced in**: `agile_v_skills_repo_improvement_plan.md:815`

16. **crewAIInc/crewAI**
    - **URL**: https://github.com/crewAIInc/crewAI
    - **Documentation**: https://docs.crewai.com/en/introduction
    - **Status**: Evaluated for potential integration
    - **Referenced in**: `agile_v_skills_repo_improvement_plan.md:816`

17. **pydantic/pydantic-ai**
    - **URL**: https://github.com/pydantic/pydantic-ai
    - **Documentation**: https://pydantic.dev/docs/ai/overview/
    - **Status**: Evaluated for potential integration
    - **Referenced in**: `agile_v_skills_repo_improvement_plan.md:817`

18. **run-llama/llama_index**
    - **URL**: https://github.com/run-llama/llama_index
    - **Documentation**: https://developers.llamaindex.ai/python/llamaagents/workflows/
    - **Status**: Evaluated for potential integration
    - **Referenced in**: `agile_v_skills_repo_improvement_plan.md:818`

19. **SWE-agent/SWE-agent**
    - **URL**: https://github.com/SWE-agent/SWE-agent
    - **Status**: Evaluated for potential integration
    - **Referenced in**: `agile_v_skills_repo_improvement_plan.md:821`

---

## 📖 External Documentation & Resources

### Specifications & Standards

1. **AgentSkills.io Specification**
   - **URL**: https://agentskills.io/specification
   - **Purpose**: Agent skill format specification
   - **Contribution**: Standard format for skill definitions and agent capabilities
   - **Referenced throughout**: README, skill files, schemas

2. **Agile-V.org**
   - **URL**: https://agile-v.org
   - **Purpose**: Official Agile V framework homepage and documentation
   - **Referenced in**: Multiple locations as standard reference

3. **JSON Schema**
   - **URLs**:
     - http://json-schema.org/draft-07/schema
     - https://json-schema.org/draft/2020-12/schema
   - **Purpose**: Schema definitions for configuration and validation
   - **Referenced in**: Schema files throughout the codebase

4. **Semantic Versioning (SemVer)**
   - **URL**: https://semver.org/
   - **Purpose**: Versioning strategy
   - **Referenced in**: Release management and changelog

5. **Conventional Commits**
   - **URL**: https://www.conventionalcommits.org/
   - **Purpose**: Commit message format for automated versioning and changelog generation
   - **Referenced in**: Git workflow and CI/CD

6. **Model Context Protocol**
   - **URL**: https://modelcontextprotocol.io/specification/2025-06-18
   - **Purpose**: Protocol specification for future integration consideration
   - **Referenced in**: `agile_v_skills_repo_improvement_plan.md:819`

### Tool-Specific Documentation

7. **KiCad CLI Documentation**
   - **URL**: https://docs.kicad.org/9.0/en/cli/cli.html
   - **Purpose**: KiCad command-line interface for PCB automation
   - **Contribution**: Reference for PCB design automation using KiCad 8.0+
   - **Referenced in**: `agentic_agile_v_pcb_development_integration_plan.md:24`

8. **OpenHands Documentation**
   - **URL**: https://docs.all-hands.dev
   - **Purpose**: Official documentation for OpenHands integration
   - **Referenced in**: `docs/integrations/openhands.md:662`

9. **pytest Documentation**
   - **URL**: https://docs.pytest.org/en/stable/how-to/cache.html
   - **Purpose**: Testing framework documentation
   - **Referenced in**: `.pytest_cache/README.md:8`

### Platform-Specific Documentation

10. **GitHub Copilot Skills Documentation**
    - **URL**: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
    - **Purpose**: GitHub Copilot skill development
    - **Referenced in**: Skills integration documentation

11. **Cursor Skills Documentation**
    - **URL**: https://cursor.com/docs/context/skills
    - **Purpose**: Cursor IDE skill integration
    - **Referenced in**: Editor configuration docs

12. **Claude Code Skills Documentation**
    - **URL**: https://code.claude.com/docs/en/skills
    - **Purpose**: Claude Code skill development
    - **Referenced in**: Skills integration documentation

13. **VS Code Copilot Skills Documentation**
    - **URL**: https://code.visualstudio.com/docs/copilot/customization/agent-skills
    - **Purpose**: VS Code agent skill customization
    - **Referenced in**: Editor configuration docs

### Component & Vendor Documentation

14. **Espressif ESP32 Documentation**
    - **URL**: https://www.espressif.com/sites/default/files/documentation/esp32-c3-mini-1_datasheet_en.pdf
    - **Purpose**: ESP32-C3 datasheet for PCB examples
    - **Referenced in**: `examples/pcb/component_index.json:93,98`

15. **Component Supplier References** (in PCB examples)
    - Digikey: https://www.digikey.com/
    - Yageo: https://www.yageo.com/
    - Samsung Semiconductor: https://www.samsung.com/semiconductor/
    - Murata: https://www.murata.com/
    - Diodes Inc.: https://www.diodes.com/
    - GCT: https://gct.co/
    - Würth Elektronik: https://www.we-online.com/
    - **Purpose**: Component sourcing and datasheets for PCB design

---

## 📋 Compliance Standards & Regulations

### ISO Standards

1. **ISO 9001:2015** - Quality Management Systems
   - **Status**: Aligned (Design Phase)
   - **Coverage**: 3 Compliant, 9 Partial, 2 Non-Compliant clauses
   - **Documentation**: Compliance matrices and gap analysis

2. **ISO 13485:2016** - Medical Device Quality Management
   - **Status**: Partial (Design Controls)
   - **Coverage**: 2 Compliant, 6 Partial, 6 Non-Compliant clauses
   - **Documentation**: Compliance matrices and gap roadmap

3. **ISO 27001:2022** - Information Security Management
   - **Status**: Aligned (Development Controls)
   - **Coverage**: 5 Compliant, 10 Partial, 2 Non-Compliant controls
   - **Documentation**: Security compliance documentation

4. **ISO 26262** - Automotive Functional Safety
   - **Referenced in**: Embedded systems development skills
   - **Context**: Safety-critical automotive software development

### Aerospace & Industry Standards

5. **AS9100D** - Aerospace Quality Management
   - **Status**: Aligned
   - **Documentation**: AS9100D-specific compliance matrices

6. **IEC 61508** - Functional Safety of Electrical/Electronic/Programmable Electronic Safety-related Systems
   - **Referenced in**: Embedded systems development
   - **Context**: Safety integrity levels (SIL) for safety-critical systems

7. **DO-178C** - Software Considerations in Airborne Systems and Equipment Certification
   - **Referenced in**: Embedded systems development
   - **Context**: Avionics software development and certification

### Pharmaceutical & Regulatory

8. **GxP / GAMP 5** - Good Automated Manufacturing Practice
   - **Status**: Aware
   - **Coverage**: 3 Compliant, 3 Partial, 2 Non-Compliant requirements
   - **Documentation**: GxP compliance matrices

9. **21 CFR Part 11** - FDA Electronic Records and Electronic Signatures
   - **Status**: Partial
   - **Gap**: Electronic signature infrastructure
   - **Documentation**: Compliance gap roadmap

10. **EU Annex 11** - Computerized Systems
    - **Referenced in**: Compliance documentation
    - **Context**: Electronic signature requirements for pharmaceutical systems

### Software Development Standards

11. **MISRA-C:2012** - Motor Industry Software Reliability Association C Coding Standard
    - **Referenced in**: Embedded systems development (19 matches)
    - **Context**: Safety-critical C programming guidelines

12. **AUTOSAR** - Automotive Open System Architecture
    - **Referenced in**: Embedded systems documentation
    - **Context**: Automotive software architecture standards

13. **V-Model** - Software Development Lifecycle
    - **Referenced extensively**: Throughout development documentation
    - **Context**: Development lifecycle methodology for safety-critical systems

---

## 📦 Dependencies

### Python Dependencies (pyproject.toml)

**Main Dependencies:**
- `pyyaml>=6.0` - YAML parsing and configuration

**Development Dependencies:**
- `pytest>=8.0` - Testing framework
- `pytest-cov>=5.0` - Code coverage reporting
- `ruff>=0.4` - Linting and code formatting
- `mypy>=1.10` - Static type checking

### JavaScript/Node Dependencies (Test Projects)

**NestJS Test Project:**
- `@nestjs/common@^11.1.23`
- `@nestjs/core@^11.1.23`
- `reflect-metadata@^0.2.2`
- `rxjs@^7.8.2`

---

## 🏆 Attribution & Licensing

### Copyright Holders

1. **Agile V™**
   - **Email**: info@agile-v.org, hello@agile-v.org
   - **Copyright**: Agile-V framework and implementation
   - **License**: Proprietary

2. **Lex Christopherson**
   - **Copyright**: © 2025 Lex Christopherson
   - **License**: MIT License
   - **Contribution**: GSD patterns (Get Shit Done)
   - **Referenced in**: Orchestration and context engineering patterns

3. **Kadajett**
   - **Copyright**: © 2024 Kadajett
   - **License**: MIT License
   - **Contribution**: NestJS agent skills

### License Information

- **This Repository**: Proprietary / Agile-V™
- **agile_v_skills**: CC-BY-SA-4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
- **OpenHands**: MIT License
- **Understand Anything**: MIT License
- **GSD**: MIT License
- **Karpathy Skills**: MIT License
- **Kadajett NestJS Skills**: MIT License

---

## 📊 Contribution Summary

- **Academic Papers**: 1 (pcbGPT)
- **GitHub Repositories**: 19 repositories (7 Agile-V, 4 upstream sources, 1 execution backend, 7 evaluated frameworks)
- **External Documentation Sites**: 15+
- **Compliance Standards**: 13+ standards (ISO, aerospace, pharmaceutical, automotive)
- **Total URL References**: 195+ unique URLs
- **Primary Licenses**: MIT, CC-BY-SA-4.0, Proprietary

---

## 🎯 Key Integration Points

1. **OpenHands** (1,085+ references) - Autonomous execution backend
2. **Understand Anything** (185+ references) - Knowledge graph for system understanding
3. **Get Shit Done** - Context engineering and orchestration patterns
4. **Karpathy Skills** - Behavioral guidelines and agent interaction patterns
5. **KiCad** (273+ references) - PCB design automation

---

## 📝 Notes

- All external references are properly attributed with URLs and license information
- MIT-licensed patterns and code maintain original copyright notices with Agile-V adaptations noted
- Compliance standards are referenced for alignment purposes; full certification requires additional implementation
- Component datasheets and vendor documentation are referenced for PCB design automation examples

---

**Last Updated**: June 2026  
**Repository Version**: Based on commit `fe8c896` (feat/pcb-development-integration)

For questions or attribution clarifications, contact: info@agile-v.org
