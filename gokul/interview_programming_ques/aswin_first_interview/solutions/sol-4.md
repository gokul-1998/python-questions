## Write SQL query to create and update a table

```sql
CREATE TABLE employee (
    emp_id INT PRIMARY KEY,
    emp_name VARCHAR(50),
    emp_salary INT
);

INSERT INTO employee (emp_id, emp_name, emp_salary) VALUES (1, 'John', 1000);
INSERT INTO employee (emp_id, emp_name, emp_salary) VALUES (2, 'Doe', 2000);
INSERT INTO employee (emp_id, emp_name, emp_salary) VALUES (3, 'Jane', 3000);

UPDATE employee
SET emp_name = 'John Doe'
WHERE emp_id = 2;
```

