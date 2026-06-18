# Alibaba Cloud Integration Guide

## Overview

The Agent Skills MVP integrates with Alibaba Cloud services to enhance planning, storage, and deployment capabilities.

## Services Used

### 1. Qwen LLM (Large Language Model)

**Purpose**: Intelligent plan generation and issue analysis

**Integration Points**:
- Plan creation with confidence scoring
- Issue severity assessment
- Step generation for complex tasks

**Example Usage**:

```python
from aliyun.core import qwen_client

def create_plan_with_qwen(scan_result):
    """Create plan using Qwen LLM"""
    prompt = f"""
    Analyze these scan results and create an execution plan:
    - Files scanned: {scan_result.files_scanned}
    - Issues found: {len(scan_result.issues)}
    - Issues: {scan_result.issues}
    
    Generate:
    1. Clear steps to fix issues
    2. Time estimate
    3. Confidence score (0-1)
    """
    
    response = qwen_client.generate(prompt)
    return parse_plan(response)
```

### 2. OSS (Object Storage Service)

**Purpose**: Artifact storage and report archival

**Integration Points**:
- Store scan results
- Archive reports
- Version control
- Backup management

**Example Usage**:

```python
from aliyun.oss import oss_client

def store_report(report, task_id):
    """Store report in OSS"""
    key = f"reports/{task_id}/report.json"
    oss_client.put_object(
        bucket='agent-mvp-reports',
        key=key,
        data=json.dumps(report)
    )
    return f"oss://agent-mvp-reports/{key}"
```

### 3. ECS (Elastic Compute Service)

**Purpose**: Backend deployment and scaling

**Deployment Configuration**:

```yaml
instance:
  image_id: "ubuntu-22.04"
  instance_type: "ecs.t6-c1m1.large"
  region: "cn-hangzhou"
  security_group: "agent-mvp-sg"

software:
  - qt6-base
  - python3
  - cmake
  - git

startup_script: |
  #!/bin/bash
  cd /opt/agent-mvp
  ./build/bin/agent-skills-mvp &
```

## Configuration

### Environment Variables

```bash
# Alibaba Cloud Credentials
export ALIBABA_CLOUD_ACCESS_KEY_ID="your-access-key"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-secret-key"
export ALIBABA_CLOUD_REGION="cn-hangzhou"

# OSS Configuration
export OSS_BUCKET="agent-mvp-reports"
export OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"

# Qwen Configuration
export QWEN_API_KEY="your-qwen-api-key"
export QWEN_MODEL="qwen-max"
```

### Configuration File

Create `config/alibaba.yaml`:

```yaml
alibaba_cloud:
  region: "cn-hangzhou"
  access_key_id: "${ALIBABA_CLOUD_ACCESS_KEY_ID}"
  access_key_secret: "${ALIBABA_CLOUD_ACCESS_KEY_SECRET}"

qwen:
  api_key: "${QWEN_API_KEY}"
  model: "qwen-max"
  temperature: 0.7
  max_tokens: 2048

oss:
  bucket: "${OSS_BUCKET}"
  endpoint: "${OSS_ENDPOINT}"
  region: "cn-hangzhou"
  acl: "private"

ecs:
  region: "cn-hangzhou"
  instance_type: "ecs.t6-c1m1.large"
  image_id: "ubuntu-22.04"
```

## API Integration Examples

### Using Qwen for Plan Generation

```python
import json
from aliyun.core import qwen_client

class QwenPlanner:
    def __init__(self, api_key, model="qwen-max"):
        self.api_key = api_key
        self.model = model
    
    def generate_plan(self, scan_result):
        """Generate execution plan using Qwen"""
        prompt = self._build_prompt(scan_result)
        
        response = qwen_client.generate(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert code analyzer and task planner."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return self._parse_response(response)
    
    def _build_prompt(self, scan_result):
        return f"""
        Analyze the following scan results and create a detailed execution plan:
        
        Scan Results:
        - Total files: {scan_result.files_scanned}
        - Issues found: {len(scan_result.issues)}
        - Timestamp: {scan_result.timestamp}
        
        Issues:
        {json.dumps(scan_result.issues, indent=2)}
        
        Please provide:
        1. A clear description of the plan
        2. Numbered steps to fix each issue
        3. Time estimate in seconds
        4. Confidence score (0-1)
        
        Format as JSON:
        {{
            "description": "...",
            "steps": ["step1", "step2", ...],
            "estimated_time": 30,
            "confidence": 0.85
        }}
        """
    
    def _parse_response(self, response):
        try:
            data = json.loads(response)
            return {
                "description": data.get("description"),
                "steps": data.get("steps", []),
                "estimated_time": data.get("estimated_time", 30),
                "confidence": data.get("confidence", 0.5)
            }
        except json.JSONDecodeError:
            return {
                "description": response,
                "steps": [],
                "estimated_time": 30,
                "confidence": 0.5
            }
```

