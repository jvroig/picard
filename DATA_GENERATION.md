# PICARD Data Generation Reference

This document provides a comprehensive reference for all data types that can be generated in PICARD's sandbox environment. Use this guide to create realistic test data for CSV files and SQLite databases.

## Table of Contents

- [Overview](#overview)
- [People & Identity](#people--identity)
  - [`person_name`](#person_name) - Full names with first and last
  - [`first_name`](#first_name) - First names only
  - [`last_name`](#last_name) - Last names/surnames only
- [Business & Finance](#business--finance)
  - [`company`](#company) - Company names
  - [`department`](#department) - Business departments
  - [`salary`](#salary) - Annual salary amounts
  - [`currency`](#currency) - General monetary amounts
  - [`price`](#price) - Product/service prices with decimals
  - [`product`](#product) - Product names
- [Location & Geography](#location--geography)
  - [`city`](#city) - US city names
  - [`region`](#region) - Geographic regions
  - [`phone`](#phone) - US phone numbers
- [Time & Dates](#time--dates)
  - [`date`](#date) - Dates in ISO format
  - [`age`](#age) - Person ages
  - [`experience`](#experience) - Years of experience
- [Status & Categories](#status--categories)
  - [`status`](#status) - General status values
  - [`boolean`](#boolean) - True/false values
  - [`category`](#category) - Product/content categories
- [Identifiers & Numbers](#identifiers--numbers)
  - [`id`](#id) - Random ID numbers
  - [`auto_id`](#auto_id) - Auto-incrementing primary key (SQLite only)
  - [`score`](#score) - Scores, grades, or ratings
- [Communication](#communication)
  - [`email`](#email) - Email addresses
- [Education & Skills](#education--skills)
  - [`course`](#course) - Academic course names
  - [`semester`](#semester) - Academic terms
- [Content & Text](#content--text)
  - [`entity_pool`](#entity_pool) - Random words from PICARD's entity pool
  - [`lorem_word`](#lorem_word) - Single lorem ipsum word
  - [`lorem_words`](#lorem_words) - Multiple lorem ipsum words
- [Auto-Detection Rules](#auto-detection-rules)
- [Usage Examples](#usage-examples)

---

## Overview

PICARD can generate realistic data for CSV files and SQLite databases using either:
- **Automatic detection**: Based on header/column names
- **Explicit specification**: Using `header_types` (CSV) or `data_type` (SQLite)

```yaml
# Automatic detection
headers: ["customer_name", "email", "salary", "department"]

# Explicit specification  
headers: ["CUST_NM", "EMAIL_ADDR", "SAL_AMT", "DEPT_CD"]
header_types: ["person_name", "email", "salary", "department"]
```

---

## People & Identity

### `person_name`
**Description**: Full names with first and last names  
**Format**: "FirstName LastName"  
**Examples**: "John Smith", "Sarah Johnson", "Michael Brown"

**Auto-detected from**: `name`, `full_name`, `fullname`, `customer_name`, `client_name`, `*name*`

### `first_name`
**Description**: First names only  
**Examples**: "John", "Sarah", "Michael", "Emily"

**Auto-detected from**: `first_name`, `firstname`, `first`

### `last_name`
**Description**: Last names/surnames only  
**Examples**: "Smith", "Johnson", "Brown", "Wilson"

**Auto-detected from**: `last_name`, `lastname`, `last`, `surname`

---

## Business & Finance

### `company`
**Description**: Company names  
**Examples**: "Acme Corp", "Global Industries", "Tech Solutions", "Dynamic Systems"

**Auto-detected from**: `company`, `employer`, `company_name`, `*company*`

### `department`
**Description**: Business departments  
**Examples**: "Engineering", "Sales", "Marketing", "Finance", "HR", "Operations"

**Auto-detected from**: `department`, `dept`, `*department*`, `*dept*`

### `salary`
**Description**: Annual salary amounts  
**Range**: 30,000 to 150,000  
**Examples**: "65000", "42000", "125000"

**Auto-detected from**: `salary`, `income`, `*salary*`

### `currency`
**Description**: General monetary amounts  
**Range**: 1,000 to 100,000  
**Examples**: "25000", "75000", "50000"

**Auto-detected from**: `total`, `sum`, `revenue`, `amount`, `*amount*`

### `price`
**Description**: Product/service prices with decimals  
**Format**: "XXX.XX"  
**Examples**: "123.45", "89.99", "456.78"

**Auto-detected from**: `price`, `cost`, `amount`, `*price*`, `*cost*`

### `product`
**Description**: Product names  
**Examples**: "Widget Pro", "Super Gadget", "Ultra Tool", "Smart Sensor"

**Auto-detected from**: `product`, `item`, `product_name`, `*product*`

---

## Location & Geography

### `city`
**Description**: US city names  
**Examples**: "New York", "Los Angeles", "Chicago", "Houston", "Phoenix"

**Auto-detected from**: `city`, `location`, `city_name`, `*city*`

### `region`
**Description**: Geographic regions  
**Examples**: "North", "South", "East", "West", "Central", "Northeast", "Midwest"

**Auto-detected from**: `region`, `area`, `zone`, `*region*`

### `phone`
**Description**: US phone numbers  
**Format**: "(XXX) XXX-XXXX"  
**Examples**: "(555) 123-4567", "(212) 987-6543"

**Auto-detected from**: `phone`, `telephone`, `phone_number`, `*phone*`

---

## Time & Dates

### `date`
**Description**: Dates in ISO format  
**Format**: "YYYY-MM-DD"  
**Range**: 2020 to 2025  
**Examples**: "2024-03-15", "2023-11-22", "2025-01-08"

**Auto-detected from**: `date`, `created_date`, `updated_date`, `reg_dt`, `*date*`

### `age`
**Description**: Person ages  
**Range**: 18 to 70  
**Examples**: "25", "34", "56", "42"

**Auto-detected from**: `age`, `age_yrs`

### `experience`
**Description**: Years of experience  
**Range**: 0 to 40  
**Examples**: "5", "12", "0", "25"

**Auto-detected from**: `experience`, `years_experience`, `years`, `exp`, `*experience*`, `*exp*`

---

## Status & Categories

### `status`
**Description**: General status values  
**Examples**: "active", "inactive", "completed", "pending", "cancelled", "approved", "rejected", "processing"

**Auto-detected from**: `status`, `state`, `*status*`

### `boolean`
**Description**: True/false values in various formats  
**Examples**: "true", "false", "yes", "no", "1", "0"

**Auto-detected from**: `in_stock`, `available`, `active`, `*active*`

### `category`
**Description**: Product/content categories  
**Examples**: "Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Automotive"

**Auto-detected from**: `category`, `type`, `kind`, `*category*`, `*type*`

---

## Identifiers & Numbers

### `id`
**Description**: Random ID numbers  
**Range**: 1 to 9999  
**Examples**: "1247", "5683", "892", "3456"

**Auto-detected from**: `*_id`, `id`, `*id*`

### `auto_id` (SQLite only)
**Description**: Auto-incrementing primary key  
**Examples**: 1, 2, 3, 4, 5...

**Usage**: `{name: "EMP_ID", type: "auto_id"}`

### `score`
**Description**: Scores, grades, or ratings  
**Range**: 60 to 100  
**Examples**: "85", "92", "78", "96"

**Auto-detected from**: `score`, `grade`, `rating`, `points`, `*score*`, `*grade*`

---

## Communication

### `email`
**Description**: Email addresses  
**Format**: "firstname.lastname@domain.com"  
**Domains**: gmail.com, yahoo.com, hotmail.com, company.com, email.com  
**Examples**: "john.smith@gmail.com", "sarah.jones@company.com"

**Auto-detected from**: `email`, `email_address`, `*email*`

---

## Education & Skills

### `course`
**Description**: Academic course names  
**Examples**: "Math 101", "Physics 201", "Computer Science 202", "Data Science 501"

**Auto-detected from**: `course`, `subject`, `class`, `*course*`, `*subject*`

### `semester`
**Description**: Academic terms  
**Format**: "Season YYYY"  
**Examples**: "Spring 2024", "Fall 2023", "Summer 2025"

**Auto-detected from**: `semester`, `term`, `quarter`

---

## Content & Text

### `entity_pool`
**Description**: Random words from PICARD's entity pool  
**Examples**: "crimson", "harbor", "whisper", "ancient", "mountain", "legend"

**Usage**: Draws from the same 154-word entity pool used for `{{entity1}}` placeholders

### `lorem_word`
**Description**: Single lorem ipsum word  
**Examples**: "lorem", "ipsum", "dolor", "consectetur"

### `lorem_words`
**Description**: Multiple lorem ipsum words  
**Count**: 2 to 5 words randomly  
**Examples**: "lorem ipsum dolor", "consectetur adipiscing", "tempor incididunt"

**Default fallback**: Used when no specific type is detected

---

## Auto-Detection Rules

PICARD uses intelligent pattern matching to detect data types:

### 1. Direct Matches
Exact header name matches (case-insensitive):
- `name` → `person_name`
- `email` → `email`
- `age` → `age`
- `status` → `status`

### 2. Suffix Patterns
Headers ending with specific patterns:
- `*_id` → `id`
- `*_name` → `person_name`
- `*_date` → `date`

### 3. Substring Matches
Headers containing specific words:
- `*email*` → `email`
- `*price*` → `price`
- `*company*` → `company`
- `*department*` → `department`

### 4. Fallback
If no pattern matches: `lorem_words`

---

## Usage Examples

### CSV with Automatic Detection

```yaml
content:
  headers: ["customer_name", "email", "age", "city", "salary", "status"]
  rows: 100
# Generates: person_name, email, age, city, salary, status
```

### CSV with Explicit Types

```yaml
content:
  headers: ["CUST_NM", "CONTACT", "YRS", "LOC", "PAY", "STAT"]
  header_types: ["person_name", "email", "age", "city", "salary", "status"]
  rows: 100
```

### SQLite Single Table

```yaml
content:
  table_name: "employees"
  columns:
    - {name: "emp_id", type: "auto_id"}
    - {name: "name", type: "TEXT", data_type: "person_name"}
    - {name: "dept", type: "TEXT", data_type: "department"}
    - {name: "salary", type: "INTEGER", data_type: "salary"}
    - {name: "hire_date", type: "TEXT", data_type: "date"}
    - {name: "active", type: "TEXT", data_type: "boolean"}
  rows: 150
```

### Enterprise Business Scenario

```yaml
content:
  headers: ["EMP_ID", "EMPLOYEE_NAME", "DEPT_CODE", "SALARY_AMT", "YEARS_EXP", "EMAIL_ADDR", "PHONE_NUM", "HIRE_DT", "STATUS_FLG"]
  header_types: ["id", "person_name", "department", "salary", "experience", "email", "phone", "date", "status"]
  rows: 200
```

### E-commerce Product Catalog

```yaml
content:
  headers: ["PROD_ID", "PRODUCT_NAME", "CATEGORY", "PRICE", "COMPANY", "IN_STOCK"]
  header_types: ["id", "product", "category", "price", "company", "boolean"]
  rows: 500
```

### Academic Records

```yaml
content:
  headers: ["STUDENT_ID", "STUDENT_NAME", "COURSE", "SEMESTER", "SCORE", "EMAIL"]
  header_types: ["id", "person_name", "course", "semester", "score", "email"]
  rows: 300
```

---

## Best Practices

### For CSV Files
- Mix data types to create realistic business scenarios
- Include 50-200 rows for meaningful aggregation testing
- Use explicit data types to control exact data generation routine

### For SQLite Databases
- Use `auto_id` for primary keys
- Create foreign key relationships between tables
- Use appropriate SQLite types (`INTEGER`, `TEXT`, `REAL`)
- Use explicit data types to control exact data generation routine


### For Business Realism
- Combine related data types (person_name + email + phone)
- Use enterprise naming conventions (EMP_ID, CUST_NM, DEPT_CD)
- Include status and category fields for filtering tests