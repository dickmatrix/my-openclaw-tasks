# 常见代码模式库

## 错误处理模式

### Go 错误处理
```go
// 定义自定义错误
type ValidationError struct {
    Field string
    Msg   string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error: %s - %s", e.Field, e.Msg)
}

// 使用
if err != nil {
    if ve, ok := err.(*ValidationError); ok {
        log.Printf("Field: %s, Message: %s", ve.Field, ve.Msg)
    }
    return err
}
```

### Python 错误处理
```python
class ValidationError(Exception):
    def __init__(self, field: str, msg: str):
        self.field = field
        self.msg = msg
        super().__init__(f"validation error: {field} - {msg}")

try:
    validate_input(data)
except ValidationError as e:
    logger.error(f"Field: {e.field}, Message: {e.msg}")
```

### TypeScript 错误处理
```typescript
class ValidationError extends Error {
    constructor(public field: string, public msg: string) {
        super(`validation error: ${field} - ${msg}`);
    }
}

try {
    validateInput(data);
} catch (error) {
    if (error instanceof ValidationError) {
        console.error(`Field: ${error.field}, Message: ${error.msg}`);
    }
}
```

## 并发模式

### Go Goroutine 池
```go
type WorkerPool struct {
    jobs    chan Job
    results chan Result
    wg      sync.WaitGroup
}

func (p *WorkerPool) Start(numWorkers int) {
    for i := 0; i < numWorkers; i++ {
        p.wg.Add(1)
        go p.worker()
    }
}

func (p *WorkerPool) worker() {
    defer p.wg.Done()
    for job := range p.jobs {
        result := processJob(job)
        p.results <- result
    }
}
```

### Python 异步处理
```python
async def process_jobs(jobs: List[Job]) -> List[Result]:
    tasks = [process_job(job) for job in jobs]
    return await asyncio.gather(*tasks)

async def process_job(job: Job) -> Result:
    async with aiohttp.ClientSession() as session:
        async with session.get(job.url) as resp:
            return await resp.json()
```

## 数据验证模式

### Pydantic 验证
```python
from pydantic import BaseModel, validator

class User(BaseModel):
    name: str
    email: str
    age: int

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('invalid email')
        return v

    @validator('age')
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError('invalid age')
        return v
```

### TypeScript 类型守卫
```typescript
interface User {
    name: string;
    email: string;
    age: number;
}

function isUser(obj: unknown): obj is User {
    return (
        typeof obj === 'object' &&
        obj !== null &&
        'name' in obj &&
        'email' in obj &&
        'age' in obj &&
        typeof obj.name === 'string' &&
        typeof obj.email === 'string' &&
        typeof obj.age === 'number'
    );
}
```
