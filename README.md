# Django ERP

Django 5.2 기반의 현대적인 HR/급여 관리 ERP 시스템

## 프로젝트 개요

Django Unfold Admin 테마를 활용한 엔터프라이즈급 HR/ERP 시스템입니다. 직원 관리, 근태 관리, 휴가 관리, 급여 관리, 인사평가 등 HR 업무의 전체 라이프사이클을 지원합니다.

### 주요 특징

- **현대적인 관리자 UI**: Django Unfold 테마로 구축된 직관적인 인터페이스
- **FSM 기반 워크플로우**: django-fsm을 활용한 체계적인 상태 관리
- **변경 이력 추적**: django-simple-history로 모든 중요 데이터의 변경 이력 보존
- **객체 레벨 권한**: django-guardian으로 세밀한 접근 제어
- **다중 통화 지원**: django-money를 활용한 급여 관리
- **4대보험 자동 계산**: 국민연금, 건강보험, 고용보험, 소득세 자동 계산

## 기술 스택

- **Backend**: Python 3.13+ / Django 5.2
- **Admin UI**: Django Unfold
- **Database**: SQLite (개발용) / PostgreSQL (프로덕션)
- **State Management**: django-fsm
- **Money Fields**: django-money
- **History Tracking**: django-simple-history
- **Permissions**: django-guardian
- **Import/Export**: django-import-export
- **Package Manager**: Poetry

## 프로젝트 구조

```
django-erp/
├── core/                    # 핵심 모듈
│   ├── models.py           # AuditedModel, User (역할 기반)
│   └── ...
├── organization/           # 조직 구조
│   ├── models.py          # Company, Department, JobGrade, JobPosition
│   └── ...
├── employees/             # 직원 관리
│   ├── models.py         # Employee, EmployeeDocument, EmployeeHistory
│   ├── admin.py          # Unfold Admin 커스터마이징
│   └── ...
├── attendance/           # 근태 관리
│   ├── models.py        # WorkSchedule, AttendanceRecord, OvertimeRequest, Holiday
│   └── ...
├── leave/               # 휴가 관리
│   ├── models.py       # LeaveType, LeaveBalance, LeaveRequest (FSM), LeaveApproval
│   └── ...
├── payroll/            # 급여 관리 ⭐
│   ├── models.py      # PayrollPeriod, Payslip, AllowanceType, DeductionType, SalaryContract
│   ├── admin.py       # 급여 Admin (커스텀 액션)
│   ├── services/      # 비즈니스 로직
│   │   └── payroll_calculator.py  # 급여 계산 엔진
│   └── fixtures/      # 초기 데이터
│       ├── allowance_types.json   # 수당 유형
│       └── deduction_types.json   # 공제 유형
├── evaluation/         # 인사평가 ⭐
│   ├── models.py      # EvaluationTemplate, EvaluationPeriod, EmployeeEvaluation, EvaluationSummary
│   └── ...
└── reports/           # 보고서 (예정)
    └── ...
```

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd django-erp
```

### 2. 가상환경 설정 (Poetry)

```bash
# Poetry 설치 (없는 경우)
curl -sSL https://install.python-poetry.org | python3 -

# 의존성 설치
poetry install