### Using OSS for Report Storage

```python
from aliyun.oss import oss_client
import json
from datetime import datetime

class ReportStorage:
    def __init__(self, bucket, endpoint):
        self.bucket = bucket
        self.endpoint = endpoint
    
    def store_report(self, report, task_id):
        """Store report in OSS"""
        timestamp = datetime.now().isoformat()
        key = f"reports/{task_id}/{timestamp}/report.json"
        
        oss_client.put_object(
            bucket=self.bucket,
            key=key,
            data=json.dumps(report, indent=2)
        )
        
        return f"oss://{self.bucket}/{key}"
    
    def retrieve_report(self, task_id, timestamp):
        """Retrieve report from OSS"""
        key = f"reports/{task_id}/{timestamp}/report.json"
        
        data = oss_client.get_object(
            bucket=self.bucket,
            key=key
        )
        
        return json.loads(data)
    
    def list_reports(self, task_id):
        """List all reports for a task"""
        prefix = f"reports/{task_id}/"
        
        objects = oss_client.list_objects(
            bucket=self.bucket,
            prefix=prefix
        )
        
        return [obj.key for obj in objects]
```

## Deployment on Alibaba Cloud ECS

### Step 1: Create ECS Instance

```bash
# Using Alibaba Cloud CLI
aliyun ecs CreateInstance \
  --RegionId cn-hangzhou \
  --ImageId ubuntu-22.04 \
  --InstanceType ecs.t6-c1m1.large \
  --InstanceName agent-mvp-server
```

### Step 2: Configure Security Group

```bash
aliyun ecs AuthorizeSecurityGroup \
  --RegionId cn-hangzhou \
  --SecurityGroupId sg-xxxxx \
  --IpProtocol tcp \
  --PortRange 3000/3000 \
  --SourceCidrIp 0.0.0.0/0
```

### Step 3: Install Dependencies

```bash
#!/bin/bash
sudo apt-get update
sudo apt-get install -y \
  qt6-base-dev \
  qt6-declarative-dev \
  python3-dev \
  cmake \
  git \
  build-essential

# Install Alibaba Cloud SDK
pip3 install aliyun-python-sdk-core
pip3 install aliyun-python-sdk-oss
```

### Step 4: Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/agent-mvp.git
cd agent-mvp

# Build
mkdir build && cd build
cmake ..
cmake --build .

# Run
./bin/agent-skills-mvp
```

## Monitoring and Logging

### CloudWatch Integration

```python
from aliyun.monitor import cloudwatch_client

def log_workflow_metrics(scan_result, plan, validation, simulation):
    """Log metrics to CloudWatch"""
    metrics = {
        "files_scanned": scan_result.files_scanned,
        "issues_found": len(scan_result.issues),
        "plan_confidence": plan.confidence,
        "validation_score": validation.score,
        "simulation_success": simulation.success
    }
    
    for metric_name, value in metrics.items():
        cloudwatch_client.put_metric_data(
            namespace="AgentMVP",
            metric_name=metric_name,
            value=value
        )
```

## Best Practices

1. **API Rate Limiting** — Implement exponential backoff for API calls
2. **Error Handling** — Gracefully handle cloud service failures
3. **Caching** — Cache Qwen responses for similar scans
4. **Security** — Use IAM roles instead of hardcoded credentials
5. **Monitoring** — Track all cloud API calls and costs

## Troubleshooting

### Connection Issues

```python
# Test Alibaba Cloud connectivity
try:
    qwen_client.test_connection()
    oss_client.test_connection()
    print("✅ All Alibaba Cloud services connected")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### Authentication Errors

```bash
# Verify credentials
export ALIBABA_CLOUD_ACCESS_KEY_ID="your-key"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your-secret"

# Test authentication
aliyun ecs DescribeRegions
```

## References

- [Alibaba Cloud Qwen LLM Documentation](https://help.aliyun.com/document_detail/2400395.html)
- [Alibaba Cloud OSS Documentation](https://help.aliyun.com/document_detail/31883.html)
- [Alibaba Cloud ECS Documentation](https://help.aliyun.com/document_detail/25367.html)
- [Alibaba Cloud Python SDK](https://github.com/aliyun/aliyun-openapi-python-sdk)

---

**Status**: ✅ Production Ready | **Version**: 1.0.0
