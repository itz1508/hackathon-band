# System Architecture

## High-Level Architecture Diagram

```mermaid
graph TB
    subgraph Desktop["Desktop Application"]
        UI["Qt/QML UI<br/>- Folder Selection<br/>- Progress Tracking<br/>- Results Display"]
        Bridge["Qt/Python Bridge<br/>- Signal/Slot Communication<br/>- Type Conversion"]
    end
    
    subgraph Backend["Python Backend"]
        Scanner["Scanner<br/>- Folder Traversal<br/>- Issue Detection<br/>- File Analysis"]
        Planner["Planner<br/>- Task Creation<br/>- Step Generation<br/>- Time Estimation"]
        Validator["Validator<br/>- Plan Verification<br/>- Gap Detection<br/>- Scoring"]
        Simulator["Simulator<br/>- Safe Execution<br/>- Issue Analysis<br/>- Report Gen"]
    end
    
    subgraph Cloud["Alibaba Cloud"]
        Qwen["Qwen LLM<br/>- Plan Enhancement<br/>- Confidence Calc<br/>- Analysis"]
        OSS["OSS Storage<br/>- Report Archive<br/>- Artifact Store<br/>- Backup"]
        ECS["ECS Deployment<br/>- Backend Hosting<br/>- Scaling<br/>- HA"]
    end
    
    UI -->|Qt Signals| Bridge
    Bridge -->|Python Calls| Scanner
    Scanner -->|Issues| Planner
    Planner -->|Plan| Validator
    Validator -->|Validation| Simulator
    Simulator -->|Report| UI
    
    Planner -->|API Call| Qwen
    Simulator -->|Store| OSS
    Backend -->|Deploy| ECS
```

## Component Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Qt/QML UI
    participant Bridge as Qt/Python Bridge
    participant Backend as Python Backend
    participant Qwen as Qwen LLM
    participant OSS as OSS Storage
    
    User->>UI: Select Folder
    UI->>Bridge: startWorkflow(folderPath)
    Bridge->>Backend: scan_folder()
    Backend->>Backend: Analyze Files
    Backend-->>Bridge: ScanResult
    Bridge-->>UI: onScanCompleted()
    
    Backend->>Backend: create_plan()
    Backend->>Qwen: Generate Plan
    Qwen-->>Backend: Plan with Confidence
    Backend-->>Bridge: Plan
    Bridge-->>UI: onPlanCreated()
    
    Backend->>Backend: validate_plan()
    Backend-->>Bridge: ValidationResult
    Bridge-->>UI: onValidationCompleted()
    
    Backend->>Backend: simulate_execution()
    Backend-->>Bridge: SimulationResult
    Bridge-->>UI: onSimulationCompleted()
    
    Backend->>Backend: generate_report()
    Backend->>OSS: Store Report
    OSS-->>Backend: Stored
    Backend-->>Bridge: Report
    Bridge-->>UI: onReportGenerated()
    
    UI->>User: Display Results
```

## Data Flow Architecture

```mermaid
graph LR
    A["Input<br/>Folder Path"] -->|Scan| B["ScanResult<br/>Files & Issues"]
    B -->|Plan| C["Plan<br/>Steps & Confidence"]
    C -->|Validate| D["ValidationResult<br/>Score & Readiness"]
    D -->|Simulate| E["SimulationResult<br/>Output & Status"]
    E -->|Report| F["Report<br/>Complete Data"]
    F -->|Store| G["OSS<br/>Archive"]
```

## Deployment Architecture

```mermaid
graph TB
    subgraph Local["Local Development"]
        Dev["Developer Machine<br/>Qt/QML + Python"]
    end
    
    subgraph Cloud["Alibaba Cloud"]
        subgraph ECS["ECS Instance"]
            Backend["Agent MVP Backend<br/>Python + Qt"]
        end
        
        subgraph Services["Cloud Services"]
            Qwen["Qwen LLM API"]
            OSS["OSS Bucket"]
            Monitor["CloudWatch"]
        end
    end
    
    Dev -->|Deploy| Backend
    Backend -->|API Calls| Qwen
    Backend -->|Store| OSS
    Backend -->|Metrics| Monitor
```

## Technology Stack

### Frontend
- **Qt 6.4.2** — Desktop UI framework
- **QML** — UI markup language
- **C++17** — Native performance

### Backend
- **Python 3.8+** — Core logic
- **JSON** — Data serialization
- **Subprocess** — Command execution

### Cloud Integration
- **Alibaba Cloud Qwen** — LLM services
- **Alibaba Cloud OSS** — Object storage
- **Alibaba Cloud ECS** — Compute resources

### Build & Deployment
- **CMake 3.20+** — Build system
- **Git** — Version control
- **Docker** — Containerization (optional)

## Security Architecture

```mermaid
graph TB
    subgraph Security["Security Layers"]
        Auth["Authentication<br/>IAM Roles"]
        Encrypt["Encryption<br/>TLS/SSL"]
        Audit["Audit Logging<br/>CloudWatch"]
        Sandbox["Sandbox Mode<br/>Read-Only"]
    end
    
    subgraph Data["Data Protection"]
        Input["Input Validation"]
        Output["Output Sanitization"]
        Store["Secure Storage"]
    end
    
    Auth --> Encrypt
    Encrypt --> Audit
    Audit --> Sandbox
    Input --> Store
    Output --> Store
