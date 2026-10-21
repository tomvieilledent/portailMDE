# Maison de l'Économie Dashboard – Project Charter (Stage 2)

## Table of Contents

1. SMART Method
2. Identify Stakeholders and Team Roles
3. Project Scope
4. Identify Risks
5. Develop a High-Level Plan

---

## 1. SMART Method

| Criterion      | Description                                                                                                                                                                                                                                                                                                |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Specific**   | Develop a comprehensive web platform (Maison de l'Économie Dashboard) enabling member companies to communicate, learn, access training resources, and monitor economic news within a centralized ecosystem.                                                                                                |
| **Measurable** | Success is measured by: platform adoption rate among member companies, user engagement metrics (login frequency, feature usage), training course completions, messaging activity volume, and stakeholder satisfaction scores. Deliverables include working features, deployed MVP, and user documentation. |
| **Achievable** | The project is feasible within 12 weeks using proven technologies (Python Flask, React, PostgreSQL, WebSockets). The team comprises three capable fullstack developers with balanced expertise. MVP scope focuses on essential features; advanced features deferred to Phase 2.                            |
| **Relevant**   | Directly addresses real stakeholder needs: improving communication channels, enabling professional development, building network effects, and increasing member retention for Maison de l'Économie. The platform creates tangible business value for the organization.                                     |
| **Time-bound** | Project completion target: 12 weeks from start to production deployment. Major milestones at weeks 2, 4, 6, 9, and 12. Two-week sprints with client validation every two weeks ensure timeline adherence.                                                                                                  |

---

## 2. Identify Stakeholders and Team Roles

### Stakeholders

| Stakeholder Category   | Name/Role                               | Responsibilities                                                                                    |
| ---------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **Internal (Project)** | Tom Vieilledent (Backend Developer)     | API development, database architecture, WebSocket implementation, backend system design             |
|                        | Nabil Zinini (Frontend Developer)       | User interface design, React component development, responsive design, user experience optimization |
|                        | Florian Roosebeke (Fullstack Developer) | Cross-layer integration, technical bottleneck resolution, architecture review, quality assurance    |
| **External (Client)**  | Céline (Manager)                        | Strategic direction, requirement validation, scope approval, executive decision-making              |
|                        | Karine (Manager)                        | Operations oversight, user feedback collection, feature validation, deployment support              |
| **External (Support)** | Holberton School                        | Technical mentorship, infrastructure access, evaluation and project validation                      |

### Team Roles

| Role                       | Team Member(s)    | Responsibilities                                                                                                                 |
| -------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Project Manager / Lead** | Florian Roosebeke | Oversee timeline, coordinate between frontend/backend, ensure feature integration, track progress, manage dependencies           |
| **Backend Developer**      | Tom Vieilledent   | Design and implement Flask API, create database schema, implement authentication, develop WebSocket services, API documentation  |
| **Frontend Developer**     | Nabil Zinini      | Build React components, implement responsive design with Tailwind, manage application state, ensure UX quality, frontend testing |
| **Fullstack Support**      | Florian Roosebeke | Bridge frontend/backend gaps, assist with integration, perform end-to-end testing, troubleshoot cross-layer issues               |
| **QA / Tester**            | All Team Members  | Perform unit testing, integration testing, user acceptance testing, identify and document bugs                                   |
| **Documentation Lead**     | Florian Roosebeke | Prepare API documentation, create deployment guides, write user manuals, document architecture decisions                         |

---

## 3. Project Scope

### In-Scope Features (MVP Phase 1)

- **User Authentication & Authorization**: Secure login system with role-based access control (Admin, Company User, Employee)
- **Companies & Employees Directory**: Searchable directory with company profiles, employee listings, and contact information
- **Training Catalog**: Browse, search, and enroll in professional development courses with progress tracking
- **Internal Messaging System**: Real-time messaging between users and companies using WebSockets
- **Economic News Monitoring**: Curated economic news feed with filters and search functionality
- **User Profiles**: User profile pages with customizable information and preferences
- **Responsive Design**: Fully responsive interface supporting desktop, tablet, and mobile devices
- **Search & Filtering**: Advanced search across directory, training catalog, and news
- **User Notifications**: In-app notifications for messages, course updates, and system announcements
- **Database & API**: RESTful API with proper authentication, PostgreSQL database, SQLAlchemy ORM
- **Deployment**: Production-ready deployment configuration with documentation

### Out-of-Scope Features (Phase 2+)

- **Real-time Notifications**: Push notifications and email alerts (deferred to Phase 2)
- **Dashboard Analytics**: User engagement statistics and business intelligence dashboards
- **Event Management**: Company event creation, registration, and calendar integration
- **Document Sharing**: File upload and company-level document management
- **Video Training**: Video content delivery for courses
- **Advanced Search**: AI-powered recommendation engine
- **Mobile App**: Native iOS/Android applications
- **Multi-language Support**: Internationalization beyond current language
- **Social Features**: User following, commenting, ratings, and reviews

---

## 4. Identify Risks

### Purpose

To identify potential challenges and obstacles that could affect project success, and establish mitigation strategies to minimize impact on timeline, quality, and scope.

### Risks and Solutions

| Risk Category    | Risk Description                                                 | Impact | Probability | Mitigation Strategy                                                                                                           |
| ---------------- | ---------------------------------------------------------------- | ------ | ----------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Technical**    | WebSocket implementation complexity and real-time messaging bugs | High   | High        | Early prototype development (Week 2-3); use proven Socket.io library; dedicated learning sessions; thorough testing framework |
| **Technical**    | Database performance issues with large user datasets             | High   | Medium      | Implement query optimization early; add database indexing; load testing in Week 8-9; performance monitoring setup             |
| **Technical**    | Authentication/authorization security vulnerabilities            | High   | Medium      | Use Flask-JWT-Extended library; security code review; implement OWASP best practices; penetration testing                     |
| **Timeline**     | 12-week deadline too tight for scope                             | High   | Medium      | Strict feature prioritization; scope freeze after Week 8; weekly progress tracking; client communication on delays            |
| **Timeline**     | Developer unavailability (illness, conflict)                     | Medium | Medium      | Clear task documentation; pair programming on critical features; knowledge sharing sessions; task cross-assignment            |
| **Team**         | Integration issues between frontend and backend                  | Medium | Medium      | Define API contracts early; weekly integration testing; daily standups; clear communication channels                          |
| **Requirements** | Scope creep or requirement changes mid-project                   | Medium | High        | Formal change request process; bi-weekly client validation; "no new features" rule after Week 8; clear done criteria          |
| **Deployment**   | Server/database configuration issues at deployment               | Medium | Low         | Test deployment early (Week 9); use infrastructure-as-code; documentation of all setup steps; dry-run before final deployment |
| **Quality**      | Insufficient testing leading to production bugs                  | Medium | Medium      | Test-driven development approach; automated testing suite; reserve Week 10-11 for QA; user acceptance testing with client     |
| **External**     | Client unavailability for validation meetings                    | Low    | Low         | Schedule meetings well in advance; provide async feedback options; documentation for self-review                              |

---

## 5. Develop a High-Level Plan

### Purpose

To outline the main phases and activities from project initiation through delivery, providing a clear roadmap for successful MVP development and deployment.

### High-Level Plan

| Phase                               | Activity                                                                                                                                                          | Deliverable                                                                                            |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **1. Setup & Configuration**        | Create GitHub repository, set up development environments, install dependencies (Flask, React, PostgreSQL), initialize database, configure CI/CD pipeline         | Project repository ready, development environment configured, empty application scaffolding            |
| **2. Architecture & Design**        | Design system architecture (frontend/backend separation), create database schema, define API routes and WebSocket contracts, design UI mockups/wireframes         | Documented architecture diagram, ER diagram for database, API specification document, UI design system |
| **3. Core Backend**                 | Implement user authentication system, set up database models, create core API routes (users, companies, employees), implement JWT token management                | Working login system, functional API endpoints, database with test data                                |
| **4. Core Frontend**                | Build main layout components (navbar, sidebar), create authentication pages (login/signup), set up routing structure, implement responsive design foundation      | Functional login flow, navigable layout, responsive pages                                              |
| **5. Directory Feature**            | Implement companies and employees database models, create directory search/filter API, build directory UI components and search interface                         | Fully searchable directory, company profiles, employee listings                                        |
| **6. Training Feature**             | Create training course database models, build course catalog API, implement course browsing/enrollment UI, add progress tracking                                  | Working training catalog with enrollment, progress tracking                                            |
| **7. Real-time Messaging**          | Implement WebSocket server with Socket.io, create messaging database model, build messaging UI components, integrate real-time updates                            | Real-time messaging functional between users                                                           |
| **8. News Feature**                 | Set up news data source/API, create news database model, implement news filtering and search, build news feed UI                                                  | Economic news display with filtering                                                                   |
| **9. Integration & Optimization**   | Connect all features together, optimize database queries, optimize frontend performance, implement error handling and loading states                              | Fully integrated MVP, improved performance                                                             |
| **10. Testing & QA**                | Unit testing for critical functions, integration testing of features, end-to-end user testing, bug identification and fixing, user acceptance testing with client | Test report with <5% critical bugs, client sign-off                                                    |
| **11. Documentation & Deployment**  | Write API documentation, create deployment guide, set up production environment, perform security audit, prepare user documentation                               | Deployed live application, documentation complete, deployment runbook                                  |
| **12. Final Review & Presentation** | Bug fixes from UAT, performance tuning, prepare project presentation, knowledge transfer documentation, final client demo                                         | Production-ready system, presentation materials                                                        |

### Timeline

**Week 1-2: Project Setup (Phase 1-2)**

- Repository initialization and development environment setup
- Architecture design and database schema finalization
- Deliverable: Development environment ready, architecture approved

**Week 3-4: Core Implementation (Phase 3-4)**

- Backend authentication and API foundation
- Frontend layout and authentication UI
- Deliverable: Working login system, basic navigation

**Week 5-6: Features Phase 1 (Phase 5-6)**

- Directory feature implementation
- Training catalog implementation
- Deliverable: Directory and training catalog functional

**Week 7-9: Features Phase 2 & Real-time (Phase 7-8)**

- Real-time messaging with WebSockets
- Economic news feature
- Integration and optimization
- Deliverable: All MVP features complete and integrated

**Week 10: Testing & QA (Phase 10)**

- Comprehensive testing
- Bug fixing
- User acceptance testing
- Deliverable: Quality assurance complete, client validation

**Week 11-12: Deployment & Finalization (Phase 11-12)**

- Production deployment
- Documentation finalization
- Final presentation preparation
- Deliverable: Live production system, documentation, project presentation

---

## Key Metrics & Success Criteria

### Functional Delivery

- All MVP features implemented and operational
- Zero critical bugs in production
- System performance: <2s page load time, <100ms API response

### Quality Standards

- Test coverage: >80% of critical code paths
- Code quality: ESLint pass rate 100%
- Security: Zero OWASP Top 10 vulnerabilities

### Stakeholder Satisfaction

- Client sign-off on feature completeness
- User testing: >80% satisfaction score
- On-time delivery within 12-week timeline

---

## Next Steps

1. **Week 1**: Finalize all technical specifications and development environment setup
2. **Week 1**: First sprint planning meeting with full team
3. **Week 1**: First client validation meeting to confirm scope
4. **Ongoing**: Daily 15-minute standups via Discord
5. **Bi-weekly**: Client validation meetings on Thursdays at 3 PM

---

**Project Charter Approval Date**: May 2026
**Team**: Nabil Zinini, Tom Vieilledent, Florian Roosebeke
**Client Contact**: Maison de l'Économie (Céline & Karine)