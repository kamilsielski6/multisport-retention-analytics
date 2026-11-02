CREATE TABLE customers (
    customer_id VARCHAR(20) NOT NULL,
    signup_date DATE NOT NULL,
    city VARCHAR(50) NOT NULL,
    plan_type VARCHAR(20) NOT NULL,
    age_band VARCHAR(10) NOT NULL,
    acquisition_channel VARCHAR(30) NOT NULL
);

CREATE TABLE memberships (
    membership_id VARCHAR(20) NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) NOT NULL,
    monthly_fee DECIMAL(10, 2) NOT NULL
);

CREATE TABLE visits (
    visit_id VARCHAR(20) NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    visit_date DATE NOT NULL,
    activity_type VARCHAR(30) NOT NULL,
    duration_minutes INTEGER NOT NULL
);

CREATE TABLE payments (
    payment_id VARCHAR(20) NOT NULL,
    membership_id VARCHAR(20) NOT NULL,
    payment_date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL
);

CREATE TABLE churn_labels (
    customer_id VARCHAR(20) NOT NULL,
    snapshot_date DATE NOT NULL,
    last_visit_date DATE,
    inactivity_days INTEGER,
    churned INTEGER NOT NULL,
    churn_reason VARCHAR(30) NOT NULL
);