# 가상환경 활성화
poetry shell
```

### 3. 데이터베이스 마이그레이션

```bash
python manage.py migrate
```

### 4. 초기 데이터 로드

```bash
# 수당 및 공제 유형 로드
python manage.py loaddata payroll/fixtures/allowance_types.json
python manage.py loaddata payroll/fixtures/deduction_types.json
```

### 5. 슈퍼유저 생성

```bash
python manage.py createsuperuser
```

### 6. 개발 서버 실행

```bash
python manage.py runserver
```

관리자 페이지: http://localhost:8000/admin/

## 앱 상세 설명

### Core (핵심)

- **User**: 역할 기반 사용자 (ADMIN, HR_MANAGER, TEAM_MANAGER, EMPLOYEE)
- **AuditedModel**: created_at, modified_at 자동 추적 기본 모델

### Organization (조직 구조)

- **Company**: 회사 정보
- **Department**: 계층적 부서 구조 (부모-자식 관계)
- **JobGrade**: 직급 (사원, 대리, 과장, 차장, 부장 등)
- **JobPosition**: 직책 (팀장, 파트장 등) - 수당 지급

### Employees (직원 관리)

- **Employee**: 직원 기본 정보, HR 정보, 계약 정보, 연봉 정보
- **EmployeeDocument**: 직원 증명서 (계약서, 이력서, 졸업장 등)
- **EmployeeHistory**: 인사 이력 (채용, 승진, 전배, 급여변경, 퇴직)

### Attendance (근태 관리)

- **WorkSchedule**: 근무 일정 템플릿
- **AttendanceRecord**: 일일 출석 기록 (체크인/아웃, 근무시간, 초과근무)
- **OvertimeRequest**: 초과근무 신청 (FSM: PENDING → APPROVED → COMPLETED)
- **Holiday**: 휴일 관리

### Leave (휴가 관리)

- **LeaveType**: 휴가 유형 (연차, 병가, 특별휴가 등)
- **LeaveBalance**: 연도별 휴가 잔여일수
- **LeaveRequest**: 휴가 신청 (FSM: DRAFT → PENDING → TEAM_APPROVED → APPROVED)
- **LeaveApproval**: 휴가 승인 이력

### Payroll (급여 관리) ⭐ 신규 구현

#### 모델

- **PayrollPeriod**: 급여 지급 주기 (FSM: DRAFT → CALCULATING → PENDING_APPROVAL → APPROVED → PAID → CLOSED)
- **Payslip**: 개인별 급여명세서 (base_salary, allowances, deductions, net_salary)
- **AllowanceType**: 수당 유형 마스터 데이터 (식대, 교통비, 직책수당, 초과근무수당 등)
- **DeductionType**: 공제 유형 마스터 데이터 (국민연금, 건강보험, 고용보험, 소득세 등)
- **SalaryContract**: 연봉 계약 (이력 추적)
- **PayslipAllowance**: 급여명세서 수당 상세
- **PayslipDeduction**: 급여명세서 공제 상세
- **PayrollAdjustment**: 급여 조정 (보너스, 차감 등)

#### 급여 계산 엔진 (`payroll/services/payroll_calculator.py`)

```python
calculator = PayrollCalculator(payroll_period)
payslips = calculator.calculate_all_employees()
```

**계산 로직:**
1. 근무 데이터 수집 (Attendance, Leave)
2. 기본급 계산 (무급휴가 차감)
3. 수당 계산 (직책수당, 초과근무수당, 고정수당)
4. 4대보험 계산 (국민연금 4.5%, 건강보험 3.545%, 장기요양, 고용보험 0.9%)
5. 소득세 및 주민세 계산 (간이세액표)
6. 실수령액 계산 (총지급액 - 공제액)

#### Admin 커스텀 액션

- **급여 계산**: PayrollPeriod에서 전체 직원 급여 자동 계산
- **승인**: HR 매니저가 급여 승인
- **지급 완료**: 급여 지급 처리

### Evaluation (인사평가) ⭐ 신규 구현

#### 평가 템플릿

- **EvaluationTemplate**: 평가 템플릿 (직급/부서별 적용)
- **EvaluationCategory**: 평가 카테고리 (역량, 업무성과, 태도)
- **EvaluationCriteria**: 평가 세부 항목 (5점/10점/100점 척도)

#### 평가 실행

- **EvaluationPeriod**: 평가 기간 (FSM: DRAFT → OPEN → UNDER_REVIEW → COMPLETED → CLOSED)
- **EmployeeEvaluation**: 직원별 평가 인스턴스 (자기/동료/상사 평가)
- **EvaluationScore**: 평가 항목별 점수
- **EvaluationSummary**: 평가 결과 종합 (등급 S/A/B/C/D, 부서/전사 순위)

#### 평가 가중치

- 자기평가: 20%
- 동료평가: 30%
- 상사평가: 50%

## 주요 기능

### 1. 급여 관리

```bash
# 관리자 페이지에서:
1. Payroll > Payroll Periods > 새 기간 생성
2. "급여 계산" 액션 클릭
3. 자동으로 전체 직원 급여 계산
4. 개별 Payslip 확인 및 수정
5. "승인" 액션으로 승인
6. "지급 완료" 액션으로 지급 처리
```

### 2. 인사평가

```bash
# 관리자 페이지에서:
1. Evaluation > Evaluation Periods > 새 평가 기간 생성
2. Evaluation Templates 설정 (카테고리, 평가 항목)
3. "평가 시작" 액션으로 평가 오픈
4. Employee Evaluations에서 평가 입력
5. "결과 계산" 액션으로 최종 점수 및 등급 산출
6. Evaluation Summaries에서 종합 결과 확인
```

### 3. 휴가 관리

```bash
# 직원:
1. Leave > Leave Requests > 휴가 신청
2. 제출 (DRAFT → PENDING)