```

## Performance Architecture

```mermaid
graph LR
    A["Scan<br/>1-5s"] -->|Cache| B["Plan<br/>100ms"]
    B -->|Parallel| C["Validate<br/>50ms"]
    C -->|Async| D["Simulate<br/>2-10s"]
    D -->|Batch| E["Report<br/>100ms"]
```

## Scaling Architecture

```mermaid
graph TB
    subgraph Scale["Horizontal Scaling"]
        LB["Load Balancer"]
        I1["Instance 1"]
        I2["Instance 2"]
        I3["Instance N"]
    end
    
    subgraph Data["Shared Data Layer"]
        OSS["OSS Storage"]
        Cache["Redis Cache"]
    end
    
    LB -->|Route| I1
    LB -->|Route| I2
    LB -->|Route| I3
    
    I1 -->|Read/Write| OSS
    I2 -->|Read/Write| OSS
    I3 -->|Read/Write| OSS
    
    I1 -->|Cache| Cache
    I2 -->|Cache| Cache
    I3 -->|Cache| Cache
```

## API Architecture

```mermaid
graph TB
    subgraph REST["REST API Layer"]
        Scan["POST /api/scan"]
        Plan["POST /api/plan"]
        Validate["POST /api/validate"]
        Simulate["POST /api/simulate"]
        Report["GET /api/report/:id"]
    end
    
    subgraph Backend["Backend Processing"]
        Scanner["Scanner"]
        Planner["Planner"]
        Validator["Validator"]
        Simulator["Simulator"]
    end
    
    Scan -->|Process| Scanner
    Plan -->|Process| Planner
    Validate -->|Process| Validator
    Simulate -->|Process| Simulator
    Report -->|Retrieve| Simulator
```

## Database Schema

```mermaid
erDiagram
    TASK ||--o{ SCAN : has
    TASK ||--o{ PLAN : has
    TASK ||--o{ VALIDATION : has
    TASK ||--o{ SIMULATION : has
    TASK ||--o{ REPORT : generates
    
    TASK {
        string task_id PK
        string folder_path
        timestamp created_at
        timestamp updated_at
        string status
    }
    
    SCAN {
        string scan_id PK
        string task_id FK
        int files_scanned
        int issues_found
        json issues
        timestamp timestamp
    }
    
    PLAN {
        string plan_id PK
        string task_id FK
        string description
        json steps
        float estimated_time
        float confidence
        timestamp created_at
    }
    
    VALIDATION {
        string validation_id PK
        string task_id FK
        boolean is_valid
        float score
        json gaps
        boolean ready_for_simulation
    }
    
    SIMULATION {
        string simulation_id PK
        string task_id FK
        boolean success
        string output
        json errors
        json changes_made
        timestamp completed_at
    }
    
    REPORT {
        string report_id PK
        string task_id FK
        json scan_data
        json plan_data
        json validation_data
        json simulation_data
        timestamp generated_at
    }
```

## Error Handling Flow

```mermaid
graph TB
    A["Input"] -->|Validate| B{Valid?}
    B -->|No| C["Error Handler"]
    B -->|Yes| D["Process"]
    D -->|Exception| E["Catch"]
    E -->|Log| F["CloudWatch"]
    F -->|Notify| G["User"]
    C -->|Return| G
```

## Monitoring Architecture

```mermaid
graph TB
    subgraph App["Application"]
        Scan["Scan Phase"]
        Plan["Plan Phase"]
        Validate["Validate Phase"]
        Simulate["Simulate Phase"]
    end
    
    subgraph Monitor["Monitoring"]
        Metrics["Metrics<br/>Duration, Success Rate"]
        Logs["Logs<br/>Detailed Events"]
        Traces["Traces<br/>Request Flow"]
    end
    
    subgraph Cloud["Alibaba Cloud"]
        CW["CloudWatch<br/>Dashboards & Alerts"]
    end
    
    Scan -->|Emit| Metrics
    Plan -->|Emit| Metrics
    Validate -->|Emit| Metrics
    Simulate -->|Emit| Metrics
    
    Scan -->|Write| Logs
    Plan -->|Write| Logs
    Validate -->|Write| Logs
    Simulate -->|Write| Logs
    
    Metrics -->|Send| CW
    Logs -->|Send| CW
    Traces -->|Send| CW
```

## Deployment Checklist

- [ ] Qt 6.0+ installed
- [ ] Python 3.8+ installed
- [ ] CMake 3.20+ installed
- [ ] Alibaba Cloud credentials configured
- [ ] OSS bucket created
- [ ] Qwen API key obtained
- [ ] ECS instance launched
- [ ] Security groups configured
- [ ] Application built
- [ ] Tests passed
- [ ] Documentation complete

---

**Architecture Version**: 1.0.0 | **Last Updated**: 2026-06-17