# 팀장:
3. 승인 (PENDING → TEAM_APPROVED)

# HR:
4. 최종 승인 (TEAM_APPROVED → APPROVED, 휴가 잔여일수 자동 차감)
```

### 4. 근태 관리

```bash
# 관리자:
1. Attendance > Attendance Records > 일일 출석 기록
2. 체크인/체크아웃 시간 입력
3. 자동으로 근무시간, 초과근무, 지각 계산

# 직원:
4. Overtime Requests > 초과근무 신청
```

## 데이터 모델 주요 관계

```
Company
  ├─ Departments (계층)
  │   ├─ Employees
  │   └─ JobGrades
  └─ JobPositions

Employee
  ├─ SalaryContracts (연봉 이력)
  ├─ AttendanceRecords (근태)
  ├─ LeaveRequests (휴가)
  ├─ Payslips (급여명세서)
  └─ EmployeeEvaluations (평가)

PayrollPeriod
  └─ Payslips
      ├─ PayslipAllowances (수당 상세)
      ├─ PayslipDeductions (공제 상세)
      └─ PayrollAdjustments (조정)

EvaluationPeriod
  └─ EmployeeEvaluations
      └─ EvaluationScores (항목별 점수)
```

## 권한 관리

### 역할 (User.role)

- **ADMIN**: 전체 접근
- **HR_MANAGER**: HR 관련 전체 접근
- **TEAM_MANAGER**: 팀 내 직원 정보 조회, 휴가/초과근무 승인
- **EMPLOYEE**: 본인 정보만 조회

### 객체 레벨 권한 (Guardian)

- 직원은 본인 급여명세서만 조회
- 평가자는 자신이 작성하는 평가만 수정

## 개발 가이드

### 새 앱 추가 시 패턴

1. **모델 작성** (`models.py`)
   - `AuditedModel` 상속
   - FSM 필요 시 `FSMField` 및 `@transition` 사용
   - 변경 이력 필요 시 `HistoricalRecords()` 추가
   - 금액 필드는 `MoneyField` 사용

2. **Admin 작성** (`admin.py`)
   - `ModelAdmin` 상속 (Unfold)
   - 권한 필요 시 `GuardedModelAdmin` 추가
   - 이력 필요 시 `SimpleHistoryAdmin` 추가
   - `@display` 데코레이터로 커스텀 표시
   - `@action` 데코레이터로 커스텀 액션
   - Inline 활용

3. **비즈니스 로직** (`services/`)
   - 복잡한 계산 로직은 별도 서비스 클래스로 분리
   - 예: `PayrollCalculator`, `EvaluationCalculator`

4. **초기 데이터** (`fixtures/`)
   - 마스터 데이터는 JSON fixtures로 관리

### 코드 스타일

- 모든 문자열은 `gettext_lazy(_())` 사용 (다국어 지원)
- verbose_name, help_text 명시
- `__str__` 메서드 구현
- Meta 클래스에 ordering 지정

## 배포

### 환경 변수 설정

```bash
# .env 파일 생성
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### 프로덕션 설정

```bash
# Static 파일 수집
python manage.py collectstatic --noinput

# Gunicorn 실행
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## 라이선스

MIT License

## 기여

PR은 언제나 환영합니다!

## 참고

- [Django Unfold Documentation](https://unfoldadmin.com/)
- [django-fsm Documentation](https://github.com/viewflow/django-fsm)
- [django-money Documentation](https://github.com/django-money/django-money)

---

**개발**: Django 5.2 + Unfold Admin
**버전**: 1.0.0
**최종 업데이트**: 2024-01-15
